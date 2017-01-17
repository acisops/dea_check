.. dea_check documentation master file

1DEAMZT Thermal Model (``dea_check``)
=====================================

.. |acis_thermal_check| replace:: ``acis_thermal_check``
.. _acis_thermal_check: http://cxc.harvard.edu/acis/acis_thermal_check

Overview
--------

This code generates backstop load review outputs for checking the ACIS temperature
1DEAMZT. It also generates model validation plots for 1DEAMZT, comparing predicted
values to telemetry for the previous three weeks. ``dea_check`` depends on the
|acis_thermal_check|_ Python package for nearly all of its functionality.

Installation and Development
----------------------------

This assumes that you have a cloned copy of ``dea_check`` from
http://github.com/acisops/dea_check. If you have your own Python/Ska environment
available (on a laptop or some other machine), and you have write permissions on it,
to install the package simply run:

::

    python setup.py install

from the top-level directory of the package. This will install ``dea_check`` as a
Python package, including installing the ``dea_check`` command-line script into the
same ``bin`` directory that the Python executable is in.

If you are running and testing this package using the flight-approved Ska environment
on the HEAD LAN, you will not be able to directly install into this environment but
can install ``dea_check`` as a local package. In this case, the command is slightly
modified:

::

    python setup.py install --user

which will install the package under a path given by the ``site.USER_BASE`` variable
in Python, which on Linux is ``~/.local``. This path can be modified by setting the
environment variable ``PYTHONUSERBASE`` to the desired path before running the above
command. You will need to add ``${PYTHONUSERBASE}/bin`` to your ``PATH`` environment
variable in order to run the ``dea_check`` script from there.

If you are doing frequent development and would like to be able to change the code
on the fly and re-run without having to reinstall the code every time, you can use the
``develop`` option of ``setup.py``, which lets you run the code from the source directory
itself:

::

    python setup.py develop [--user]

where the ``--user`` flag is again only necessary if you do not have write permissions for
the Python environment you are installing into. If you use ``develop``, all imports of
the ``dea_check`` package will refer back to the code in the source directory that you are
working from.

Command line options
--------------------

Typical use case
^^^^^^^^^^^^^^^^

In the typical use case for doing load review the ``dea_check`` tool will propagate
forward from a 5-minute average of the last available telemetry using the ``cmd_states``
table. The following options control the runtime behavior of the ``dea_check`` script:

========================= ================================== ===================
Option                    Description                        Default           
========================= ================================== ===================
  --outdir=OUTDIR         Output directory                   out
  --oflsdir=OFLSDIR       Load products OFLS directory       None
  --model-spec=MODEL_SPEC Model specification file           dea_model_spec.json
  --days=DAYS             Days of validation data (days)     21
  --run-start=RUN_START   Start time for regression testing  None
  --traceback=TRACEBACK   Enable tracebacks                  True
  --verbose=VERBOSE       Verbosity 0=quiet 1=normal 2=debug 1 (normal)
  --version               Print version                      
========================= ================================== ===================

Custom initial conditions
^^^^^^^^^^^^^^^^^^^^^^^^^

In the event that the Ska database is unavailable or specific initial conditions
are desired, the following options are provided. The only required option is that of
the initial temperature:

.. note::

    Specifying custom conditions *still requires* the Ska database in the current release.

All the rest of the options have default values that will produce a conservative (hot)
prediction:

========================= ==================================== ===================
Option                    Description                          Default
========================= ==================================== ===================
  --T-dea=T_DEA           Initial 1DEAMZT temperature (degC)   None
  --ccd-count=CCD_COUNT   Initial number of CCDs               6
  --fep-count=FEP_COUNT   Initial number of FEPs               6
  --vid-board=VID_BOARD   Initial state of ACIS vid_board      1
  --clocking=CLOCKING     Initial state of ACIS clocking       1
  --simpos=SIMPOS         Initial SIM-Z position (steps)       75616
  --pitch=PITCH           Initial pitch (degrees)              150
  --dh_heater=DH_HEATER   ACIS DH Heater on/off (PSMC only)    0
========================= ==================================== ===================

Example Invocations
-------------------

::

  dea_check --oflsdir=/data/acis/LoadReviews/2009/MAY1809/oflsb --outdir=out 
  
  dea_check --oflsdir=/data/acis/LoadReviews/2009/MAY1809/oflsb --simpos=-99616 \
            --pitch=130.0 --T-dea=22.2 --ccd-count=1 --fep-count=1

  dea_check --outdir=regress2010 --run-start=2010:365 --days=360
  

Regression Tests
----------------

Running Tests
^^^^^^^^^^^^^

``dea_check`` comes with a regression test suite which uses `py.test <http://pytest.org/>`_ to
run the tests by comparing the answers given by the code to a "gold standard" set of answers. To
determine if code changes pass these tests, within a cloned copy of ``dea_check`` in the
``dea_check/dea_check/tests`` subdirectory run:

::

    py.test -s

The ``-s`` flag outputs the ``stdout`` and ``stderr`` to screen so you can see what's going on.
If you'd rather not see that, just remove the flag. 

If you have changed the model specification file or made another change that will change the answers,
to generate new answers run:

::

    py.test -s --generate_answers=answer_dir

where ``answer_dir`` is a directory to output the new answers to. The new answers should be reviewed
with the ACIS operations team before copying to the default location for the "gold standard"
answers.

Answers should be generated using the ``py.test`` that is part of the flight Ska environment.

Adding New Tests
^^^^^^^^^^^^^^^^

If you want to add a new test for 1DEAMZT which runs the model for a particular load, it is very easy.
This test should be added to ``dea_check/dea_check/tests/test_dea.py``, and have the following form:

.. code-block:: python

    def test_dea_may3016(generate_answers):
        run_start = "2016:122:12:00:00.000"
        load_week = "MAY3016"
        dea_test_template(generate_answers, run_start, load_week)

This test runs the model for the ``"MAY3016"`` ``load_week``, at a particular value of ``run_start``. 
These arguments are fed into the ``dea_test_template`` fucntion, which runs the actual test. The function
should have a name in the format ``test_dea_{load_week}``, and it must take the ``generate_answers``
argument. 