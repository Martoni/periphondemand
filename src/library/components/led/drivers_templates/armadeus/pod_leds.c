/*
 ***********************************************************************
 *
 * (c) Copyright 2008	Armadeus project
 * Fabien Marteau <fabien.marteau@armadeus.com>
 * Specific led driver for generic led driver
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

#ifdef CONFIG_MACH_APF9328 /* To remove when MX1 platform is merged */
# include "../arch/arm/plat-mxc/include/mach/fpga.h"
# include <mach/irqs.h>
#else
# include <mach/fpga.h>
#endif

#include "../../virtual_components/led/led.h"

/*$foreach:instance$*/
static struct resource led/*$instance_num$*/_resources[] = {
	[0] = {
		.start	= ARMADEUS_FPGA_BASE_ADDR + /*$registers_base_address:swb16$*/,
		.end	= ARMADEUS_FPGA_BASE_ADDR + /*$registers_base_address:swb16$*/ + 3,
		.flags	= IORESOURCE_MEM,
	},
};

static struct plat_led_port plat_led/*$instance_num$*/_data = {
	.name		= "/*$instance_name$*/",
	.num		= /*$instance_num$*/,
	.idnum		= /*$generic:id$*/,
	.idoffset	=  /*$register:swb16:id:offset$*/ * (16 /8)
};
/*$foreach:instance:end$*/

void plat_led_release(struct device *dev)
{
	dev_dbg(dev, "released\n");
}

static struct platform_device plat_led_devices[] = {
/*$foreach:instance$*/
    {
	    .name	= "led",
	    .id	= /*$instance_num$*/,
	    .dev	= {
	    	.release	= plat_led_release,
	    	.platform_data	= &plat_led/*$instance_num$*/_data
	    },
	    .num_resources	= ARRAY_SIZE(led/*$instance_num$*/_resources),
	    .resource	= led/*$instance_num$*/_resources,
    }
/*$foreach:instance:end$*/
};

static int __init sled_init(void)
{
	return platform_device_register(plat_led_devices);
}

static void __exit sled_exit(void)
{
	platform_device_unregister(plat_led_devices);
}

module_init(sled_init);
module_exit(sled_exit);

MODULE_AUTHOR("Fabien Marteau <fabien.marteau@armadeus.com>");
MODULE_DESCRIPTION("Driver to blink blink some leds");
MODULE_LICENSE("GPL");

