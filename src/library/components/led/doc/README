 led component
================

This component is designed to drive a led plugged on low significant bit of a
register.

FPGA component
--------------

led component is composed of two 16 bits registers:

|   offset   | name        | description           |
|:-----------|:-----------:|:---------------------:|
|    0x00    | DATA        | data                  |
|    0x01    | ID          | component identifiant |

* DATA: memory register, LSB is plugged on led :

| 15 downto 1 |   0  |
|:-----------:|:----:|
|    void     | led  |

ARMAdeus Linux driver
---------------------

Load generic module and board module :
    # modprobe g_led
    # modprobe board_leds
    LED0: MAJOR: 252 MINOR: 0
    LED module LED0 insered

Then use major and minor number given to create the node :
mknod /dev/led0 c 252 0

To test the led, an C example program is available in drivers file.
Compile it :
    $ arm-linux-gcc testled.c -o testled

Then launch it on platform :

    # ./testled /dev/led0 
    Testing led driver
    Read 1
    Write 0
    Read 0
    Write 1
    Read 1
    Write 0
    Read 0

LED is blinking slowly.
