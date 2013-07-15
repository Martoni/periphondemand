Wishbone interface for GPIO featuring interrupts
=======================

This component is designed to drive some inputs/outputs and generate an interrupt signal on
input.

FPGA component
--------------

Use the following registers:

| offset | name                     | description                |
|:-------|:------------------------:|:--------------------------:|
| 0x00   | ID                       | Wishbone identifier        |
| 0x01   | GPIO_CONFIG              | Input/output configuration |
| 0x02   | GPIO_VALUE               | Input/output value of gpio |
| 0x03   | GPIO_ENABLE_INTERRUPT    | Enable interrupt on GPIOs  |
| 0x04   | GPIO_INTERRUPT_STATUS    | Interrupt status register  |
| 0x05   | GPIO_INTERRUPT_EDGE_TYPE | Edge type interrupt        |
| 0x06   | void                     | read 0x00                  |
| 0x07   | void                     | read 0x00                  |

* GPIO_CONFIG
    Set the bit corresponding to the desired GPIO to put it in input. Reset it for output.
* GPIO_VALUE
    This register contains the value of each GPIO. Read the input values or write output values.
* GPIO_ENABLE_INTERRUPT
    Set the bit to activate the corresponding GPIO interrupt.
* GPIO_INTERRUPT_STATUS
    If an interrupt is triggered on GPIO, the corresponding bit of this register is triggered.
    Write a logic '1' on this bit to acknowledge it.
* GPIO_INTERRUPT_EDGE_TYPE
    This register is used to define which edge trigger the interruption:
        - Set the corresponding bit to the desired GPIO define it edge as rising edge
        - Reset the corresponding bit to the desired GPIO define it edge as falling edge

ARMadeus linux driver
---------------------

    * Load these modules:

        # modprobe pod_gpio_platform
        # modprobe pod_gpio

    * Check wich GPIO number is used by the driver.
    * Export the GPIO number:
        # echo [my_gpio_number] > /sys/class/gpio/export
    * Configure your GPIO:
        - Set the direction by writin "in" or "out" in /sys/class/gpio/gpio[my_gpio_number]/direction
            echo [in_or_out] > /sys/class/gpio/gpio[my_gpio_number]/direction
        - You can configure an interruption if the modules of the component irq_mng is loaded.

For further informations about gpiolib :

http://www.armadeus.com/wiki/index.php?title=GPIOlib
http://www.avrfreaks.net/wiki/index.php/Documentation:Linux/GPIO
