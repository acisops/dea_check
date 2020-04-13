from ..dea_check import model_path, DEACheck
from acis_thermal_check.regression_testing import \
    RegressionTester, all_loads
import pytest

dea_rt = RegressionTester(DEACheck, model_path, "dea_test_spec.json")

# SQL state builder tests

dea_rt.run_models(state_builder='sql')

# Prediction tests


@pytest.mark.parametrize('load', all_loads)
def test_prediction(answer_store, load):
    if not answer_store:
        dea_rt.run_test("prediction", load)
    else:
        pass

# Validation tests


@pytest.mark.parametrize('load', all_loads)
def test_validation(answer_store, load):
    if not answer_store:
        dea_rt.run_test("validation", load)
    else:
        pass
