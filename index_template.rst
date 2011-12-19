=======================
DPA temperatures check
=======================
.. role:: red

{% if proc.errors %}
Processing Errors
-----------------
.. class:: red
{% endif %}

Summary
--------         
.. class:: borderless

====================  =============================================
Date start            {{proc.datestart}}
Date stop             {{proc.datestop}}
1DPAMZT status        {%if viols.dpa%}:red:`NOT OK`{% else %}OK{% endif%} (limit = {{proc.dpa_limit|floatformat:1}} C)
{% if opt.loaddir %}
Load directory        {{opt.loaddir}}
{% endif %}
Run time              {{proc.run_time}} by {{proc.run_user}}
Run log               `<run.dat>`_
Temperatures          `<temperatures.dat>`_
States                `<states.dat>`_
====================  =============================================

{% if viols.dpa  %}
1DPAMZT Violations
-------------------
=====================  =====================  ==================
Date start             Date stop              Max temperature
=====================  =====================  ==================
{% for viol in viols.dpa %}
{{viol.datestart}}  {{viol.datestop}}  {{viol.maxtemp|floatformat:2}}
{% endfor %}
=====================  =====================  ==================
{% else %}
No 1DPAMZT Violations
{% endif %}

.. image:: {{plots.dpa.filename}}
.. image:: {{plots.pow_sim.filename}}

=======================
DPA Model Validation
=======================

MSID quantiles
---------------

Note: DPA quantiles are calculated using only points where 1DPAMZT > 20 degC.

.. csv-table:: 
   :header: "MSID", "1%", "5%", "16%", "50%", "84%", "95%", "99%"
   :widths: 15, 10, 10, 10, 10, 10, 10, 10

{% for plot in plots_validation %}
{% if plot.quant01 %}
   {{plot.msid}},{{plot.quant01}},{{plot.quant05}},{{plot.quant16}},{{plot.quant50}},{{plot.quant84}},{{plot.quant95}},{{plot.quant99}}
{% endif %}
{% endfor%}

{% if valid_viols %}
Validation Violations
---------------------

.. csv-table:: 
   :header: "MSID", "Quantile", "Value", "Limit"
   :widths: 15, 10, 10, 10

{% for viol in valid_viols %}
   {{viol.msid}},{{viol.quant}},{{viol.value}},{{viol.limit|floatformat:2}}
{% endfor%}

{% else %}
No Validation Violations
{% endif %}


{% for plot in plots_validation %}
{{ plot.msid }}
-----------------------

Note: DPA residual histograms include only points where 1DPAMZT > 20 degC.

Red = telemetry, blue = model

.. image:: {{plot.lines}}
.. image:: {{plot.histlog}}
.. image:: {{plot.histlin}}

{% endfor %}
