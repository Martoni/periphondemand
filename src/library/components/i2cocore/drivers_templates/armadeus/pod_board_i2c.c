/*
 * board_i2c.c
 * structures declaration for i2c ocores devices
 * Fabien Marteau <fabien.marteau@armadeus.com>
 *
 * This file is licensed under the terms of the GNU General Public License
 * version 2.  This program is licensed "as is" without any warranty of any
 * kind, whether express or implied.
*/

#include <linux/version.h>
#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,20)
#include <linux/config.h>
#endif

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/errno.h>
#include <linux/platform_device.h>
#include <linux/i2c.h>
#include <linux/interrupt.h>
#include <linux/wait.h>
#include <asm/io.h>
#ifndef CONFIG_MACH_APF9328 /* To remove when MX1 platform is merged */
#include <mach/fpga.h>
#endif

#include "i2c-ocores-pod.h"

#define APF9328_FPGA_IRQ_MNGR (192)
#define CLOCK_FPGA     (/*$main_clock$*/)

/*$foreach:instance$*/
#define /*$instance_name$*/_BASEADDR (ARMADEUS_FPGA_BASE_ADDR + /*$registers_base_address:swb16$*/)
#define /*$instance_name$*/_IRQ      (IRQ_FPGA(/*$interrupt_number$*/))
/*$foreach:instance:end$*/

void board_i2c_release(struct device *dev)
{
    /* release */
}

/*$foreach:instance$*/
static struct resource ocores_/*$instance_name$*/_resources[] = {
	[0] = {
		.start	= /*$instance_name$*/_BASEADDR,
		.end	= /*$instance_name$*/_BASEADDR + 16,
		.flags	= IORESOURCE_MEM,
	},
	[1] = {
		.start	= /*$instance_name$*/_IRQ,
		.end	= /*$instance_name$*/_IRQ,
		.flags	= IORESOURCE_IRQ,
	},
};

static struct ocores_i2c_platform_data /*$instance_name$*/_i2c_data = {
	.regstep	= 2,		/* two bytes between registers */
	.clock_khz	= CLOCK_FPGA,	/* input clock of 96MHz */
	.id         = /*$generic:id$*/,   /* component identification number*/
	.idoffset   = /*$register:swb16:id:offset$*/*(16/8)/*id address offset*/
};

static struct platform_device /*$instance_name$*/_i2c = {
	.name			= "ocores-i2c-pod",
    .id             = /*$instance_num$*/,
	.dev = {
        .release        = board_i2c_release,
		.platform_data	= &/*$instance_name$*/_i2c_data,
	},
	.num_resources		= ARRAY_SIZE(ocores_/*$instance_name$*/_resources),
	.resource = ocores_/*$instance_name$*/_resources,
};
/*$foreach:instance:end$*/

static int __init board_i2c_init(void)
{
	int retval=-ENODEV;
/*$foreach:instance$*/
	retval = platform_device_register(&/*$instance_name$*/_i2c);
	if(retval<0){
		printk("Error registering /*$instance_name$*/_i2c\n");
		return retval;
	}
/*$foreach:instance:end$*/
	return retval;
}

static void __exit board_i2c_exit(void)
{
/*$foreach:instance$*/
	platform_device_unregister(&/*$instance_name$*/_i2c);
/*$foreach:instance:end$*/
}

module_init(board_i2c_init);
module_exit(board_i2c_exit);

MODULE_AUTHOR("Fabien Marteau <fabien.marteau@armadeus.com>");
MODULE_DESCRIPTION("Board specific i2c-bus driver for pod");
MODULE_LICENSE("GPL");

