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

# include <mach/fpga.h>

#include "../../virtual_components/sploader/spartan_loadsecond.h"

/*$foreach:instance$*/
static struct resource sploader/*$instance_num$*/_resources[] = {
	[0] = {
		.start	= ARMADEUS_FPGA_BASE_ADDR, + /*$registers_base_address:swb16$*/,
		.end	= ARMADEUS_FPGA_BASE_ADDR + /*$registers_base_address:swb16$*/ + 3,
		.flags	= IORESOURCE_MEM,
	},
};

static Xilinx_desc plat_sploader/*$instance_num$*/_data = {
	.family = Xilinx_Spartan6,
	.iface = slave_parallel,
	.size = (11875104l / 8),    //XILINX_XC6SLX45_SIZE,
	.fpga_offset = 0xD6000000l,
	.ip_id = 0, // l'id du composant == idnum
	.cookie = 1,
	.name		= "/*$instance_name$*/",
	.num		= /*$instance_num$*/,
	.idnum		= /*$generic:id$*/,
	.idoffset	=  /*$register:swb16:id:offset$*/ * (16 /8) // pos de l'id dans le composant
};
/*$foreach:instance:end$*/

void plat_sploader_release(struct device *dev)
{
	dev_dbg(dev, "released\n");
}

static struct platform_device plat_sploader_devices[] = {
/*$foreach:instance$*/
    {
	    .name	= "sploader",
	    .id	= /*$instance_num$*/,
	    .dev	= {
	    	.release	= plat_sploader_release,
	    	.platform_data	= &plat_sploader/*$instance_num$*/_data
	    },
	    .num_resources	= ARRAY_SIZE(sploader/*$instance_num$*/_resources),
	    .resource	= sploader/*$instance_num$*/_resources,
    }
/*$foreach:instance:end$*/
};

static int __init sploader_init(void)
{
	return platform_device_register(plat_sploader_devices);
}

static void __exit sploader_exit(void)
{
	platform_device_unregister(plat_sploader_devices);
}

module_init(sploader_init);
module_exit(sploader_exit);

MODULE_AUTHOR("Fabien Marteau <fabien.marteau@armadeus.com>");
MODULE_AUTHOR("Gwenhael Goavec-Merou <gwenhael.goavec-merou@armadeus.com>");
MODULE_DESCRIPTION("Driver to load spvision fpga");
MODULE_LICENSE("GPL");

