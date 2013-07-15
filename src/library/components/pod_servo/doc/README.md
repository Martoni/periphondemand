POD_SERVO
=======================

Generate a PWM output to drive servo.

FPGA component
--------------

This component generate a pwm signal to set the angle of a servo.
You must set the value of the angle proportionnally between a range of 0 to 999
corresponding to a pulse of 1ms to 2 ms. This value is accessible by reading or
writing in the 1rst register. The 0 register is used for the component generic
id.

ARMadeus linux driver
---------------------

Not provided yet. Please use fpgaregs or mmap to read/write in the pod_servo
registers.
