simplegpio component
====================

This component is designed to use IO fpga pin as GPIO

FPGA Component
--------------

Output component is composed of four 16 bits registers:

|   offset   | name        | description                            |
|:-----------|:-----------:|:--------------------------------------:|
|    0x00    | DATA        | Data read/write on port                |
|    0x01    | CTRL        | Control register                       |
|    0x02    | ID          | Component identifiant                  |
|    0x03    |  -          | Void, 0-read register                  |

* DATA: data register, if pin is output each bit written select the output
        value. If pin is input, each bit read represent pin value.
* CTRL: Control register, for each bit : 0->input, 1->output.

* ID : unique number to identify component.

ARMadeus linux driver
---------------------

No ARMadeus linux driver for this moment.
