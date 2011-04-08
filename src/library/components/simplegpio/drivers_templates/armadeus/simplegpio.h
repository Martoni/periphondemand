/*
 ***********************************************************************
 *
 * (c) Copyright 2007	Armadeus project
 * Fabien Marteau <fabien.marteau@armadeus.com>
 * Driver for Wishbone simplegpio IP
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


#ifndef __simplegpio_H__
#define __simplegpio_H__

#include <linux/version.h>
#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,20)
#include <linux/config.h>
#endif

/* form module/drivers */
#include <linux/init.h>
#include <linux/module.h>

/* for file  operations */
#include <linux/fs.h>
#include <linux/cdev.h>

/* copy_to_user function */
#include <asm/uaccess.h>

/* request_mem_region */
#include <linux/ioport.h>

/* readw() writew() */
#include <asm/io.h>

#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,27)
/* hardware addresses */
#	include <asm/hardware.h>
#else
#	include <mach/hardware.h>
#endif


/* for platform device */
#include <linux/platform_device.h>

/* ioctl */
#include <linux/ioctl.h>

#endif

/* for debugging messages*/
#define simplegpio_DEBUG

#undef PDEBUG
#ifdef simplegpio_DEBUG
# ifdef __KERNEL__
	/* for kernel spage */
#   define PDEBUG(fmt,args...) printk(KERN_DEBUG "simplegpio : " fmt, ##args)
# else
	/* for user space */
#   define PDEBUG(fmt,args...) printk(stderr, fmt, ##args)
# endif
#else
# define PDEBUG(fmt,args...) /* no debbuging message */
#endif


#define FPGA_BASE_ADDR IMX_CS1_PHYS
#define FPGA_MEM_SIZE  IMX_CS1_SIZE

#define simplegpio_NUMBER /*$number_of_instances$*/

#define SIMPLEGPIO_REG_OFFSET		(0x00)
#define SIMPLEGPIO_STATUS_OFFSET	(0x02)
#define SIMPLEGPIO_ID_OFFSET		(0x04)

/* platform device */
struct plat_simplegpio_port{
	const char  *name;		/* instance name  */
	int			num;		/* instance number */
	void		*membase;	/* virtual base address */
	int			idnum;		/* identity number */
	int			idoffset;	/* identity relative address */
	struct kobject kobj_io;    /* kobject for input/output */
	struct kobject kobj_status;/* kobject for status */
	struct simplegpio_dev *sdev;	/* struct for main device structure*/
};

/* ioctl codes */
#define SGPIO_MAGIC (0x82)
#define SGPIO_IORDIRECTION _IOR(SGPIO_MAGIC,0,int)
#define SGPIO_IOWDIRECTION _IOW(SGPIO_MAGIC,1,int)
#define	SGPIO_IOC_MAX 2
