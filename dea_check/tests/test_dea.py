from ..dea_check import model_path, DEACheck
from acis_thermal_check.regression_testing import \
    RegressionTester, all_loads
import pytest

dea_rt = RegressionTester(DEACheck, model_path)

# Prediction tests


@pytest.mark.parametrize('load', all_loads)
def test_prediction(answer_store, load):
    dea_rt.run_test("prediction", answer_store, load)

# Validation tests


@pytest.mark.parametrize('load', all_loads)
def test_validation(answer_store, load):
    dea_rt.run_test("validation", answer_store, load)
