/*
 * Platform data for IRQ manager generic driver
 *
 * (c) Copyright 2011    The Armadeus Project - ARMadeus Systems
 * Author: Julien Boibessot <julien.boibessot@armadeus.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 */

#include <linux/version.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/interrupt.h>
#include <linux/irq.h>

#include <mach/hardware.h>
#ifndef CONFIG_MACH_APF9328 /* To remove when MX1 platform is merged */
#include <mach/fpga.h>
#endif

#include "../../virtual_components/irq_mngr/irq_mng.h"

/*$foreach:instance$*/
static struct resource /*$instance_name$*/_resources[] = {
	[0] = {
		.start	= ARMADEUS_FPGA_BASE_ADDR + /*$registers_base_address:swb16$*/,
		.end	= ARMADEUS_FPGA_BASE_ADDR + /*$registers_base_address:swb16$*/ + 0x7,
		.flags	= IORESOURCE_MEM,
	},
	[1] = {
		.start	= ARMADEUS_FPGA_IRQ,
		.end	= ARMADEUS_FPGA_IRQ,
		.flags	= IORESOURCE_IRQ,
	}
};

static struct ocore_irq_mng_pdata /*$instance_name$*/_data = {
	.num		= /*$instance_num$*/,
	.idnum		= /*$generic:id$*/,
	.idoffset	= (/*$register:swb16:id:offset$*/ * (/*$register:swb16:id:size$*/ /8)),
};

static void /*$instance_name$*/_release(struct device *dev)
{
	dev_dbg(dev, "released\n");
}

static struct platform_device /*$instance_name$*/_device = {
	.name		= "ocore_irq_mng",
	.id		= 0,
	.dev		= {
		.release	= /*$instance_name$*/_release,
		.platform_data	= &/*$instance_name$*/_data
	},
	.num_resources	= ARRAY_SIZE(/*$instance_name$*/_resources),
	.resource	= /*$instance_name$*/_resources,
};
/*$foreach:instance:end$*/
#ifdef CONFIG_MACH_APF27
static int fpga_pins[] = {
	(APF27_FPGA_INT_PIN | GPIO_IN | GPIO_GPIO),
};
#endif

static int __init board_irq_mng_init(void)
{
	int ret;

#ifdef CONFIG_MACH_APF27
	ret = mxc_gpio_setup_multiple_pins(fpga_pins, ARRAY_SIZE(fpga_pins), "FPGA");
	if (ret)
		return -EINVAL;
#endif
#if LINUX_VERSION_CODE > KERNEL_VERSION(2,6,39)
    irq_set_irq_type(ARMADEUS_FPGA_IRQ, IRQ_TYPE_EDGE_RISING);
#else
	set_irq_type(ARMADEUS_FPGA_IRQ, IRQ_TYPE_EDGE_RISING);
#endif
/*$foreach:instance$*/
	ret = platform_device_register(&/*$instance_name$*/_device);
/*$foreach:instance:end$*/
	return ret;
}

static void __exit board_irq_mng_exit(void)
{
/*$foreach:instance$*/
	platform_device_unregister(&/*$instance_name$*/_device);
/*$foreach:instance:end$*/
#ifdef CONFIG_MACH_APF27
	mxc_gpio_release_multiple_pins(fpga_pins, ARRAY_SIZE(fpga_pins));
#endif
}

module_init(board_irq_mng_init);
module_exit(board_irq_mng_exit);

MODULE_AUTHOR("Julien Boibessot <julien.boibessot@armadeus.com>");
MODULE_DESCRIPTION("Platform data for IRQ manager IP driver");
MODULE_LICENSE("GPL");
