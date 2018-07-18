import scraper
import pytest



# #salary_sufficient
@pytest.mark.parametrize("salary, sufficient_status",[
						 ("nothing found", True),
						 ('Nothing_found', True),
						 ('Anything else', False)
])
def test_salary_sufficient_when_nothing_found(salary,sufficient_status):
	assert scraper.salary_sufficient(salary) == sufficient_status

@pytest.mark.parametrize("salary, sufficient_status",[
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

@pytest.mark.parametrize("salary",[
						 ('$one billion per year'),
						 ('not real numbers per year')
])
def test_if_annual_salary_cannot_be_parsed(salary, capsys):
	scraper.salary_sufficient(salary)
	captured = capsys.readouterr()
	assert captured.out == "could not parse salary value was: {0}\n".format(salary)

