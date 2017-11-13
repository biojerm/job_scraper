#!/home/jeremy/miniconda3/envs/py3k/bin/python
from datetime import datetime
import os
import sys
import re
import requests
import time

from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import pandas as pd
import pygsheets


import gmail_sender as email
import private  # file with private information


def salary_sufficient(salary):

    """
    Salary can be found in a number of different formats (annual, hourly,
        monthly)
    """
    if salary == 'nothing found' or salary == 'Nothing_found':
        return(True)
    elif 'year' in salary:
        min_salary = re.search(r'^\$([0-9]+,[0-9]+)', salary).group(1).replace(',', '')
        return(int(min_salary) >= 120000)
    elif 'month' in salary:
        min_salary = re.search(r'^\$([0-9]+,[0-9]+)', salary).group(1).replace(',', '')
        return(int(min_salary)*12 >= 120000)
    elif 'hour' in salary:
        try:
            min_salary = re.search(r'^\$([0-9]+\.[0-9]+)', salary).group(1).replace('.', '')
        except:
            min_salary = re.search(r'^\$([0-9]+)', salary).group(1).replace('.', '')
        return((float(min_salary)*40*52) >= 120000)
    else:
        print('could not parse salary value was: {0}'.format(salary))
        return(False)

stop_words = set(stopwords.words('english'))


def summary_score(summary):
    """
    Assigns a score to the the summary add points to good_words and
    subtracting from bad_words.  A score is returned
    """
    score = 0
    tokenized_summary = word_tokenize(summary.lower())
    summary_no_stop = [token for token in tokenized_summary if token not in stop_words]

    # keep these all lowercase
    good_words = ['tax', 'international', 'corporate', 'law', 'attorney',
                  'LLM', 'planning']
    bad_words = ['preparation', 'gift tax', 'estates', 'cpa', 'controller']

    for word in summary_no_stop:
        if word in good_words:
            score += 1
        elif word in bad_words:
            score -= 1
    return(score)


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
    return(score)

rejected_request = 0  # used for error tracking
max_results_per_city = 20
query_set = [
    'California', 'Oregon', 'Washington', 'Nevada', 'Utah', 'Colorado',
    'Montana', 'Idaho', 'Wyoming', 'Nebraska', 'New+Mexico', 'Texas',
    'Missouri', 'Minnesota', 'Michigan', 'Wisconsin', 'Illinois', 'Ohio',
    'West+Virgina', 'North+Carolina', 'South+Carolina', 'Virgina', 'Maryland',
    'Pennsylvania', 'New+York', 'New+Jersey', 'Delaware', 'Massachusetts',
    'Vermont', 'New+Hampshire', 'Maine', 'Tennessee', 'Iowa'
             ]
job_titles = [
              'tax+attorney', 'international+tax+planning', 'tax+planning',
              'tax+associate'
             ]

columns = [
    'capture_date', 'job_title', 'company_name', 'city', 'state', 'summary',
    'link', 'salary'
          ]
job_listings = pd.DataFrame(columns=columns)

# Web scraping code:
start_time = datetime.now()
print('Started collecting jobs at {}'.format(datetime.now().strftime('%I:%M %p')))
for job in job_titles:
    print("Searching the locations for the positions with the title of: {}".format(job))
    for query in query_set:
        for start in range(0, max_results_per_city, 10):
            try:
                page = requests.get('https://www.indeed.com/jobs?q={0}&l={1}&start={2}&fromage=1'.format(job, str(query), str(start)))
            except requests.exceptions.ConnectionError:
                print('~~~~~connection refused sleeping for a bit longer~~~~~~~')
                time.sleep(15)
                rejected_request += 1
            time.sleep(3)  # ensuring at least 3 seconds between page requests
            soup = BeautifulSoup(page.text, 'lxml')
            for div in soup.find_all(name='div', attrs={'class': 'row'}):
                job_post = []
                job_post.append(str(datetime.now().date()))
                # grabbing job title
                for a in div.find_all(name='a', attrs={'data-tn-element': 'jobTitle'}):
                    job_post.append(a['title'])
                # grabbing company name
                company = div.find_all(name='span', attrs={'class': 'company'})
                if len(company) > 0:
                    for b in company:
                        job_post.append(b.text.strip())
                else:
                    sec_try = div.find_all(name='span', attrs={'class': 'result-link-source'})
                    for span in sec_try:
                        job_post.append(span.text)
                # grabbing city and state
                c = div.findAll('span', attrs={'class': 'location'})
                for span in c:
                    try:
                        job_post.append(re.search(r'(^[a-zA-Z]+(?:[\s-][a-zA-Z]+)*)(, )([A-Z]{2})', span.text).group(1))
                        job_post.append(re.search(r'(^[a-zA-Z]+(?:[\s-][a-zA-Z]+)*)(, )([A-Z]{2})', span.text).group(3))
                    except:
                        job_post.append('No information found')
                        job_post.append('No information found')
                # grabbing summary text
                d = div.findAll('span', attrs={'class': 'summary'})
                for span in d:
                    job_post.append(span.text.strip())
                # grabbing job URL
                for link_div in div.find_all(name='a', attrs={'data-tn-element': 'jobTitle'}):
                    job_post.append('www.indeed.com' + link_div['href'])
                # grabbing salary
                try:
                    job_post.append(div.find('nobr').text)
                except:
                    try:
                        div_two = div.find(name='div', attrs={'class': 'sjcl'})
                        div_three = div_two.find('div')
                        job_post.append(div_three.text.strip())
                    except:
                        job_post.append('Nothing_found')
                try:
                    job_posting = pd.DataFrame([job_post], columns=columns)
                    job_listings = job_listings.append(job_posting)
                    # print(job_post[1]) #print the titles of the jobs being found
                except (ValueError, AssertionError) as e:
                    print('An error occurred, it was: {}'.format(e))
                    print('https://www.indeed.com/jobs?q={0}&l={1}&start={2}&fromage=1'.format(job, str(query), str(start)))
                    # print(job_post)
                    pass

end_time = datetime.now()
print('Web scraping took {0}'.format(end_time - start_time))
print("requests were rejected {0} times".format(str(rejected_request)))
# load data from CVS file
# sample_df = pd.read_csv('filtered_jobs_5_18.csv', index_col=0)

# #### Filtering Data #######

# filtering out duplicate entries
remove_duplicates_df = job_listings.drop_duplicates(subset=['job_title', 'company_name', 'city', 'state', 'summary'], keep='first')
sample_df = remove_duplicates_df.drop_duplicates(subset='link', keep='first')
# The word 'tax' must be in the summary
tax_in_summary_index = ['tax' in row or 'Tax' in row for row in sample_df['summary']]
tax_in_summary = sample_df[tax_in_summary_index].copy()
# Check if salary is sufficient in posting
salary_index = [salary_sufficient(row) for row in tax_in_summary.salary]
salary_filtered = tax_in_summary[salary_index].copy()
# Filtering out jobs with bad titles
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
bad_title_index = []
for row in salary_filtered.job_title:
    comparison = []
    for title in bad_titles:
        comparison.append(title in row)
    bad_title_index.append(not any(comparison))
title_filtered = salary_filtered[bad_title_index].copy()

# filtering out bad companies
bad_companies = [
    'Block Advisors Tax and Business Services', 'The Vitamin Shoppe',
    'Staffing', 'H&R Block', 'FirstService Residential', 'Allied Universal',
    'CareOregon, Inc.', 'Catholic Charities', 'Golden Nugget',
    'Scott Credit Union', 'Royal American Management, Inc.', 'Block Advisors',
    'Mercer Transportation', 'Transportation Security Administration',
    'HR block'
    ]
bad_company_index = []
for row in title_filtered.company_name:
    comparison = []
    for company in bad_companies:
        comparison.append(company in row)
    bad_company_index.append(not any(comparison))
bad_companies_filtered = title_filtered[bad_company_index].copy()
# scoring summary based on relevance 
bad_companies_filtered.loc[:, 'score'] = bad_companies_filtered.summary.apply(summary_score).copy()
# scoring title based on relevance
bad_companies_filtered['score'] += bad_companies_filtered.job_title.apply(title_score)
filtered_jobs = bad_companies_filtered[bad_companies_filtered.score > 2].sort_values('score', ascending=False).copy()

# for testing !
# filtered_jobs.to_csv('filtered_jobs_test.csv')

print('Creating log, {} jobs found'.format(len(filtered_jobs)))

# ## Upload jobs to G-Sheets
job_listings = filtered_jobs.values.tolist()
print("{0} jobs found, starting upload to Google sheet.".format(len(job_listings)))

dir_path = os.path.dirname(os.path.abspath(__file__))
gc = pygsheets.authorize(service_file=os.path.join(dir_path, 'client_secret.json'))
# Open spreadsheet and then worksheet
sh = gc.open('Indeed Job Sheet')
wks = sh.worksheet_by_title('Job Posts')

try:
    if any(isinstance(i, list) for i in job_listings):
        wks.insert_rows(row=7, number=len(job_listings), values=job_listings)
    else:
        wks.insert_rows(row=7, values=job_listings)  # if only 1 job then only insert 1 row
except Exception as e:
    print('Insertion of data to google sheet failed.')
    print('Here is the error: {0}'.format(e))

# # Send summary email. Most code in gmail_sender.py
high_scoring_jobs = len(filtered_jobs[filtered_jobs.score > 6])
email_message = 'Hi Honey,<br /> The script was just run and {0} jobs were found. {1} jobs appear to have a pretty high relevance score'.format(len(filtered_jobs), high_scoring_jobs)
subject = 'Job postings on {0}'.format(datetime.now().strftime('%-m/%-d'))
email.create_and_send_message(private.email['J'], private.email['A'], subject, email_message)
