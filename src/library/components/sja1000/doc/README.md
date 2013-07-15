SJA1000 CAN Controller interface component
=======================

This component is designed to drive a SJA1000 CAN controller.

FPGA component
--------------

Output component is used for read/write in the SJA1000 registers.
Please see the technical datasheet of the SJA1000 for registers details.

You must specify the generic "gpiopin", otherwise the Linux driver doesn't compile!

note: For ARMadeus APF27, gpiopin value must be "173" if you have soldered the interruption of the SJA1000
on "SW1" switch. For ARMadeus APF51, gpiopin value must be "3" if you have soldered the interruption of the SJA1000
on "IMX Switch".

Warning: Please ensure that your configuration respect the timing conditions of the SJA1000.
You must be sure that duration of a low state on the chipselect of the Wrapper will never be
less than 100ns (a little bit more is advised) and after a request of the SJA1000, you must be sure that
the following request will be in 15ns minimum.

Exemple for an APF27:

in Uboot on ARMadeus Boards

Configuration of the chip select duration (writing 0x00002000 in the register
 CSCR5U at address 0xD8002050):
mw D8002050 00002000

Configuration of the next request time (writing 0x00000d21 in the register
 CSCR5L at address 0xD8002054):
mw D8002054 00000d21

ARMadeus linux driver
---------------------

You must load these modules :

> modprobe sja1000_apf
> modprobe sja1000_platform

These modules can be required by some applications :

> modprobe can
> modprobe can_bcm
> modprobe can_dev
> modprobe can_raw

Use this command to set the bitrate :

> ip link set can0 up type can bitrate 125000

Verify that your interface is correctly mounted :

> ifconfig can0
