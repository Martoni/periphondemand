/*
 * Initialisation Driver for OpenCore 16550 serial IP
 *   loaded in FPGA of the Armadeus boards.
 *
 * (C) Copyright 2008 Armadeus Systems
 * Author: Julien Boibessot <julien.boibessot@armadeus.com>
 *
 * Inspired from Au1x00 Init from Pantelis Antoniou
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */

#include <linux/errno.h>
#include <linux/init.h>
#include <linux/interrupt.h>
#include <linux/ioport.h>
#include <linux/module.h>
#include <linux/serial_core.h>
#include <linux/serial_8250.h>
#include <linux/types.h>

#include <asm/io.h> // readb()

/* for debugging messages*/
#define LED_DEBUG

#undef PDEBUG
#ifdef LED_DEBUG
# ifdef __KERNEL__
    /* for kernel spage */
#   define PDEBUG(fmt,args...) printk(KERN_DEBUG "LED : " fmt, ##args)
# else
    /* for user space */
#   define PDEBUG(fmt,args...) printk(stderr, fmt, ##args)
# endif
#else
# define PDEBUG(fmt,args...) /* no debbuging message */
#endif



#define PORT(_base, _phys, _clock, _irq)   \
	{	                                   \
		.membase  = (void __iomem *)_base, \
		.mapbase  = _phys,                 \
		.irq      = _irq,                  \
		.uartclk  = _clock,                \
		.regshift = 1,                     \
		.iotype   = UPIO_MEM,              \
		.flags    = UPF_BOOT_AUTOCONF      \
	}


#define APF9328_FPGA_IRQ_MNGR (192)

/*$foreach:instance$*/
#define /*$instance_name$*/_INPUT_CLOCK   /*$generic:clock_speed$*/
#define /*$instance_name$*/_BASE  /*$registers_base_address:swb16$*/
#define /*$instance_name$*/_IRQ   IRQ_FPGA(/*$interrupt_number$*/)
/*$foreach:instance:end$*/

void plat_uart_release(struct device *dev)
{
    PDEBUG("device %s released\n",dev->bus_id);
}

/*$foreach:instance$*/
static struct plat_serial8250_port ocore_16550_uart/*$instance_num$*/_data[] = {
	PORT( APF9328_FPGA_VIRT+/*$instance_name$*/_BASE, 
		  APF9328_FPGA_PHYS+/*$instance_name$*/_BASE, 
		  /*$instance_name$*/_INPUT_CLOCK, 
		  /*$instance_name$*/_IRQ ),
	{ },
};
/*$foreach:instance:end$*/

/*$foreach:instance$*/
static struct platform_device ocore_16550_uart/*$instance_num$*/_device = {
	.name = "serial8250",
	.id=/*$instance_num$*/,
	.dev={
		.release=plat_uart_release,
		.platform_data = ocore_16550_uart/*$instance_num$*/_data,
	},
};
/*$foreach:instance:end$*/

static int __init ocore_16550_init(void)
{
    int ret = -ENODEV;
	u16 data;

/*$foreach:instance$*/
	/*************************************************/
	/* check if ID is correct for /*$instance_name$*/*/
	/*************************************************/
	data = ioread16((void*)ARMADEUS_FPGA_BASE_ADDR_VIRT+/*$registers_base_address:swb16$*/+/*$register:swb16:id:offset$*/*2);
	if(data != /*$generic:id$*/){
		printk(KERN_WARNING "For /*$instance_name$*/ id:/*$generic:id$*/ doesn't match with "
			   "id read %d,\n is device present ?\n",data);
		return -ENODEV;
	}
/*$foreach:instance:end$*/

/*$foreach:instance$*/  
	ret =	platform_device_register( &ocore_16550_uart/*$instance_num$*/_device ); 
	if(ret<0)return ret;
/*$foreach:instance:end$*/
    return ret;
}

static void __exit ocore_16550_exit(void)
{
/*$foreach:instance$*/	
	platform_device_unregister( &ocore_16550_uart/*$instance_num$*/_device );
/*$foreach:instance:end$*/
}

module_init(ocore_16550_init);
module_exit(ocore_16550_exit);

MODULE_AUTHOR("Julien Boibessot, <julien.boibessot@armadeus.com>");
MODULE_DESCRIPTION("8250 Linux layer registration module for 16550 OpenCore IP in Armadeus FPGA");
MODULE_LICENSE("GPL");
