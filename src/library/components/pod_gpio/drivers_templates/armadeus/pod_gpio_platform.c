/*
 * ARMadeus platform data/device for the POD component pod_gpio
 *
 * (C) Copyright 2011 - Armadeus Systems <support@armadeus.com>
 * Author: Kevin JOLY joly.kevin25@gmail.com
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

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/platform_device.h>
#ifndef CONFIG_MACH_APF9328 /* To remove when MX1 platform is merged */
#include <mach/fpga.h>
#endif

#include "../../virtual_components/pod_gpio/pod_gpio.h"

/*$foreach:instance$*/
#define /*$instance_name$*/_BASE /*$registers_base_address:swb16$*/
/*$foreach:instance:end$*/

/*$foreach:instance$*/
static struct resource /*$instance_name$*/_resources[] = {
	[0] = {
		.start = ARMADEUS_FPGA_BASE_ADDR + /*$instance_name$*/_BASE,
		.end = ARMADEUS_FPGA_BASE_ADDR + /*$instance_name$*/_BASE + 0x07,
		.flags = IORESOURCE_MEM | IORESOURCE_MEM_16BIT,
	},
	[1] = {
		.start	= IRQ_FPGA(/*$interrupt_number$*/),
		.end	= IRQ_FPGA(/*$interrupt_number$*/),
		.flags	= IORESOURCE_IRQ,
	}
};

void /*$instance_name$*/_release(struct device *dev)
{
	dev_dbg(dev, "released\n");
}

static struct platform_device /*$instance_name$*/_pdev = {
	.name = pod_gpio_DRIVER_NAME,
	.id = /*$generic:id$*/,
	.dev = {
		.release = /*$instance_name$*/_release,
	},
	.num_resources = ARRAY_SIZE(/*$instance_name$*/_resources),
	.resource = /*$instance_name$*/_resources,
};
/*$foreach:instance:end$*/

static int __init pod_gpio_platform_init(void)
{
	int ret;

/*$foreach:instance$*/
	ret = platform_device_register(&/*$instance_name$*/_pdev);
	if (ret < 0)
		printk(KERN_ERR "Error: Can't init device /*$instance_name$*/\n");
/*$foreach:instance:end$*/

	return ret;
}
module_init(pod_gpio_platform_init);

static void __exit pod_gpio_platform_exit(void)
{
/*$foreach:instance$*/
	platform_device_unregister(&/*$instance_name$*/_pdev);
/*$foreach:instance:end$*/
}
module_exit(pod_gpio_platform_exit);

MODULE_AUTHOR("Kevin Joly <joly.kevin25@gmail.com>");
MODULE_DESCRIPTION("GPIO driver for pod_gpio component of POD");
MODULE_LICENSE("GPL v2");
