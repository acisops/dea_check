from ..dea_check import VALIDATION_LIMITS, \
    HIST_LIMIT, model_path
from acis_thermal_check.regression_testing import \
    RegressionTester, all_loads
import pytest

dea_rt = RegressionTester("1deamzt", "dea", model_path, VALIDATION_LIMITS,
                          HIST_LIMIT)

# Prediction tests


@pytest.mark.parametrize('load', all_loads)
def test_prediction(answer_store, load):
    dea_rt.run_test("prediction", answer_store, load)

# Validation tests


@pytest.mark.parametrize('load', all_loads)
def test_validation(answer_store, load):
    dea_rt.run_test("validation", answer_store, load)
