from ..dea_check import VALIDATION_LIMITS, \
    HIST_LIMIT, calc_model, model_path
from acis_thermal_check.regression_testing import \
    run_test_arrays

def test_dea_loads(answer_store):
    run_test_arrays("1deamzt", "dea", model_path,
                    [VALIDATION_LIMITS, HIST_LIMIT, calc_model],
                    answer_store, 
                    exclude_images=["1deamzt_valid.png","1deamzt.png","pow_sim.png"])
