import os
import shutil
import tempfile

from ..dea_check import dea_check, model_path
from acis_thermal_check.test_utils import run_answer_test, \
    run_image_test, run_model

def test_dea(generate_answers, cmd_states_db):
    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)
    model_spec = os.path.join(model_path, "dea_model_spec.json")
    out_dir = run_model("dea", dea_check, model_spec, cmd_states_db)
    run_answer_test("dea", out_dir, generate_answers)
    run_image_test("1deamzt", "dea", out_dir, generate_answers)
    os.chdir(curdir)
    shutil.rmtree(tmpdir)

