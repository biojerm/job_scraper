#!/home/jeremy/miniconda3/envs/py3k/bin/pytho

from datetime import datetime
import os
import re
import time
import itertools
import argparse

import requests
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import pandas as pd
import pygsheets


# files with helper methods and private passwords/keys/emailaddresses
import gmail_sender as email
import private  # file with private information


# ### Helper Methods ###
def pay_interval(payment_phrase: str) -> str:
    """Find first match of pay interval key word

    payment_phrase: text containg pay interval information:

    raises: ValueError if cannot find a payment interval insde payment_phrase
    """
    interval_exp = '(?P<interval>hour|day|week|biweek|month|year|annual)'
    match = re.search(interval_exp, payment_phrase.lower())
    if match:
        interval = match.group('interval')
    else:
        print(f'Could not find payment interval in {payment_phrase}')
        raise ValueError

    return interval

def calculate_salary(rate: str, interval: str) -> int:
    """Converts pay rate to annual salary

    raises: ValueError if rate cannot be cast to float
            ValueError if no known interval value
    """
    ann_salary = None
    try:
        rate = float(rate)
    except:
        raise ValueError

    if interval == 'hour':
        ann_salary = rate * 8 * 5 * 52
    elif interval == 'week':
        ann_salary = rate * 52
    elif interval == 'biweek':
        ann_salary = rate * 26
    elif interval == 'month':
        ann_salary = rate * 12
    elif interval in {'year', 'annual'}:
        ann_salary = rate
    else:
        raise ValueError

    return ann_salary

def get_rate(string: str) -> str:
    """Parse sting for pay rate

    string: string representations of pay test_parse_rate_string

    raises: ValueError:If cannot find numeric pay rate
    """
    currency_regex = r'\d+(\.\d+)?'
    match = re.search(currency_regex, string.replace(',', ''))
    if not match:
        raise ValueError

    return match.group(0)

def salary_sufficient(comp_stmnt: str, suff_salary: int) -> bool:
    """Evaluates if annual salary is sufficient amount

    comp_stmnt: string with pay rate and interval
    sufficient_status: required salary for position
    """
    sufficient = False
    if comp_stmnt == 'Nothing_found':
        return True
    try:
        rate_str = get_rate(comp_stmnt)
        interval = pay_interval(comp_stmnt)
        if rate_str and interval:
            rate = calculate_salary(rate_str, interval)
            if rate >= suff_salary:
                sufficient = True
    except ValueError:
        print(f'Could not parse salary value was: {comp_stmnt}')
        sufficient = False

    return sufficient

def summary_score(summary):
    """
    Assigns a score to the the summary add points to good_words and
    subtracting from bad_words.  A score is returned
    """
    stop_words = set(stopwords.words('english'))
    score = 0
    tokenized_summary = word_tokenize(summary.lower())
    summary_no_stop = filter(lambda x: x not in stop_words, tokenized_summary)
    # keep these all lowercase
    good_words = {'tax', 'international', 'corporate', 'law', 'attorney',
                  'LLM', 'planning'}
    bad_words = {'preparation', 'gift', 'estates', 'cpa', 'controller'}
    for word in summary_no_stop:
        if word in good_words:
            score += 1
        elif word in bad_words:
            score -= 1
    return score


def title_score(title):
    """
     The word tax must be in the first, second, or last word of title.
     Second word allowed because sometimes there is a qualifier
     ex: 'Senior Tax Manager'
     Last word often tax like 'Senior Manager - tax'
    """
    score = 0
    token_title = word_tokenize(title.lower())
    if 'tax' in token_title[0:2] or 'tax' in token_title[-1]:
        score += 2
    else:
        score -= 2
    return score



def indeed_url(job, location, posting_offset):
    """Returns Indeed.com API url for job query

    Args:
        job (str): Title of job
        location (str): Location of job
        posting_offset (str): Index of first posting

    Return (str): Indeed url
    """
    url = (f"https://www.indeed.com/jobs"
           f"?q={job}&l={location}&start={str(posting_offset)}&fromage=1")
    return url


class JobPost:
    """JobPost parses a BeautifulSoup object from Indeed.com"""
    def __init__(self, html_soup):
        self.listing = html_soup
        self.current_date = str(datetime.now().date())


    def _job_title(self):
        """Parses job title from Indeed posting"""
        title_element = self.listing.find(
            name='a', attrs={'data-tn-element': 'jobTitle'})
        title = ''
        if title_element:
            title = title_element.text.strip()

        return title


    def _company_name(self):
        """Parse company name fom Indeed job posting"""
        company_element = self.listing.find(
            name='span', attrs={'class': 'company'})
        company = ''
        if company_element:
            company = company_element.text.strip()

        return company


    def _location(self):
        """Parse job location from Indeed job post"""

        location_element = self.listing.find('span',
                                             attrs={'class': 'location'})
        city = ''
        state = ''
        if location_element:
            location_re = re.compile(r"(^[a-zA-Z]+(?:[\s-][a-zA-Z]+)*)"
                                     "(, )([A-Z]{2})")
            match = location_re.search(location_element.text.strip())
            try:
                city = match.group(1)
                state = match.group(3)
            except AttributeError:
                city = "No information found"
                state = "No information found"

        return city, state


    def _summary_text(self):
        """Parse job summary from Indeed job post"""
        summary_element = self.listing.find('div', attrs={'class': 'summary'})
        summary = ''
        if summary_element:
            summary = summary_element.text.strip()

        return summary

    def _job_url(self):
        """Parse url of job post in Indeed job post"""
        url_element = self.listing.find(name='a',
                                        attrs={'data-tn-element': 'jobTitle'})
        url = f"www.indeed.com{url_element['href']}"
        return url

    def _salary(self):
        """Parse salary string from Indeed job post"""
        salary_element = self.listing.find(name='span',
                                           attrs={'class':'no-wrap'})
        salary = ''
        if salary_element:
            salary = salary_element.text.strip()
        else:
            salary = "Nothing_found"

        return salary


    def get_details(self):
        """Assembles the details of a job post

        Returns (lst): Job posting information"""
        date = self.current_date
        job_title = self._job_title()
        company_name = self._company_name()
        city, state = self._location()
        summary = self._summary_text()
        url = self._job_url()
        salary = self._salary()

        return [date, job_title, company_name, city,
                state, summary, url, salary]


def parse_posting(page_text):
    """Parse the job postings of each page from Indeed.com

    :param page_text: raw text form webpage

    Returns list of job postsings (list of lists)
    """
    job_listings = []
    soup = BeautifulSoup(page_text, 'lxml')
    for div in soup.find_all(name='div', attrs={'class': 'row'}):
        job_post = JobPost(div)
        job_listings.append(job_post.get_details())
    return job_listings

def indeed_search(locations, job_titles):
    """
    returns a dataframe with job postings from Indeed.com using API.
    Provide array of locations and job titles to search
    """
    max_results_per_city = 20
    columns = [
        'capture_date', 'job_title', 'company_name',
        'city', 'state', 'summary', 'link', 'salary'
    ]
    job_listings = []

    # Web scraping code:
    jobs_per_page = range(0, max_results_per_city, 10)
    query_keys = itertools.product(job_titles, locations, jobs_per_page)
    for key_tup in query_keys:
        (job, query, start) = key_tup
        try:
            page = requests.get(indeed_url(job, query, str(start)))
        except requests.exceptions.ConnectionError:
            print('~~~~~connection refused sleeping for a bit longer~~~~~~~')
            time.sleep(15)
        time.sleep(3)  # ensuring at least 3 seconds between page requests

        job_post = parse_posting(page.text)
        try:
            job_df = pd.DataFrame(job_post, columns=columns)
            job_listings.append(job_df)
        except (ValueError, AssertionError) as err:
            print(f'An error occurred, it was: {err}')
            print(f'https://www.indeed.com/jobs?q={job}&l={str(query)}'
                  '&start={str(start)}&fromage=1')
    listing_df = pd.concat(job_listings)
    return listing_df


def filter_found_jobs(job_results):
    """
    Takes queried job results dataframe from Indeed job search and
    filters out the results to a more manageable size
    """
    # Selection of companies and job titles that are not relevant
    bad_titles = [
        'paralegal', 'Paralegal', 'secretary', 'Secretary', 'clerk', 'Clerk',
        'closer', 'Closer', 'Engineer', 'engineer', 'service', 'Service', 'Care',
        'care', 'Administrator', 'administrator', 'accountant', 'Accountant',
        'customer', 'Customer', 'nurse', 'Nurse', 'Help', 'help', 'science',
        'Science', 'loan', 'Loan', 'energy', 'Energy', 'marketing', 'Marketing',
        'assistant', 'Assistant', 'CPA', 'Research', 'research', 'PARALEGAL',
        'Financial Advisor', 'HR', 'Licensing Specialist', 'Furnishings Officer',
        'Intern', 'Licensed Customs Broker', 'Real Estate', 'Neurology',
        'Physician', 'Lending', 'Financial Controller', 'Accounts Payable',
        'payroll', 'Payroll', 'Justice', 'sales', 'Sales', 'Finance Manager',
        'Retail', 'Bookkeeper', 'Banker', 'IT', 'RN', 'Buyer', 'Accounting',
        'Mortgage', 'Shared Living Provider', 'Night Auditor',
        'Relationship Associate', 'product specialist', 'Title Agent',
        'WM Investment', 'Receptionist', 'Sourcing', 'SOURCING', 'Clinic',
        'Property', 'Business Analyst', 'Developer', 'Administrative',
        'Collections', 'Preparer', 'Architect', 'Mobility', 'Wealth', 'WM',
        'Pricing', 'Estate', 'Information Technology', 'Financial Analyst',
        'Fixed Income', 'Valuation', 'Creative', 'Escrow', 'Benefits Attorney',
        'Cashier', 'Compliance Specialist', 'Front Desk Supervisor',
        'People & Culture Sr. Associate', 'Staffing Coordinator', 'Technician',
        'Part-time', 'Actuarial', 'RETAIL', 'HUD', 'LIHCT', 'Supply Chain',
        'Program Budget Lead', 'Auto Delivery Specialist', 'Relationship',
        'Coder', 'WEALTH', 'part time', 'Billing', 'Trust Officer', 'QA', 'CEO',
        'CFO', 'Scientist'
    ]
    bad_companies = [
        'Block Advisors Tax and Business Services', 'The Vitamin Shoppe',
        'Staffing', 'H&R Block', 'FirstService Residential', 'Allied Universal',
        'CareOregon, Inc.', 'Catholic Charities', 'Golden Nugget',
        'Scott Credit Union', 'Royal American Management, Inc.', 'Block Advisors',
        'Mercer Transportation', 'Transportation Security Administration',
        'HR block'
    ]
    # filtering out duplicate entries
    remove_duplicates_df = job_results.drop_duplicates(subset=['job_title', 'company_name', 'city', 'state', 'summary'], keep='first').copy()
    remove_duplicates_df.drop_duplicates(subset='link', keep='first', inplace=True)
    # The word 'tax' must be in the summary
    tax_in_summary_index = ['tax' in row or 'Tax' in row for row in remove_duplicates_df['summary']]
    # Check if salary is sufficient in posting
    salary_index = remove_duplicates_df.salary.apply(salary_sufficient,
            args=(120000,))
    # Removing specific companies and job titles
    bad_title_index = ~remove_duplicates_df.job_title.isin(bad_titles)
    bad_company_index = ~remove_duplicates_df.company_name.isin(bad_companies)
    # applying all filtration jobs dataframe
    unscored_jobs_df = remove_duplicates_df.loc[tax_in_summary_index & salary_index & bad_title_index & bad_company_index, :].copy()
    # scoring summary based on relevance
    unscored_jobs_df.loc[:, 'score'] = unscored_jobs_df.summary.apply(summary_score)
    # scoring title based on relevance
    unscored_jobs_df.loc[:, 'score'] += unscored_jobs_df.job_title.apply(title_score)
    filtered_jobs = unscored_jobs_df[unscored_jobs_df.score > 2].sort_values('score', ascending=False)

    return(filtered_jobs)


# ## Upload jobs to G-Sheets
def update_google_sheets(jobs, auth_token_path):
    """update_google_sheets

    :param jobs:
    :param auth_token_path:
    """
    job_listings = jobs.values.tolist()
    print(f"{len(job_listings)} jobs found, starting upload to Google sheet.")
    dir_path = os.path.dirname(os.path.abspath(__file__))
    gc = pygsheets.authorize(service_file=auth_token_path, no_cache=True)
    # Open spreadsheet and then worksheet
    sh = gc.open('Indeed Job Sheet')
    wks = sh.worksheet_by_title('Job Posts')
    try:
        if any(isinstance(i, list) for i in job_listings):
            wks.insert_rows(row=7, number=len(job_listings), values=job_listings)
        else:
            wks.insert_rows(row=7, values=job_listings)
    except Exception as e:
        print('Insertion of data to google sheet failed.')
        print(f'Here is the error: {e}')


def email_summary(jobs):
    """Sends an email summary of jobs found.  Would need to update private.py
    file and private.email['x'] below to work on other instument
    """
    filtered_jobs = jobs.copy()
    high_scoring_jobs = len(filtered_jobs[filtered_jobs.score > 6])
    email_message = ('Hi,<br /> The script was just run and '
                     f'{len(filtered_jobs)} jobs were found. '
                     f'{high_scoring_jobs} jobs appear to have a '
                     'pretty high relevance score')
    subject = f"Job postings on {datetime.now().strftime('%m/%d')}"
    email.create_and_send_message(private.email['J'], private.email['A'], subject, email_message)


def get_args():
    """Parse command line arguements"""
    parser = argparse.ArgumentParser()
    parser.add_argument('auth_token',
                        help="Path to google sheets authorization token")
    cli_args = parser.parse_args()
    return cli_args


if __name__ == '__main__':
    query_set = ['Washington',
    'California', 'Oregon', 'Washington', 'Nevada', 'Utah', 'Colorado',
    'Montana', 'Idaho', 'Wyoming', 'Nebraska', 'New+Mexico', 'Texas',
    'Missouri', 'Minnesota', 'Michigan', 'Wisconsin', 'Illinois', 'Ohio',
    'West+Virgina', 'North+Carolina', 'South+Carolina', 'Virgina', 'Maryland',
    'Pennsylvania', 'New+York', 'New+Jersey', 'Delaware', 'Massachusetts',
    'Vermont', 'New+Hampshire', 'Maine', 'Tennessee', 'Iowa'
    ]
    job_titles = ['tax+attorney',
    'tax+attorney', 'international+tax+planning', 'tax+planning',
    'tax+associate'
    ]
    args = get_args()
    jobs = filter_found_jobs(indeed_search(query_set, job_titles))
    update_google_sheets(jobs, args.auth_token)
    email_summary(jobs)

