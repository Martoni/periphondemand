Wishbone interface for HMS Anybus modules
=======================

This component is designed to drive a HMS Anybus Module

FPGA component
--------------

Output component is used for read/write in HMS Anybus Module
Please see the technical datasheet of the HMS Anybus for registers details.

| offset | name        | description                    |
|:-------|:-----------:|:------------------------------:|
|  0x00  | ID          | Wishbone identifier            |
|  0x01  | CONTROL_REG | Control and status             |
|  0x02  | ADDRESS_REG | address of the Anybus register |
|  0x03  | DATA_REG    | Data register                  |

* CONTROL_REG
    - bit 0: if set, this bit indicate that a transmission error has occured. This bit will be
      cleared when you read the CONTROL_REG register.
    - bit 1: Set this bit to transmit data to the Anybus module.
    - bit 2: Set this bit to receive data from the Anybus module.
    - bit 3..5: This value indicate the number of Wishbone clock cycles to wait while an access
      to the modules.
* ADDRESS_REG
    This register contain the address to read/write by the component.
* DATA_REG
    This register contain the data read/to write by the component in the Anybus registers.

Please don't forget to set generic gpio_reset and gpio_irq

Warning: You must first configure the number of Wishbone clock cycles to wait before an Anybus access
with your application: It is recommended to not be lower than 25ns.
Exemple: if your Wishbone bus is clocked at 100Mhz
25ns/(1 / 100Mhz) = 2.5 ==> CONTROL_REG[3..5] = 3

ARMadeus linux driver
---------------------

Load these Linux modules:
    modprobe anybus_interface_platform
    modprobe anybus_interface

Then, you can mmap the file /dev/anybus_interface to access to the hms_anybus_interface component
registers in :
    * Write:
        - Write address in the ADDRESS_REG register
        - Write data in the DATA_REG register
        - Set the transmit bit and specify the number of Wishbone clock cycle in the CONTROL_REG register
        - Verify if transmission_error bit is low in CONTROL_REG register.
    * Read
        - Write address in the ADDRESS_REG register
        - Set the receive bit and specify the number of Wishbone clock cycle in the CONTROL_REG register
        - Read data in the DATA_REG register
        - Verify if transmission_error bit is low in CONTROL_REG register.
