/*
 * Initialisation Driver for OpenCore 16750 serial IP
 *   loaded in FPGA of the Armadeus boards.
 *
 * (C) Copyright 2008, 2009, 2010, 2011 Armadeus Systems
 * Author: Julien Boibessot <julien.boibessot@armadeus.com>
 *
 * Inspired from Au1x00 Init from Pantelis Antoniou
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */

#include <linux/version.h>
#include <linux/module.h>
#include <linux/serial_8250.h>

#include <asm/io.h>
#ifndef CONFIG_MACH_APF9328 /* To remove when MX1 platform is merged */
#include <mach/fpga.h>
#endif

/*$foreach:instance$*/
#define /*$instance_name$*/_INPUT_CLOCK   /*$generic:clock_speed$*/
#define /*$instance_name$*/_BASE  /*$registers_base_address:swb16$*/
#define /*$instance_name$*/_IRQ   IRQ_FPGA(/*$interrupt_number$*/)
/*$foreach:instance:end$*/

void plat_uart_release(struct device *dev)
{
#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,30)
	pr_debug("device %s released\n", dev->bus_id);
#else
	pr_debug("device %s released\n", dev->init_name);
#endif
}

/*$foreach:instance$*/
static struct plat_serial8250_port ocore_16750_uart/*$instance_num$*/_data[] = {
	{
		.mapbase  = ARMADEUS_FPGA_BASE_ADDR + /*$instance_name$*/_BASE,
		.irq      = /*$instance_name$*/_IRQ,
		.uartclk  = /*$instance_name$*/_INPUT_CLOCK,
		.regshift = 1,
		.iotype   = UPIO_MEM,
		.flags    = UPF_BOOT_AUTOCONF
	},
	{}
};
/*$foreach:instance:end$*/

/*$foreach:instance$*/
static struct platform_device ocore_16750_uart/*$instance_num$*/_device = {
	.name	= "serial8250",
	.id	= /*$instance_num$*/,
	.dev	= {
		.release	= plat_uart_release,
		.platform_data	= ocore_16750_uart/*$instance_num$*/_data,
	},
};
/*$foreach:instance:end$*/

static struct platform_device* ocore_16750_uart_devices[] = {
/*$foreach:instance$*/
	&ocore_16750_uart/*$instance_num$*/_device,
/*$foreach:instance:end$*/
};

static int __init ocore_16750_init(void)
{
	u16 id;

/*$foreach:instance$*/
	ocore_16750_uart/*$instance_num$*/_data[0].membase =
		ioremap(ocore_16750_uart/*$instance_num$*/_data[0].mapbase, /*$instance_name$*/_BASE);
	if (!ocore_16750_uart0_data[0].membase) {
		printk(KERN_ERR "%s: ioremap failed\n", __func__);
		return -ENOMEM;
	}

	/* check if ID is correct for /*$instance_name$*/ */
	id = readw(ocore_16750_uart/*$instance_num$*/_data[0].membase + /*$register:swb16:id:offset$*/*2);
	if (id != /*$generic:id$*/) {
		printk(KERN_WARNING "For /*$instance_name$*/ id:/*$generic:id$*/ doesn't match with "
			   "id read %d,\n is device present ?\n", id);
		return -ENODEV;
	}
/*$foreach:instance:end$*/

	return platform_add_devices(ocore_16750_uart_devices, ARRAY_SIZE(ocore_16750_uart_devices));
}

static void __exit ocore_16750_exit(void)
{
/*$foreach:instance$*/
	platform_device_unregister(&ocore_16750_uart/*$instance_num$*/_device);
/*$foreach:instance:end$*/
}

module_init(ocore_16750_init);
module_exit(ocore_16750_exit);

MODULE_AUTHOR("Julien Boibessot, <julien.boibessot@armadeus.com>");
MODULE_DESCRIPTION("8250 Linux layer registration module for 16750 OpenCore IP in Armadeus FPGA");
MODULE_LICENSE("GPL");
