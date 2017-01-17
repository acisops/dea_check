import pytest

def pytest_addoption(parser):
    parser.addoption("--generate_answers", 
        help="Generate new answers, but don't test. Argument is the directory to store the answers to.")

@pytest.fixture()
def generate_answers(request):
    return request.config.getoption('--generate_answers')
