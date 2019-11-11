from datetime import datetime
import scraper
import pytest



class TestPayInterval:

    @pytest.mark.parametrize(
            'phrase, result',[
                ('You are payed $20 per hour','hour'),
                ('$4,000 weekly', 'week'),
                ('1000 per Month', 'month'),
                ('75,000 per YEAR', 'year')
                ]
            )
    def test_parse_pay_interval(self, phrase, result):
        interval = scraper.pay_interval(phrase)
        assert interval == result

    def test_no_match(self):
        with pytest.raises(ValueError):
            phrase = 'foo'
            scraper.pay_interval(phrase)

class TestAnnualSalary:

    @pytest.mark.parametrize(
        'rate, interval, expected', [
            ('20', 'hour', 41600),
            ('200', 'week', 10400),
            ('800', 'biweek', 20800),
            ('3000', 'month', 36000),
            ('75000', 'year', 75000),
            ]
        )
    def test_convery_anual_salary(self, rate, interval, expected):
       salary = scraper.calculate_salary(rate, interval)
       assert salary == expected


    def test_rate_not_intger(self):
        with pytest.raises(ValueError):
            scraper.calculate_salary('foo', 'year')

    def test_no_salary_matches(self):
        with pytest.raises(ValueError):
            scraper.calculate_salary('foo', 'year')


class TestGetRate:

    @pytest.mark.parametrize('string, expected',[
        ('$120,001 per year', '120001'),
        ('$99,999 per year', '99999' ),
        ('120001.01 per year', '120001.01'),
        ('99999.93 per year', '99999.93'),
        ('$10,001 per month', '10001'),
        ('$9,999 per month', '9999'),
        ('12,000 per month', '12000'),
        ('99.93 per month', '99.93'),
        ('$57.70 per hour', '57.70'),
        ('38 per hour', '38'),
        ('75 per hour', '75'),
        ('9.93 per hour', '9.93'),
        ('$25 - $40 an hour', '25')
        ]
    )
    def test_parse_rate_string(self, string, expected):
        assert scraper.get_rate(string) == expected

    def test_no_rate_found(self):
        with pytest.raises(ValueError):
            scraper.get_rate('foo')

# ### salary_sufficient
@pytest.mark.parametrize(
    'salary, sufficient_status',[
     # ('nothing found', True),
     ('Nothing_found', True),
     ('Anything else', False)
     ]
)
def test_salary_sufficient_when_nothing_found(salary,sufficient_status):
    assert scraper.salary_sufficient(salary, 120000) == sufficient_status

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
    ('$25 - $40 an hour', False),
    ('$one billion per year', False),
    ('not real numbers per year', False)
    ])
def test_annual_salary_greater_120000(salary, sufficient_status):
    assert scraper.salary_sufficient(salary, 120000) == sufficient_status

# ### summary_score
def test_summary_scoring():
    summary = ("Corporate tax company looking for attorney."
               " Will calculate gift tax")
    assert scraper.summary_score(summary) == 3


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

def test_parse_posting(job_listings):
	job_details = scraper.parse_posting(job_listings)
	assert len(job_details) == 15, 'Should have 15 job postings'
	assert job_details[-1][0] == str(datetime.now().date()), 'First element is the date'
	assert job_details[-1][1] == 'Tax accounting assistant/Bookkeeper', 'Second element is the job title'
	assert job_details[-1][2] == 'Bennet Shay CPAs', 'Third element is the company name'
	assert job_details[-1][3] == 'Santa Clara', 'Fourth element is the city'
	assert job_details[-1][4] == 'CA', 'Fifth element is the State' # or love ;)
	assert job_details[-1][5] == 'Create estimate tax envelopes and tax filings. Tax Assistant – 45%. File annual property tax reports. Data entry of client tax documents....', 'Sixth element is a summary of the job'
	assert job_details[-1][6] == 'www.indeed.com/pagead/clk?mo=r&ad=-6NYlbfkN0AnFnp7dmWfQ3fR6EGyjMo1ArRAXIGEJnVLL94bXtaM9tTCmkH5jcm3mrgBiBE8efeWahpkqcYEIe86fy_D_iOyBR30XTByePKyter7098zmkga8PZHFT0AD45QdCPD_HyAFO3Wbaq-HFHacunYXRmbMgxYdCa1-LpWN1x8USld0eHT6LfEsuP6frsqEEDbY6qDtrc4ahyR0NSuSRRQLjcaS-h5soioNE0wNw4Ids0BhZwKw_5BFvuVopGSrf7n3gF1dw5065UHTbTgIN7MHaPbsYs6tIz93RiT-RpaNDdIgU8NGMrdKSrPAvT7L7PuDUxKxHgFZ9OrY2cDDEDfMP66_xIsoSt3176Zt3hQiKb7j5hHZ4Kn8CtKwEWJEFN5pIuCSGiGzfnV8xFZR7wHhxnUJ00WtodjaD10q5CmIz56vaz34fX2j7ksodNW4bNGx2k=&vjs=3&p=5&sk=&fvj=1', 'Seventh element is the URL of the job'
	assert job_details[-1][7] == '$17 - $20 an hour'



# indeed_search

# things to test:
# 1. correct requests URL
# 2. connection timeout
# 3. page returned from requests
# 4. dataframe must be returned 
# 5. parse job posting
