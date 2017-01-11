import pytest

def pytest_addoption(parser):
    parser.addoption("--generate_answers", 
        help="Generate new answers, but don't test. Argument is the directory to store the answers to.")
    parser.addoption("--cmd-states-db",
        help="Commanded states database server (sybase|sqlite)", default="sybase")

@pytest.fixture()
def generate_answers(request):
    return request.config.getoption('--generate_answers')

@pytest.fixture()
def cmd_states_db(request):
    return request.config.getoption("--cmd-states-db")