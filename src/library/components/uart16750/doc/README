UART 16750
==========

This component come from opencores (http://www.opencores.org/?do=project&who=uart16750).

FPGA Component
--------------

The documentation of UART 16750 can be found on TI website :
http://focus.ti.com/general/docs/lit/getliterature.tsp?genericPartNumber=tl16c750&fileType=pdf

ARMadeus linux driver
---------------------

To use uart in linux (armadeus) the generic serial driver 8250 must be use. Then before compiling the kernel, select it in make linux26-menuconfig :
> device drivers -> Character devices -> Serial drivers ->  <M> 8250/16750 and compatible serial support

Once system compiled and flashed on board, mount module in this order :

> modprobe irq_ocore
> modprobe 8250
> modprobe 16750_ocore

A message will appear with ttyS* used. Typicaly when one uart it's ttyS0.
