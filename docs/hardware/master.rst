Master device
=============

.. jupyter-execute::
    :hide-code:

    %config InlineBackend.figure_format = 'svg'
    import schemdraw
    from schemdraw import elements as elm
    from schemdraw import flow
    import numpy as np
    from matplotlib import pyplot
    from IPython.display import Latex
    from UliEngineering.Electronics.Resistors import normalize_numeric

Design calculations for the electronics of the master device.

Buck converter
--------------

LMR51420 is chosen as the regulator delivering *3.3V* to the FTDI device, resistor values were
selected based on what I had in inventory and resulted roughly in the expected voltage.

.. jupyter-execute::
    :hide-code:

    lmr51420_vref = '0.6V'
    lmr51420_rft = '47kΩ'
    lmr51420_rfb = '10.330kΩ'
    lmr51420_vout = (normalize_numeric(lmr51420_rft) / normalize_numeric(lmr51420_rfb)) * normalize_numeric(lmr51420_vref) + normalize_numeric(lmr51420_vref)

.. jupyter-execute::
    :hide-code:

    Latex(f'R_{{top}} = {lmr51420_rft}')

.. jupyter-execute::
    :hide-code:

    Latex(f'R_{{bot}} = {lmr51420_rfb}')

.. jupyter-execute::
    :hide-code:

    Latex(f'V_{{out}} = {lmr51420_vout:.03f}V')

Boost converter
---------------

TPS61085 is chosen as the boost converter providing high voltage to targets connected, resistors
again selected based on stock, a trim-pot is used to adjust the output voltage depending on the
final system voltage which is going to be something in between *6.5V* and *12V*.

.. jupyter-execute::
    :hide-code:

    tps61085_vin = '5V'
    tps61085_cout = '10uF'
    tps61085_inductor = '4.7uH'
    tps61085_iout = '500mA'
    tps61085_vs = '12V'

    tps61085_rcomp = (110 * normalize_numeric(tps61085_vin) * normalize_numeric(tps61085_vs) * normalize_numeric(tps61085_cout)) / (normalize_numeric(tps61085_inductor) / normalize_numeric(tps61085_iout))
    tps61085_ccomp = (normalize_numeric(tps61085_vs) * normalize_numeric(tps61085_cout)) / (7.5 * normalize_numeric(tps61085_iout) * tps61085_rcomp)

    tps61085_vref = '1.238V'
    tps61085_rft = '10kΩ'
    tps61085_rfb = '1kΩ'
    tps61085_trim = '2kΩ'

    tps61085_trim_values = np.linspace(0, normalize_numeric(tps61085_trim), num=30)
    tps61085_outputs = [normalize_numeric(tps61085_vref) * (1 + normalize_numeric(tps61085_rft) / (normalize_numeric(tps61085_rfb) + trim)) for trim in tps61085_trim_values]

.. jupyter-execute::
    :hide-code:

    Latex(f'R_{{comp}} = {tps61085_rcomp / 10**3:.03f}kΩ')

.. jupyter-execute::
    :hide-code:

    Latex(f'R_{{comp}} = {tps61085_ccomp * 10**9:.02f}nF')

.. jupyter-execute::
    :hide-code:

    Latex(f'R_{{top}} = {tps61085_rft}')

.. jupyter-execute::
    :hide-code:

    Latex(f'R_{{bot}} = {tps61085_rfb}')

.. jupyter-execute::
    :hide-code:

    Latex(f'R_{{bot}} = {tps61085_trim}')

Sweeping over potentiometer's range it yields the following output voltages.

.. jupyter-execute::
    :hide-code:

    pyplot.plot(tps61085_trim_values, tps61085_outputs)
    pyplot.xlabel(r"$R_{trim}$")
    pyplot.ylabel(r"$V_{out}$")
    pyplot.grid()


