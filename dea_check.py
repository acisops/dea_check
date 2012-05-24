#!/usr/bin/env python

"""
========================
dpa_check
========================

This code generates backstop load review outputs for checking the ACIS
DPA temperature 1DPAMZT.  It also generates DPA model validation
plots comparing predicted values to telemetry for the previous three weeks.
"""

import sys
import os
import glob
import logging
from pprint import pformat
import re
import time
import shutil
import pickle

import numpy as np
import Ska.DBI
import Ska.Table
import Ska.Numpy
import Ska.engarchive.fetch_sci as fetch
from Chandra.Time import DateTime

import Chandra.cmd_states as cmd_states
# Matplotlib setup
# Use Agg backend for command-line (non-interactive) operation
import matplotlib
if __name__ == '__main__':
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import Ska.Matplotlib

import xija

MSID = dict(dpa='1DPAMZT')
YELLOW = dict(dpa=35.0)
MARGIN = dict(dpa=2.5)
VALIDATION_LIMITS = {'1DPAMZT': [(1, 2.5),
                                 (50, 1.0),
                                 (99, 2.5)],
                     'PITCH': [(1, 3.0),
                                  (99, 3.0)],
                     'TSCPOS': [(1, 2.5),
                                (99, 2.5)]
                     }

TASK_DATA = os.path.dirname(__file__)
URL = "http://cxc.harvard.edu/mta/ASPECT/dpa_daily_check"

logger = logging.getLogger('dpa_check')

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
                      default=os.path.join(TASK_DATA, 'dpa_model_spec.json'),
                       help="DPA model specification file")
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
    parser.add_option("--T-dpa",
                      type='float',
                      help="Starting 1DPAMZT temperature (degC)")
    parser.add_option("--version",
                      action='store_true',
                      help="Print version")

    opt, args = parser.parse_args()
    return opt, args


def main(opt):
    if not os.path.exists(opt.outdir):
        os.mkdir(opt.outdir)

    config_logging(opt.outdir, opt.verbose)

    # Store info relevant to processing for use in outputs
    proc = dict(run_user=os.environ['USER'],
                run_time=time.ctime(),
                errors=[],
                dpa_limit=YELLOW['dpa'] - MARGIN['dpa'],
                )
    logger.info('##############################'
                '#######################################')
    logger.info('# dpa_check.py run at %s by %s'
                % (proc['run_time'], proc['run_user']))
    logger.info('# dpa_check version = {}'.format(VERSION))
    logger.info('# model_spec file = %s' % os.path.abspath(opt.model_spec))
    logger.info('###############################'
                '######################################\n')

    logger.info('Command line options:\n%s\n' % pformat(opt.__dict__))

    # Connect to database (NEED TO USE aca_read)
    logger.info('Connecting to database to get cmd_states')
    db = Ska.DBI.DBI(dbi='sybase', server='sybase', user='aca_read',
                     database='aca')

    tnow = DateTime(opt.run_start).secs
    if opt.oflsdir is not None:
        # Get tstart, tstop, commands from backstop file in opt.oflsdir
        bs_cmds = get_bs_cmds(opt.oflsdir)
        tstart = bs_cmds[0]['time']
        tstop = bs_cmds[-1]['time']

        proc.update(dict(datestart=DateTime(tstart).date,
                         datestop=DateTime(tstop).date))
    else:
        tstart = tnow

    # Get temperature telemetry for 3 weeks prior to min(tstart, NOW)
    tlm = get_telem_values(min(tstart, tnow),
                           ['1dpamzt',
                            'sim_z', 'aosares1',
                            'dp_dpa_power'],
                           days=opt.days,
                           name_map={'sim_z': 'tscpos',
                                     'aosares1': 'pitch'})
    tlm['tscpos'] = tlm['tscpos'] * -397.7225924607

    # make predictions on oflsdir if defined
    if opt.oflsdir is not None:
        pred = make_week_predict(opt, tstart, tstop, bs_cmds, tlm, db)
    else:
        pred = dict(plots=None, viols=None, times=None, states=None,
                    temps=None)

    # Validation
    plots_validation = make_validation_plots(opt, tlm, db)
    valid_viols = make_validation_viols(plots_validation)
    if len(valid_viols) > 0:
        # generate daily plot url if outdir in expected year/day format
        daymatch = re.match('.*(\d{4})/(\d{3})', opt.outdir)
        if opt.oflsdir is None and daymatch:
            url = os.path.join(URL, daymatch.group(1), daymatch.group(2))
            logger.info('validation warning(s) at %s' % url)
        else:
            logger.info('validation warning(s) in output at %s' % opt.outdir)

    write_index_rst(opt, proc, plots_validation, valid_viols=valid_viols,
                    plots=pred['plots'], viols=pred['viols'])
    rst_to_html(opt, proc)

    return dict(opt=opt, states=pred['states'], times=pred['times'],
                temps=pred['temps'], plots=pred['plots'],
                viols=pred['viols'], proc=proc,
                plots_validation=plots_validation)


def calc_model(model_spec, states, start, stop, T_dpa=None, T_dpa_times=None):
    model = xija.ThermalModel('dpa', start=start, stop=stop,
                              model_spec=model_spec)

    times = np.array([states['tstart'], states['tstop']])
    model.comp['sim_z'].set_data(states['simpos'], times)
    model.comp['eclipse'].set_data(False)
    model.comp['1dpamzt'].set_data(T_dpa, T_dpa_times)

    for name in ('ccd_count', 'fep_count', 'vid_board', 'clocking', 'pitch'):
        model.comp[name].set_data(states[name], times)

    model.make()
    model.calc()
    return model


def make_week_predict(opt, tstart, tstop, bs_cmds, tlm, db):

    # Try to make initial state0 from cmd line options
    state0 = dict((x, getattr(opt, x))
                  for x in ('pitch', 'simpos', 'ccd_count', 'fep_count',
                            'vid_board', 'clocking', 'T_dpa'))
    state0.update({'tstart': tstart - 30,
                   'tstop': tstart,
                   'datestart': DateTime(tstart - 30).date,
                   'datestop': DateTime(tstart).date,
                   'q1': 0.0, 'q2': 0.0, 'q3': 0.0, 'q4': 1.0,
                   }
                  )

    # If cmd lines options were not fully specified then get state0 as last
    # cmd_state that starts within available telemetry.  Update with the
    # mean temperatures at the start of state0.
    if None in state0.values():
        state0 = cmd_states.get_state0(tlm['date'][-5], db,
                                       datepar='datestart')
        ok = ((tlm['date'] >= state0['tstart'] - 700) &
              (tlm['date'] <= state0['tstart'] + 700))
        state0.update({'T_dpa': np.mean(tlm['1dpamzt'][ok])})

    # TEMPORARY HACK: core model doesn't actually support predictive
    # active heater yet.  Initial temperature determines active heater
    # state for predictions now.
    if state0['T_dpa'] < 15:
        state0['T_dpa'] = 15.0

    logger.debug('state0 at %s is\n%s' % (DateTime(state0['tstart']).date,
                                           pformat(state0)))

    # Get commands after end of state0 through first backstop command time
    cmds_datestart = state0['datestop']
    cmds_datestop = bs_cmds[0]['date']

    # Get timeline load segments including state0 and beyond.
    timeline_loads = db.fetchall("""SELECT * from timeline_loads
                                 WHERE datestop > '%s'
                                 and datestart < '%s'"""
                                 % (cmds_datestart, cmds_datestop))
    logger.info('Found {} timeline_loads  after {}'.format(
            len(timeline_loads), cmds_datestart))

    # Get cmds since datestart within timeline_loads
    db_cmds = cmd_states.get_cmds(cmds_datestart, db=db, update_db=False,
                                  timeline_loads=timeline_loads)

    # Delete non-load cmds that are within the backstop time span
    # => Keep if timeline_id is not None or date < bs_cmds[0]['time']
    db_cmds = [x for x in db_cmds if (x['timeline_id'] is not None or
                                      x['time'] < bs_cmds[0]['time'])]

    logger.info('Got %d cmds from database between %s and %s' %
                  (len(db_cmds), cmds_datestart, cmds_datestop))

    # Get the commanded states from state0 through the end of backstop commands
    states = cmd_states.get_states(state0, db_cmds + bs_cmds)
    states[-1].datestop = bs_cmds[-1]['date']
    states[-1].tstop = bs_cmds[-1]['time']
    logger.info('Found %d commanded states from %s to %s' %
                 (len(states), states[0]['datestart'], states[-1]['datestop']))

    # Create array of times at which to calculate DPA temps, then do it.
    logger.info('Calculating DPA thermal model')

    model = calc_model(opt.model_spec, states, state0['tstart'], tstop,
                       state0['T_dpa'])

    # Make the DPA limit check plots and data files
    plt.rc("axes", labelsize=10, titlesize=12)
    plt.rc("xtick", labelsize=10)
    plt.rc("ytick", labelsize=10)
    temps = {'dpa': model.comp['1dpamzt'].mvals}
    plots = make_check_plots(opt, states, model.times, temps, tstart)
    viols = make_viols(opt, states, model.times, temps)
    write_states(opt, states)
    write_temps(opt, model.times, temps)

    return dict(opt=opt, states=states, times=model.times, temps=temps,
               plots=plots, viols=viols)


def make_validation_viols(plots_validation):
    """
    Find limit violations where MSID quantile values are outside the
    allowed range.
    """

    logger.info('Checking for validation violations')

    viols = []

    for plot in plots_validation:
        # 'plot' is actually a structure with plot info and stats about the
        #  plotted data for a particular MSID.  'msid' can be a real MSID
        #  (1DPAMZT) or pseudo like 'POWER'
        msid = plot['msid']

        # Make sure validation limits exist for this MSID
        if msid not in VALIDATION_LIMITS:
            continue

        # Cycle through defined quantiles (e.g. 99 for 99%) and corresponding
        # limit values for this MSID.
        for quantile, limit in VALIDATION_LIMITS[msid]:
            # Get the quantile statistic as calculated when making plots
            msid_quantile_value = float(plot['quant%02d' % quantile])

            # Check for a violation and take appropriate action
            if abs(msid_quantile_value) > limit:
                viol = {'msid': msid,
                        'value': msid_quantile_value,
                        'limit': limit,
                        'quant': quantile,
                        }
                viols.append(viol)
                logger.info('WARNING: %s %d%% quantile value of %s exceeds '
                            'limit of %.2f' %
                            (msid, quantile, msid_quantile_value, limit))

    return viols


def get_bs_cmds(oflsdir):
    """Return commands for the backstop file in opt.oflsdir.
    """
    import Ska.ParseCM
    backstop_file = globfile(os.path.join(oflsdir, 'CR*.backstop'))
    logger.info('Using backstop file %s' % backstop_file)
    bs_cmds = Ska.ParseCM.read_backstop(backstop_file)
    logger.info('Found %d backstop commands between %s and %s' %
                  (len(bs_cmds), bs_cmds[0]['date'], bs_cmds[-1]['date']))

    return bs_cmds


def get_telem_values(tstart, msids, days=14, name_map={}):
    """
    Fetch last ``days`` of available ``msids`` telemetry values before
    time ``tstart``.

    :param tstart: start time for telemetry (secs)
    :param msids: fetch msids list
    :param days: length of telemetry request before ``tstart``
    :param dt: sample time (secs)
    :param name_map: dict mapping msid to recarray col name
    :returns: np recarray of requested telemetry values from fetch
    """
    tstart = DateTime(tstart).secs
    start = DateTime(tstart - days * 86400).date
    stop = DateTime(tstart).date
    logger.info('Fetching telemetry between %s and %s' % (start, stop))
    msidset = fetch.MSIDset(msids, start, stop, stat='5min')
    start = max(x.times[0] for x in msidset.values())
    stop = min(x.times[-1] for x in msidset.values())
    msidset.interpolate(328.0, start, stop + 1)  # 328 for '5min' stat

    # Finished when we found at least 4 good records (20 mins)
    if len(msidset.times) < 4:
        raise ValueError('Found no telemetry within %d days of %s'
                         % (days, str(tstart)))

    outnames = ['date'] + [name_map.get(x, x) for x in msids]
    vals = {name_map.get(x, x): msidset[x].vals for x in msids}
    vals['date'] = msidset.times
    out = Ska.Numpy.structured_array(vals, colnames=outnames)

    return out


def rst_to_html(opt, proc):
    """Run rst2html.py to render index.rst as HTML"""

    # First copy CSS files to outdir
    import Ska.Shell
    import docutils.writers.html4css1
    dirname = os.path.dirname(docutils.writers.html4css1.__file__)
    shutil.copy2(os.path.join(dirname, 'html4css1.css'), opt.outdir)

    shutil.copy2(os.path.join(TASK_DATA, 'dpa_check.css'), opt.outdir)

    spawn = Ska.Shell.Spawn(stdout=None)
    infile = os.path.join(opt.outdir, 'index.rst')
    outfile = os.path.join(opt.outdir, 'index.html')
    status = spawn.run(['rst2html.py',
                        '--stylesheet-path={}'
                        .format(os.path.join(opt.outdir, 'dpa_check.css')),
                        infile, outfile])
    if status != 0:
        proc['errors'].append('rst2html.py failed with status {}: see run log'
                              .format(status))
        logger.error('rst2html.py failed')
        logger.error(''.join(spawn.outlines) + '\n')

    # Remove the stupid <colgroup> field that docbook inserts.  This
    # <colgroup> prevents HTML table auto-sizing.
    del_colgroup = re.compile(r'<colgroup>.*?</colgroup>', re.DOTALL)
    outtext = del_colgroup.sub('', open(outfile).read())
    open(outfile, 'w').write(outtext)


def config_logging(outdir, verbose):
    """Set up file and console logger.
    See http://docs.python.org/library/logging.html
              #logging-to-multiple-destinations
    """
    # Disable auto-configuration of root logger by adding a null handler.
    # This prevents other modules (e.g. Chandra.cmd_states) from generating
    # a streamhandler by just calling logging.info(..).
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
    rootlogger = logging.getLogger()
    rootlogger.addHandler(NullHandler())

    loglevel = {0: logging.CRITICAL,
                1: logging.INFO,
                2: logging.DEBUG}.get(verbose, logging.INFO)

    logger = logging.getLogger('dpa_check')
    logger.setLevel(loglevel)

    formatter = logging.Formatter('%(message)s')

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    filehandler = logging.FileHandler(
        filename=os.path.join(outdir, 'run.dat'), mode='w')
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)


def write_states(opt, states):
    """Write states recarray to file states.dat"""
    outfile = os.path.join(opt.outdir, 'states.dat')
    logger.info('Writing states to %s' % outfile)
    out = open(outfile, 'w')
    fmt = {'power': '%.1f',
           'pitch': '%.2f',
           'tstart': '%.2f',
           'tstop': '%.2f',
           }
    newcols = list(states.dtype.names)
    newcols.remove('T_dpa')
    newstates = np.rec.fromarrays([states[x] for x in newcols], names=newcols)
    Ska.Numpy.pprint(newstates, fmt, out)
    out.close()


def write_temps(opt, times, temps):
    """Write temperature predictions to file temperatures.dat"""
    outfile = os.path.join(opt.outdir, 'temperatures.dat')
    logger.info('Writing temperatures to %s' % outfile)
    T_dpa = temps['dpa']
    temp_recs = [(times[i], DateTime(times[i]).date, T_dpa[i])
                 for i in xrange(len(times))]
    temp_array = np.rec.fromrecords(
        temp_recs, names=('time', 'date', '1dpamzt'))

    fmt = {'1dpamzt': '%.2f',
           'time': '%.2f'}
    out = open(outfile, 'w')
    Ska.Numpy.pprint(temp_array, fmt, out)
    out.close()


def write_index_rst(opt, proc, plots_validation, valid_viols=None,
                    plots=None, viols=None):
    """
    Make output text (in ReST format) in opt.outdir.
    """
    # Django setup (used for template rendering)
    import django.template
    import django.conf
    try:
        django.conf.settings.configure()
    except RuntimeError, msg:
        print msg

    outfile = os.path.join(opt.outdir, 'index.rst')
    logger.info('Writing report file %s' % outfile)
    django_context = django.template.Context(
        {'opt': opt,
         'plots': plots,
         'viols': viols,
         'valid_viols': valid_viols,
         'proc': proc,
         'plots_validation': plots_validation,
         })
    index_template_file = ('index_template.rst'
                           if opt.oflsdir else
                           'index_template_val_only.rst')
    index_template = open(os.path.join(TASK_DATA, index_template_file)).read()
    index_template = re.sub(r' %}\n', ' %}', index_template)
    template = django.template.Template(index_template)
    open(outfile, 'w').write(template.render(django_context))


def make_viols(opt, states, times, temps):
    """
    Find limit violations where predicted temperature is above the
    yellow limit minus margin.
    """
    logger.info('Checking for limit violations')

    viols = dict((x, []) for x in MSID)
    for msid in MSID:
        temp = temps[msid]
        plan_limit = YELLOW[msid] - MARGIN[msid]
        bad = np.concatenate(([False],
                             temp >= plan_limit,
                             [False]))
        changes = np.flatnonzero(bad[1:] != bad[:-1]).reshape(-1, 2)

        for change in changes:
            viol = {'datestart': DateTime(times[change[0]]).date,
                    'datestop': DateTime(times[change[1] - 1]).date,
                    'maxtemp': temp[change[0]:change[1]].max()
                    }
            logger.info('WARNING: %s exceeds planning limit of %.2f '
                        'degC from %s to %s'
                        % (MSID[msid], plan_limit, viol['datestart'],
                           viol['datestop']))
            viols[msid].append(viol)
    return viols


def plot_two(fig_id, x, y, x2, y2,
             linestyle='-', linestyle2='-',
             color='blue', color2='magenta',
             ylim=None, ylim2=None,
             xlabel='', ylabel='', ylabel2='', title='',
             figsize=(7, 3.5),
             ):
    """Plot two quantities with a date x-axis"""
    xt = Ska.Matplotlib.cxctime2plotdate(x)
    fig = plt.figure(fig_id, figsize=figsize)
    fig.clf()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot_date(xt, y, fmt='-', linestyle=linestyle, color=color)
    ax.set_xlim(min(xt), max(xt))
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid()

    ax2 = ax.twinx()

    xt2 = Ska.Matplotlib.cxctime2plotdate(x2)
    ax2.plot_date(xt2, y2, fmt='-', linestyle=linestyle2, color=color2)
    ax2.set_xlim(min(xt), max(xt))
    if ylim2:
        ax2.set_ylim(*ylim2)
    ax2.set_ylabel(ylabel2, color=color2)
    ax2.xaxis.set_visible(False)

    Ska.Matplotlib.set_time_ticks(ax)
    [label.set_rotation(30) for label in ax.xaxis.get_ticklabels()]
    [label.set_color(color2) for label in ax2.yaxis.get_ticklabels()]

    fig.subplots_adjust(bottom=0.22)

    return {'fig': fig, 'ax': ax, 'ax2': ax2}


def make_check_plots(opt, states, times, temps, tstart):
    """
    Make output plots.

    :param opt: options
    :param states: commanded states
    :param times: time stamps (sec) for temperature arrays
    :param temps: dict of temperatures
    :param tstart: load start time
    :rtype: dict of review information including plot file names
    """
    plots = {}

    # Start time of loads being reviewed expressed in units for plotdate()
    load_start = Ska.Matplotlib.cxctime2plotdate([tstart])[0]

    logger.info('Making temperature check plots')
    for fig_id, msid in enumerate(('dpa',)):
        plots[msid] = plot_two(fig_id=fig_id + 1,
                               x=times,
                               y=temps[msid],
                               x2=pointpair(states['tstart'], states['tstop']),
                               y2=pointpair(states['pitch']),
                               title=MSID[msid],
                               xlabel='Date',
                               ylabel='Temperature (C)',
                               ylabel2='Pitch (deg)',
                               ylim2=(40, 180),
                               )
        plots[msid]['ax'].axhline(YELLOW[msid], linestyle='-', color='y',
                                  linewidth=2.0)
        plots[msid]['ax'].axhline(YELLOW[msid] - MARGIN[msid], linestyle='--',
                                  color='y', linewidth=2.0)
        plots[msid]['ax'].axvline(load_start, linestyle=':', color='g',
                                  linewidth=1.0)
        filename = MSID[msid].lower() + '.png'
        outfile = os.path.join(opt.outdir, filename)
        logger.info('Writing plot file %s' % outfile)
        plots[msid]['fig'].savefig(outfile)
        plots[msid]['filename'] = filename

    plots['pow_sim'] = plot_two(
        fig_id=3,
        title='ACIS CCDs and SIM-Z position',
        xlabel='Date',
        x=pointpair(states['tstart'], states['tstop']),
        y=pointpair(states['ccd_count']),
        ylabel='CCD_COUNT',
        ylim=(-0.1, 6.1),
        x2=pointpair(states['tstart'], states['tstop']),
        y2=pointpair(states['simpos']),
        ylabel2='SIM-Z (steps)',
        ylim2=(-105000, 105000),
        )
    plots['pow_sim']['ax'].axvline(load_start, linestyle=':', color='g',
                                   linewidth=1.0)
    plots['pow_sim']['fig'].subplots_adjust(right=0.85)
    filename = 'pow_sim.png'
    outfile = os.path.join(opt.outdir, filename)
    logger.info('Writing plot file %s' % outfile)
    plots['pow_sim']['fig'].savefig(outfile)
    plots['pow_sim']['filename'] = filename

    return plots


def get_states(datestart, datestop, db):
    """Get states exactly covering date range

    :param datestart: start date
    :param datestop: stop date
    :param db: database handle
    :returns: np recarry of states
    """
    datestart = DateTime(datestart).date
    datestop = DateTime(datestop).date
    logger.info('Getting commanded states between %s - %s' %
                 (datestart, datestop))

    # Get all states that intersect specified date range
    cmd = """SELECT * FROM cmd_states
             WHERE datestop > '%s' AND datestart < '%s'
             ORDER BY datestart""" % (datestart, datestop)
    logger.debug('Query command: %s' % cmd)
    states = db.fetchall(cmd)
    logger.info('Found %d commanded states' % len(states))

    # Add power columns to states and tlm
    # states = Ska.Numpy.add_column(states, 'power', get_power(states))

    # Set start and end state date/times to match telemetry span.  Extend the
    # state durations by a small amount because of a precision issue converting
    # to date and back to secs.  (The reference tstop could be just over the
    # 0.001 precision of date and thus cause an out-of-bounds error when
    # interpolating state values).
    states[0].tstart = DateTime(datestart).secs - 0.01
    states[0].datestart = DateTime(states[0].tstart).date
    states[-1].tstop = DateTime(datestop).secs + 0.01
    states[-1].datestop = DateTime(states[-1].tstop).date

    return states


def make_validation_plots(opt, tlm, db):
    """
    Make validation output plots.

    :param outdir: output directory
    :param tlm: telemetry
    :param db: database handle
    :returns: list of plot info including plot file names
    """
    outdir = opt.outdir
    start = tlm['date'][0]
    stop = tlm['date'][-1]
    states = get_states(start, stop, db)

    # Create array of times at which to calculate DPA temperatures, then do it
    logger.info('Calculating DPA thermal model for validation')

    model = calc_model(opt.model_spec, states, start, stop)

    # Interpolate states onto the tlm.date grid
    # state_vals = cmd_states.interpolate_states(states, model.times)
    pred = {'1dpamzt': model.comp['1dpamzt'].mvals,
            'pitch': model.comp['pitch'].mvals,
            'tscpos': model.comp['sim_z'].mvals
            }

    idxs = Ska.Numpy.interpolate(np.arange(len(tlm)), tlm['date'], model.times,
                                 method='nearest')
    tlm = tlm[idxs]

    labels = {'1dpamzt': 'Degrees (C)',
              'pitch': 'Pitch (degrees)',
              'tscpos': 'SIM-Z (steps/1000)',
              }

    scales = {'tscpos': 1000.}

    fmts = {'1dpamzt': '%.2f',
            'pitch': '%.3f',
            'tscpos': '%d'}

    plots = []
    logger.info('Making DPA model validation plots and quantile table')
    quantiles = (1, 5, 16, 50, 84, 95, 99)
    # store lines of quantile table in a string and write out later
    quant_table = ''
    quant_head = ",".join(['MSID'] + ["quant%d" % x for x in quantiles])
    quant_table += quant_head + "\n"
    for fig_id, msid in enumerate(sorted(pred)):
        plot = dict(msid=msid.upper())
        fig = plt.figure(10 + fig_id, figsize=(7, 3.5))
        fig.clf()
        scale = scales.get(msid, 1.0)
        ticklocs, fig, ax = plot_cxctime(model.times, tlm[msid] / scale,
                                         fig=fig, fmt='-r')
        ticklocs, fig, ax = plot_cxctime(model.times, pred[msid] / scale,
                                         fig=fig, fmt='-b')
        ax.set_title(msid.upper() + ' validation')
        ax.set_ylabel(labels[msid])
        ax.grid()
        filename = msid + '_valid.png'
        outfile = os.path.join(outdir, filename)
        logger.info('Writing plot file %s' % outfile)
        fig.savefig(outfile)
        plot['lines'] = filename

        # Make quantiles
        if msid == '1dpamzt':
            ok = tlm[msid] > 20.0
        else:
            ok = np.ones(len(tlm[msid]), dtype=bool)
        diff = np.sort(tlm[msid][ok] - pred[msid][ok])
        quant_line = "%s" % msid
        for quant in quantiles:
            quant_val = diff[(len(diff) * quant) // 100]
            plot['quant%02d' % quant] = fmts[msid] % quant_val
            quant_line += (',' + fmts[msid] % quant_val)
        quant_table += quant_line + "\n"

        for histscale in ('log', 'lin'):
            fig = plt.figure(20 + fig_id, figsize=(4, 3))
            fig.clf()
            ax = fig.gca()
            ax.hist(diff / scale, bins=50, log=(histscale == 'log'))
            ax.set_title(msid.upper() + ' residuals: data - model')
            ax.set_xlabel(labels[msid])
            fig.subplots_adjust(bottom=0.18)
            filename = '%s_valid_hist_%s.png' % (msid, histscale)
            outfile = os.path.join(outdir, filename)
            logger.info('Writing plot file %s' % outfile)
            fig.savefig(outfile)
            plot['hist' + histscale] = filename

        plots.append(plot)

    filename = os.path.join(outdir, 'validation_quant.csv')
    logger.info('Writing quantile table %s' % filename)
    f = open(filename, 'w')
    f.write(quant_table)
    f.close()

    # If run_start is specified this is likely for regression testing
    # or other debugging.  In this case write out the full predicted and
    # telemetered dataset as a pickle.
    if opt.run_start:
        filename = os.path.join(outdir, 'validation_data.pkl')
        logger.info('Writing validation data %s' % filename)
        f = open(filename, 'w')
        pickle.dump({'pred': pred, 'tlm': tlm}, f, protocol=-1)
        f.close()

    return plots


def plot_cxctime(times, y, fig=None, **kwargs):
    """Make a date plot where the X-axis values are in CXC time.  If no ``fig``
    value is supplied then the current figure will be used (and created
    automatically if needed).  Any additional keyword arguments
    (e.g. ``fmt='b-'``) are passed through to the ``plot_date()`` function.

    :param times: CXC time values for x-axis (date)
    :param y: y values
    :param fig: pyplot figure object (optional)
    :param **kwargs: keyword args passed through to ``plot_date()``

    :rtype: ticklocs, fig, ax = tick locations, figure, and axes object.
    """
    if fig is None:
        fig = plt.gcf()

    ax = fig.gca()
    import Ska.Matplotlib
    ax.plot_date(Ska.Matplotlib.cxctime2plotdate(times), y, **kwargs)
    ticklocs = Ska.Matplotlib.set_time_ticks(ax)
    fig.autofmt_xdate()

    return ticklocs, fig, ax


def get_power(states):
    """
    Determine the power value in each state by finding the entry in calibration
    power table with the same ``fep_count``, ``vid_board``, and ``clocking``
    values.

    :param states: input states
    :rtype: numpy array of power corresponding to states
    """

    # Make a tuple of values that define a unique power state
    powstate = lambda x: tuple(x[col] for col in ('fep_count', 'vid_board',
                                                  'clocking'))

    # dpa_power charactestic is a list of 4-tuples (fep_count vid_board
    # clocking power_avg).  Build a dict to allow access to power_avg for
    # available (fep_count vid_board clocking) combos.
    power_states = dict((row[0:3], row[3])
                        for row in characteristics.dpa_power)
    try:
        powers = [power_states[powstate(x)] for x in states]
    except KeyError:
        raise ValueError('Unknown power state: %s' % str(powstate(x)))

    return powers


def pointpair(x, y=None):
    if y is None:
        y = x
    return np.array([x, y]).reshape(-1, order='F')


def globfile(pathglob):
    """Return the one file name matching ``pathglob``.  Zero or multiple
    matches raises an IOError exception."""

    files = glob.glob(pathglob)
    if len(files) == 0:
        raise IOError('No files matching %s' % pathglob)
    elif len(files) > 1:
        raise IOError('Multiple files matching %s' % pathglob)
    else:
        return files[0]


if __name__ == '__main__':
    opt, args = get_options()
    if opt.version:
        print VERSION
        sys.exit(0)

    try:
        main(opt)
    except Exception, msg:
        if opt.traceback:
            raise
        else:
            print "ERROR:", msg
            sys.exit(1)
