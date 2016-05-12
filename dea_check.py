#!/usr/bin/env python

"""
========================
dea_check
========================

This code generates backstop load review outputs for checking the ACIS
DEA temperature 1DEAMZT.  It also generates DEA model validation
plots comparing predicted values to telemetry for the previous three weeks.
"""

import sys
import os
import logging

import numpy as np
import Ska.Sun

# Matplotlib setup
# Use Agg backend for command-line (non-interactive) operation
import matplotlib
if __name__ == '__main__':
    matplotlib.use('Agg')

import xija

from model_check import ModelCheck

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

TASK_DATA = os.path.dirname(__file__)
logger = logging.getLogger('dea_check')

# 10/02/14 -  VERSION file changed from 0.2 to 1.0
_versionfile = os.path.join(os.path.dirname(__file__), 'VERSION')
VERSION = open(_versionfile).read().strip()

def get_options():
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults()
    parser.add_option("--outdir",
                      default="out",
                      help="Output directory")
    parser.add_option("--oflsdir",
                       help="Load products OFLS directory")
    parser.add_option("--model-spec",
                      default=os.path.join(TASK_DATA, 'dea_model_spec.json'),
                       help="DEA model specification file")
    parser.add_option("--days",
                      type='float',
                      default=21.0,
                      help="Days of validation data (days)")
    parser.add_option("--run-start",
                      help="Reference time to replace run start time "
                           "for regression testing")
    parser.add_option("--traceback",
                      default=True,
                      help='Enable tracebacks')
    parser.add_option("--verbose",
                      type='int',
                      default=1,
                      help="Verbosity (0=quiet, 1=normal, 2=debug)")
    parser.add_option("--ccd-count",
                      type='int',
                      default=6,
                      help="Initial number of CCDs (default=6)")
    parser.add_option("--fep-count",
                      type='int',
                      default=6,
                      help="Initial number of FEPs (default=6)")
    parser.add_option("--vid-board",
                      type='int',
                      default=1,
                      help="Initial state of ACIS vid_board (default=1)")
    parser.add_option("--clocking",
                      type='int',
                      default=1,
                      help="Initial state of ACIS clocking (default=1)")
    parser.add_option("--simpos",
                      default=75616,
                      type='float',
                      help="Starting SIM-Z position (steps)")
    parser.add_option("--pitch",
                      default=150.0,
                      type='float',
                      help="Starting pitch (deg)")
    parser.add_option("--T-dea",
                      type='float',
                      help="Starting 1DEAMZT temperature (degC)")
    parser.add_option("--version",
                      action='store_true',
                      help="Print version")

    opt, args = parser.parse_args()
    return opt, args

def calc_off_nom_rolls(states):
    off_nom_rolls = []
    for state in states:
        att = [state[x] for x in ['q1', 'q2', 'q3', 'q4']]
        time = (state['tstart'] + state['tstop']) / 2
        off_nom_rolls.append(Ska.Sun.off_nominal_roll(att, time))
    return np.array(off_nom_rolls)

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

if __name__ == '__main__':
    opt, args = get_options()
    if opt.version:
        print VERSION
        sys.exit(0)
    try:
        dea_check = ModelCheck("1deamzt", "dea", MSID,
                               YELLOW, MARGIN, VALIDATION_LIMITS,
                               calc_model, VERSION)
        dea_check.driver(opt)
    except Exception, msg:
        if opt.traceback:
            raise
        else:
            print "ERROR:", msg
            sys.exit(1)
