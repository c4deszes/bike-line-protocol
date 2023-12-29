Physical layers
===============

The protocol isn't specific to a particular physical layer but there are common settings under which
it might be used.

USART w/ LIN PHY
----------------

Most common way by far, using an USART peripheral and a LIN transciever the communication is done
over a single wire, in this configuration multiple devices can connect to a common line.

Common settings are:

* Baudrate 9600-19200, but might be increased if the bus characteristics allow it
* 8 data bits, No parity, 1 stop bit
