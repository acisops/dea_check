from ..dea_check import dea_check, model_path
from acis_thermal_check.regression_testing import \
    load_test_template, test_loads
import os

default_model_spec = os.path.join(model_path, "dea_model_spec.json")

def test_dea_loads(answer_store):
    for load_week in test_loads:
        load_test_template("dea", dea_check, default_model_spec,
                           load_week, answer_store)
