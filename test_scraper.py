from datetime import datetime
import scraper
import pytest




# ### salary_sufficient
@pytest.mark.parametrize('salary, sufficient_status',[
						 ('nothing found', True),
						 ('Nothing_found', True),
						 ('Anything else', False)
])
def test_salary_sufficient_when_nothing_found(salary,sufficient_status):
	assert scraper.salary_sufficient(salary) == sufficient_status

@pytest.mark.parametrize('salary, sufficient_status',[
						 ('$120,001 per year', True),
						 ('$99,999 per year', False),
						 ('120001.01 per year', True),
						 ('99999.93 per year', False),
						 ('$10,001 per month', True),
						 ('$9,999 per month', False),
						 ('12,000 per month', True),
						 ('99.93 per month', False),
						 ('$57.70 per hour', True),
						 ('38 per hour', False),
						 ('75 per hour', True),
						 ('9.93 per hour', False),
						 ('$25 - $40 an hour', False)
])
def test_annual_salary_greater_120000(salary, sufficient_status):
	assert scraper.salary_sufficient(salary) == sufficient_status

@pytest.mark.parametrize('salary',[
						 ('$one billion per year'),
						 ('not real numbers per year')
])
def test_if_annual_salary_cannot_be_parsed(salary, capsys):
	scraper.salary_sufficient(salary)
	captured = capsys.readouterr()
	assert captured.out == 'could not parse salary value was: {0}\n'.format(salary)


# ### summary_score
def test_summary_scoring():
	assert scraper.summary_score('Corporate tax company looking for attorney.  Will calculate gift tax') == 3


# Title_score
@pytest.mark.parametrize('title, score', [
						('Sr Tax manager', 2),
						('tax planner', 2),
						('Real Estate Planner', -2),
						('random position tax', 2)
])
def test_job_title_scoring(title,score):
	assert scraper.title_score(title) == score


def test_indeed_url():
	job = 'Mechanic'
	location = 'California'
	posting_offset = 0
	test_url = scraper.indeed_url(job, location, posting_offset)
	assert test_url == 'https://www.indeed.com/jobs?q=Mechanic&l=California&start=0&fromage=1'


@pytest.fixture(scope='module')
def job_listings():
	with open(r"helpers/page.html","r") as page:
		return page.read()

@pytest.mark.current
def test_parse_posting(job_listings):
	job_details = scraper.parse_posting(job_listings)
	assert len(job_details) == 15, 'Should have 15 job postings'
	assert job_details[-1][0] == 	str(datetime.now().date()), 'First element is the date'
	assert job_details[-1][1] == 'Tax accounting assistant/Bookkeeper', 'Second element is the job title'
	assert job_details[-1][2] == 'Bennet Shay CPAs', 'Third element is the company name'
	assert job_details[-1][3] == 'Santa Clara', 'Fourth element is the city'
	assert job_details[-1][4] == 'CA', 'Fifth element is the State' # or love ;)
	assert job_details[-1][5] == 'Create estimate tax envelopes and tax filings. Tax Assistant â€“ 45%. File annual property tax reports. Data entry of client tax documents....', 'Sixth element is a summary of the job'
	assert job_details[-1][6] == 'www.indeed.com/pagead/clk?mo=r&ad=-6NYlbfkN0AnFnp7dmWfQ3fR6EGyjMo1ArRAXIGEJnVLL94bXtaM9tTCmkH5jcm3mrgBiBE8efeWahpkqcYEIe86fy_D_iOyBR30XTByePKyter7098zmkga8PZHFT0AD45QdCPD_HyAFO3Wbaq-HFHacunYXRmbMgxYdCa1-LpWN1x8USld0eHT6LfEsuP6frsqEEDbY6qDtrc4ahyR0NSuSRRQLjcaS-h5soioNE0wNw4Ids0BhZwKw_5BFvuVopGSrf7n3gF1dw5065UHTbTgIN7MHaPbsYs6tIz93RiT-RpaNDdIgU8NGMrdKSrPAvT7L7PuDUxKxHgFZ9OrY2cDDEDfMP66_xIsoSt3176Zt3hQiKb7j5hHZ4Kn8CtKwEWJEFN5pIuCSGiGzfnV8xFZR7wHhxnUJ00WtodjaD10q5CmIz56vaz34fX2j7ksodNW4bNGx2k=&vjs=3&p=5&sk=&fvj=1', 'Seventh element is the URL of the job'
	assert job_details[-1][7] == '$17 - $20 an hour'
 


# indeed_search

# things to test:
# 1. correct requests URL
# 2. connection timeout
# 3. page returned from requests
# 4. dataframe must be returned 
# 5. parse job posting
