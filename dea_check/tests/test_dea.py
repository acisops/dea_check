from ..dea_check import VALIDATION_LIMITS, \
    HIST_LIMIT, model_path
from acis_thermal_check.regression_testing import \
    RegressionTester

dea_rt = RegressionTester("1deamzt", "dea", model_path, VALIDATION_LIMITS,
                          HIST_LIMIT)

def test_dea_loads(answer_store):
    dea_rt.run_test_arrays(answer_store)
