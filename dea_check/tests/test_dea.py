from ..dea_check import VALIDATION_LIMITS, \
    HIST_LIMIT, calc_model, model_path
from acis_thermal_check.regression_testing import \
    load_test_template, normal_loads, too_loads, \
    stop_loads
import os

default_model_spec = os.path.join(model_path, "dea_model_spec.json")

def test_dea_loads(answer_store):
    for load_week in normal_loads:
        load_test_template("1deamzt", "dea", default_model_spec, load_week,
                           [VALIDATION_LIMITS, HIST_LIMIT, calc_model],
                           answer_store, exclude_images=["1deamzt_valid.png","1deamzt.png","pow_sim.png"])
    for load_week in too_loads:
        load_test_template("1deamzt", "dea", default_model_spec, load_week,
                           [VALIDATION_LIMITS, HIST_LIMIT, calc_model],
                           answer_store, interrupt=True, exclude_images=["1deamzt_valid.png","1deamzt.png","pow_sim.png"])
    for load_week in stop_loads:
        load_test_template("1deamzt", "dea", default_model_spec, load_week,
                           [VALIDATION_LIMITS, HIST_LIMIT, calc_model],
                           answer_store, interrupt=True, exclude_images=["1deamzt_valid.png","1deamzt.png","pow_sim.png"])

