import os
import shutil
import tempfile

from ..dea_check import dea_check, model_path
from acis_thermal_check.test_utils import run_answer_test, \
    run_image_test, run_model

def dea_test_template(generate_answers, run_start, load_week, 
                      cmd_states_db='sybase'):
    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)
    model_spec = os.path.join(model_path, "dea_model_spec.json")
    out_dir = run_model("dea", dea_check, model_spec, run_start, 
                        load_week, cmd_states_db)
    run_answer_test("dea", load_week, out_dir, generate_answers)
    run_image_test("1deamzt", "dea", load_week, out_dir, generate_answers)
    os.chdir(curdir)
    shutil.rmtree(tmpdir)

def test_dea_may3016(generate_answers):
    run_start = "2016:122:12:00:00.000"
    load_week = "MAY3016"
    dea_test_template(generate_answers, run_start, load_week)