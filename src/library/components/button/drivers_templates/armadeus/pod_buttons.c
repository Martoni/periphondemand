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
#include <linux/init.h>
#include <linux/module.h>
#include <linux/platform_device.h>

#include <mach/hardware.h>
#ifdef CONFIG_MACH_APF9328 /* To remove when MX1 platform is merged */
# include "../arch/arm/plat-mxc/include/mach/fpga.h"
# include <mach/irqs.h>
#else
# include <mach/fpga.h>
#endif

#include "../../virtual_components/button/button.h"

/*$foreach:instance$*/
#define /*$instance_name$*/_IRQ   IRQ_FPGA(/*$interrupt_number$*/)
/*$foreach:instance:end$*/


/*$foreach:instance$*/
static struct resource button/*$instance_num$*/_resources[] = {
	[0] = {
		.start	= ARMADEUS_FPGA_BASE_ADDR + /*$registers_base_address:swb16$*/,
		.end	= ARMADEUS_FPGA_BASE_ADDR + /*$registers_base_address:swb16$*/ + 3,
		.flags	= IORESOURCE_MEM,
	},
	[1] = {
		.start	= /*$instance_name$*/_IRQ,
		.end	= /*$instance_name$*/_IRQ,
		.flags	= IORESOURCE_IRQ,
	}
};

static struct plat_button_port plat_button/*$instance_num$*/_data = {
	.name		= "/*$instance_name$*/",
	.num		= /*$instance_num$*/,
	.idnum		= /*$generic:id$*/,
	.idoffset	= /*$register:swb16:id:offset$*/ * (/*$register:swb16:id:size$*/ /8)
};
/*$foreach:instance:end$*/

void plat_button_release(struct device *dev)
{
	dev_dbg(dev, "released\n");
}

static struct platform_device plat_button_device[] = {
/*$foreach:instance$*/
    {
	    .name		= "button",
	    .id		= /*$instance_num$*/,
	    .dev		= {
	    	.release	= plat_button_release,
	    	.platform_data	= &plat_button/*$instance_num$*/_data
	    },
	    .num_resources	= ARRAY_SIZE(button/*$instance_num$*/_resources),
	    .resource	= button/*$instance_num$*/_resources,
    }
/*$foreach:instance:end$*/
};

static int __init board_button_init(void)
{
	return platform_device_register(plat_button_device);
}

static void __exit board_button_exit(void)
{
	platform_device_unregister(plat_button_device);
}

module_init(board_button_init);
module_exit(board_button_exit);

MODULE_AUTHOR("Julien Boibessot, <julien.boibessot@armadeus.com>");
MODULE_DESCRIPTION("POD specific button driver");
MODULE_LICENSE("GPL");

