import pytest

def pytest_addoption(parser):
    parser.addoption("--answer_store", 
        help="Generate new answers, but don't test. Argument is the directory to store the answers to.")

@pytest.fixture()
def generate_answers(request):
    return request.config.getoption('--answer_store')
