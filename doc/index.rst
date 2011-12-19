.. dpa documentation master file, created by

Chandra DPA model tools
==================================

This suite of tools provides the tools to use and maintain the Chandra ACIS
DPA model.  The key elements are:

  - ``dpa_check.py``: Thermal check of command loads and validate DPA 
    model against recent telemetry

The DPA tools depend on Sybase tables and in particular the commanded states database
which is accessed primarily via the Chandra.cmd_states_ module.

.. _Chandra.cmd_states: ../pydocs/Chandra.cmd_states.html

dpa_check
========================

Overview
-----------

This code generates backstop load review outputs for checking the ACIS DPA
temperature 1DPAMZT.  It also generates DPA model validation plots comparing
predicted values to telemetry for the previous three weeks.

Command line options
---------------------

Typical use case
^^^^^^^^^^^^^^^^^

In the typical use case for doing load review the ``dpa_check`` tool will
propagate forward from a 5-minute average of the last available telemetry using
the ``cmd_states`` table.  The following options control the runtime behavior
of ``dpa_check``.

========================= ================================== ===================
Option                    Description                        Default           
========================= ================================== ===================
  --outdir=OUTDIR         Output directory                   out
  --oflsdir=OFLSDIR       Load products OFLS directory       None
  --model-spec=MODEL_SPEC DPA model specification file       dpa_model_spec.json
  --days=DAYS             Days of validation data (days)     21
  --run-start=RUN_START   Start time for regression testing  None
  --traceback=TRACEBACK   Enable tracebacks                  True
  --verbose=VERBOSE       Verbosity 0=quiet 1=normal 2=debug 1 (normal)
  --version               Print version                      
========================= ================================== ===================

Custom initial conditions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the event that the Ska database is unavailable or specific
initial conditions are desired, the following options are provided.  The
only required option in this case is ``--T-dpa``.  All the rest have
default values that will produce a conservative (hot) prediction.

*NOTE: Specifying custom conditions STILL REQUIRES the Ska database in the current release.*

========================= ================================== ===================
Option                    Description                        Default           
========================= ================================== ===================
  --T-dpa=T_DPA           Initial 1DPAMZT temperature (degC) None
  --ccd-count=CCD_COUNT   Initial number of CCDs             6
  --fep-count=FEP_COUNT   Initial number of FEPs             6
  --vid-board=VID_BOARD   Initial state of ACIS vid_board    1
  --clocking=CLOCKING     Initial state of ACIS clocking     1
  --simpos=SIMPOS         Initial SIM-Z position (steps)     75766
  --pitch=PITCH           Initial pitch (degrees)            150
========================= ================================== ===================

Usage
--------

The typical way to use the ``dpa_check`` load review tool is via the script
launcher ``/proj/sot/ska/bin/dpa_check``.  This script sets up the Ska runtime
environment to ensure access to the correct python libraries.  This must be run
on a 64-bit linux machine.

::

  /proj/sot/ska/bin/dpa_check --oflsdir=/data/mpcrit1/mplogs/2009/MAY1809/oflsb \
                              --outdir=out 
  
  /proj/sot/ska/bin/dpa_check --oflsdir=/data/mpcrit1/mplogs/2009/MAY1809/oflsb \
                              --simpos=-99616 --pitch=130.0 --T-dpa=22.2 \
                              --ccd-count=1 --fep-count=1

  /proj/sot/ska/bin/dpa_check --outdir=regress2010 --run-start=2010:365 --days=360
 
