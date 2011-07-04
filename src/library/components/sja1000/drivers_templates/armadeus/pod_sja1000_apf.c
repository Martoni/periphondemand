/*
 * ARMadeus platform data/device for SJA1000
 *
 * (C) Copyright 2011 - Armadeus Systems <support@armadeus.com>
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
#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,20)
#include <linux/config.h>
#endif

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/interrupt.h>
#include <linux/netdevice.h>
#include <linux/delay.h>
#include <linux/pci.h>
#include <linux/platform_device.h>
#include <linux/irq.h>
#include <linux/can/dev.h>
#include <linux/can/platform/sja1000.h>
#include <linux/io.h>
#include <linux/gpio.h>

#ifndef CONFIG_MACH_APF9328 /* To remove when MX1 platform is merged */
#include <mach/fpga.h>
#endif

/*$foreach:instance$*/
#define /*$instance_name$*/_BASE   /*$registers_base_address:swb16$*/
#define /*$instance_name$*/_IRQ_PIN /*$generic:gpiopin$*/
/*$foreach:instance:end$*/

#define DRV_NAME "sja1000_platform"

MODULE_AUTHOR("Kevin JOLY joly.kevin25@gmail.com");
MODULE_DESCRIPTION("SJA1000 device on ARMadeus APF Boards");
MODULE_LICENSE("GPL");

/*$foreach:instance$*/
static struct resource /*$instance_name$*/_resources[] = {
	[0] = {
		.start = ARMADEUS_FPGA_BASE_ADDR + /*$instance_name$*/_BASE,
		.end = ARMADEUS_FPGA_BASE_ADDR + /*$instance_name$*/_BASE + 0x1ff,
		.flags = IORESOURCE_MEM | IORESOURCE_MEM_16BIT,
	},
	[1] = {
		.start = gpio_to_irq(/*$instance_name$*/_IRQ_PIN),
		.end = gpio_to_irq(/*$instance_name$*/_IRQ_PIN),
		.flags = IORESOURCE_IRQ | IORESOURCE_IRQ_LOWEDGE,
	},
};

static struct sja1000_platform_data /*$instance_name$*/_pdata = {
	.osc_freq = 24000000,
	.ocr = OCR_MODE_NORMAL | OCR_TX0_PULLDOWN | OCR_TX1_PULLDOWN,
	.cdr = CDR_PELICAN | CDR_CBP,
};

void /*$instance_name$*/_release(struct device *dev)
{
	dev_dbg(dev, "released\n");
}

static struct platform_device /*$instance_name$*/_pdev = {
	.name = DRV_NAME,
	.id = /*$instance_num$*/,
	.dev = {
		.platform_data = &/*$instance_name$*/_pdata,
		.release = /*$instance_name$*/_release,
	},
	.num_resources = ARRAY_SIZE(/*$instance_name$*/_resources),
	.resource = /*$instance_name$*/_resources,
};

/*$foreach:instance:end$*/

static int __init sja1000_apf27dev_init(void)
{
	int ret;
/*$foreach:instance$*/
	ret = platform_device_register(&/*$instance_name$*/_pdev);

	if (ret < 0)
		printk(KERN_ERR "Error: Can't init device /*$instance_name$*/");
/*$foreach:instance:end$*/
	return ret;
}

static void __exit sja1000_apf27dev_exit(void)
{
/*$foreach:instance$*/
	platform_device_unregister(&/*$instance_name$*/_pdev);
/*$foreach:instance:end$*/
}

module_init(sja1000_apf27dev_init);
module_exit(sja1000_apf27dev_exit);
