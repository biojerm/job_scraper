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
						 ('12,0000 per month', True),
						 ('99.93 per month', False),
						 ('$57.70 per hour', True),
						 ('38 per hour', False),
						 ('75 per hour', True),
						 ('9.93 per hour', False),
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
def test_parse_posting(job_listing):
	assert job_listing == True
# indeed_search

# things to test:
# 1. correct requests URL
# 2. connection timeout
# 3. page returned from requests
# 4. dataframe must be returned 
# 5. parse job posting
