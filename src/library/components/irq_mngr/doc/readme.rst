Irq_mngr
--------
This component is designed to managed interrupts from others Virtual component
to the processor.

**FPGA Component**

Irq_mngr component is composed of four 16bits registers:

+------------+-------------+---------------------------------+
|   offset   | name        | description                     |
+============+=============+=================================+
|    0x00    | MASK        | irq mask register               |
+------------+-------------+---------------------------------+
|    0x01    | PENDING     | pending register                |
+------------+-------------+---------------------------------+
|    0x02    | ID          | Identification register         |
+------------+-------------+---------------------------------+
|    0x03    | void        | read 0                          |
+------------+-------------+---------------------------------+

* **MASK**: Write 1 on corresponding register bit to enable interrupt.
* **PENDING**: bit flag is 1 if irq pending, write 1 to reset flag
* **ID**: identification register

**ARMadeus linux driver:**

irq manager is used with other module, then before use its, unsure you have
loaded the manager :

``$ modprobe irq_ocore``

Then load pod_irq module :

``$ modprobe pod_irq_mng``

