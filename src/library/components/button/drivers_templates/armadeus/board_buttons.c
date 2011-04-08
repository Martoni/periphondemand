/*
 ***********************************************************************
 *
 * (c) Copyright 2008    Armadeus project
 * Fabien Marteau <fabien.marteau@armadeus.com>
 * Specific button driver for generic button driver
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
 **********************************************************************
 */

#include <linux/version.h>
#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,20)
#include <linux/config.h>
#endif

/* form module/drivers */
#include <linux/init.h>
#include <linux/module.h>

/* for platform device */
#include <linux/platform_device.h>
#include <mach/hardware.h>
#ifdef CONFIG_MACH_APF27 /* To remove when MX1 platform merged */
#include <mach/fpga.h>
#endif


#include "button.h"

/*$foreach:instance$*/
#define /*$instance_name$*/_IRQ   IRQ_FPGA(/*$interrupt_number$*/)
/*$foreach:instance:end$*/

/*$foreach:instance$*/
static struct plat_button_port plat_button/*$instance_num$*/_data={
	.name = "/*$instance_name$*/",
	.interrupt_number=/*$instance_name$*/_IRQ,
	.num=/*$instance_num$*/,
	.membase = (void *)(ARMADEUS_FPGA_BASE_ADDR_VIRT +
						/*$registers_base_address:swb16$*/),
	.idnum=/*$generic:id$*/,
	.idoffset=/*$register:swb16:id:offset$*/ * (/*$register:swb16:id:size$*/ /8)
};
/*$foreach:instance:end$*/

/*$foreach:instance$*/
static struct platform_device plat_button/*$instance_num$*/_device={
	.name = "button",
	.id=/*$instance_num$*/,
	.dev={
		.platform_data = &plat_button/*$instance_num$*/_data
	},
};
/*$foreach:instance:end$*/

static int __init board_button_init(void)
{
    int ret = -1;
/*$foreach:instance$*/
	ret = platform_device_register(&plat_button/*$instance_num$*/_device);
	if(ret<0)return ret;
/*$foreach:instance:end$*/
    return ret;
}

static void __exit board_button_exit(void)
{
/*$foreach:instance$*/
	platform_device_unregister(&plat_button/*$instance_num$*/_device);
/*$foreach:instance:end$*/
}

module_init(board_button_init);
module_exit(board_button_exit);

MODULE_AUTHOR("Fabien Marteau <fabien.marteau@armadeus.com>");
MODULE_DESCRIPTION("Board specific button driver");
MODULE_LICENSE("GPL");

