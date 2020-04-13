from ..dea_check import DEACheck, model_path
from acis_thermal_check.regression_testing import \
    RegressionTester
import os

dea_rt = RegressionTester(DEACheck, model_path, "dea_test_spec.json")


def test_DEC0919A_viols(answer_store):
    answer_data = os.path.join(os.path.dirname(__file__), "answers",
                               "DEC0919A_viol.json")
    dea_rt.check_violation_reporting("DEC0919A", answer_data,
                                     answer_store=answer_store)