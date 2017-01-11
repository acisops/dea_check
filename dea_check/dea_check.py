#!/usr/bin/env python

"""
========================
dea_check
========================

This code generates backstop load review outputs for checking the ACIS
DEA temperature 1DEAMZT.  It also generates DEA model validation
plots comparing predicted values to telemetry for the previous three
weeks.
"""
from __future__ import print_function

# Matplotlib setup                                                                                                                                             
# Use Agg backend for command-line (non-interactive) operation                                                                                                 
import matplotlib
matplotlib.use('Agg')

import sys
import numpy as np
import xija
from acis_thermal_check.main import ACISThermalCheck
from acis_thermal_check.utils import calc_off_nom_rolls, get_options
import os

script_path = os.path.abspath(os.path.dirname(__file__))

MSID = dict(dea='1DEAMZT')
# 10/02/14 - Changed YELLOW from 35.0 to 37.5
#            Changed MARGIN from 2.5 to 2.0
#            Modified corresponding VALIDATION_LIMITS:
#                 (1, 2.5) -> (1, 2.0)
#                 (99, 2.5) -> (99, 2.0)
YELLOW = dict(dea=37.5)
MARGIN = dict(dea=2.0)
VALIDATION_LIMITS = {'1DEAMZT': [(1, 2.0),
                                 (50, 1.0),
                                 (99, 2.0)],
                     'PITCH': [(1, 3.0),
                                  (99, 3.0)],
                     'TSCPOS': [(1, 2.5),
                                (99, 2.5)]
                     }
HIST_LIMIT = [20.]

def calc_model(model_spec, states, start, stop, T_dea=None, T_dea_times=None):
    model = xija.ThermalModel('dea', start=start, stop=stop,
                              model_spec=model_spec)
    times = np.array([states['tstart'], states['tstop']])
    model.comp['sim_z'].set_data(states['simpos'], times)
    model.comp['eclipse'].set_data(False)
    model.comp['1deamzt'].set_data(T_dea, T_dea_times)
    model.comp['roll'].set_data(calc_off_nom_rolls(states), times)
    for name in ('ccd_count', 'fep_count', 'vid_board', 'clocking', 'pitch'):
        model.comp[name].set_data(states[name], times)
    model.make()
    model.calc()
    return model

dea_check = ACISThermalCheck("1deamzt", "dea", MSID,
                             YELLOW, MARGIN, VALIDATION_LIMITS,
                             HIST_LIMIT, calc_model)

def main():
    opt, args = get_options("1DEAMZT", "dea", script_path)
    try:
        dea_check.driver(opt)
    except Exception as msg:
        if opt.traceback:
            raise
        else:
            print("ERROR:", msg)
            sys.exit(1)

if __name__ == '__main__':
    main()
