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
from acis_thermal_check import \
    ACISThermalCheck, \
    calc_off_nom_rolls, \
    get_options
import os

model_path = os.path.abspath(os.path.dirname(__file__))


MSID = {"dea": '1DEAMZT'}
VALIDATION_LIMITS = {'1DEAMZT': [(1, 2.0), (50, 1.0), (99, 2.0)],
                     'PITCH': [(1, 3.0),(99, 3.0)],
                     'TSCPOS': [(1, 2.5), (99, 2.5)]
                     }
HIST_LIMIT = [20.]

def calc_model(model_spec, states, start, stop, T_dea=None, T_dea_times=None,
               dh_heater=None, dh_heater_times=None):
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

def main():
    args = get_options("dea", model_path)
    dea_check = ACISThermalCheck("1deamzt", "dea", MSID, 
                                 VALIDATION_LIMITS, HIST_LIMIT, 
                                 calc_model, args)

    try:
        dea_check.driver()
    except Exception as msg:
        if args.traceback:
            raise
        else:
            print("ERROR:", msg)
            sys.exit(1)

if __name__ == '__main__':
    main()
