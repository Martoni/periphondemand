sp_vision_configure component
=======================

This component is designed to configure a spartan6 with SelectMap Slave
protocol.

FPGA component
--------------

Output component is composed of four 16 bits registers:

|   offset   | name        | description                            |
|:-----------|:-----------:|:--------------------------------------:|
|    0x00    | ID          | component identifiant                  |
|    0x01    | CONFIG      | configuration for control signals      |
|    0x02    | STATUS      | control signals status                 |
|    0x03    | DATA        | bitstream 16bits data sent to spartan6 |

* ID : unique number to identify component.

* CONFIG : Drive control signals

| 15 downto 5 |  4  |  3   |  2  |    1    |   0   |
|:-----------:|:---:|:----:|:---:|:-------:|:-----:|
|     void    | CLK | void |CSI_n|PROGRAM_n|RDWR_n |

CLK flag is used to switch composant in configuration mode :
- When CLK=1, component is in idle mode, CCLK output drive general clock and
	all other output signals are High impedance.
- When CLK=0, the component is in fpga configuration mode.

* STATUS : read input signal from fpga

| 15 downto 3 |  2   | 1  |   0  |
|:-----------:|:----:|:--:|:----:|
|     void    |INIT_n|BUSY|RDWR_n|

* DATA : 16 bits data wrote for configuring FPGA.
When a data is written in this register, the value is placed on data output
port, and one cclk pulse is generated.

ARMadeus linux driver
---------------------

No ARMadeus linux driver for this moment.
