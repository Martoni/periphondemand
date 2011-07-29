/*
 * Specific input driver for generic input driver
 *
 * (c) Copyright 2008    Armadeus project
 * Fabien Marteau <fabien.marteau@armadeus.com>
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

#include <linux/init.h>
#include <linux/module.h>
#include <linux/platform_device.h>
#include <mach/hardware.h>
#ifndef CONFIG_MACH_APF9328 /* To remove when MX1 platform is merged */
#include <mach/fpga.h>
#endif

#include "input.h"

/*$foreach:instance$*/
#define /*$instance_name$*/_IRQ   IRQ_FPGA(/*$interrupt_number$*/)
/*$foreach:instance:end$*/

/*$foreach:instance$*/
static struct plat_input_port plat_input/*$instance_num$*/_data={
	.name = "/*$instance_name$*/",
	.interrupt_number=/*$instance_name$*/_IRQ,
	.num=/*$instance_num$*/,
	.membase = (void *)(ARMADEUS_FPGA_BASE_ADDR +
						/*$registers_base_address:wbs$*/),
	.idnum=/*$generic:id$*/,
	.idoffset=/*$register:wbs:id:offset$*/ * (/*$register:wbs:id:size$*/ /8)
};
/*$foreach:instance:end$*/

/*$foreach:instance$*/
static struct platform_device plat_input/*$instance_num$*/_device={
	.name = "input",
	.id=/*$instance_num$*/,
	.dev={
		.platform_data = &plat_input/*$instance_num$*/_data
	},
};
/*$foreach:instance:end$*/


static int __init board_input_init(void)
{
    int ret = -1;
/*$foreach:instance$*/
	ret = platform_device_register(&plat_input/*$instance_num$*/_device);
	if(ret<0)return ret;
/*$foreach:instance:end$*/
    return ret;
}

static void __exit board_input_exit(void)
{
/*$foreach:instance$*/
	platform_device_unregister(&plat_input/*$instance_num$*/_device);
/*$foreach:instance:end$*/
}

module_init(board_input_init);
module_exit(board_input_exit);

MODULE_AUTHOR("Fabien Marteau <fabien.marteau@armadeus.com>");
MODULE_DESCRIPTION("Board specific input driver");
MODULE_LICENSE("GPL");

