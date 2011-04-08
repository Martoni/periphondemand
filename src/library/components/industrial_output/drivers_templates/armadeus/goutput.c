/*
 ***********************************************************************
 *
 * (c) Copyright 2008	Armadeus project
 * Fabien Marteau <fabien.marteau@armadeus.com>
 * Generic driver for Wishbone output IP
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

/* output */
#include "output.h"

/* for debugging messages*/
//#define output_DEBUG

#undef PDEBUG
#ifdef output_DEBUG
# ifdef __KERNEL__
/* for kernel spage */
#   define PDEBUG(fmt,args...) printk(KERN_DEBUG "output : " fmt, ##args)
# else
/* for user space */
#   define PDEBUG(fmt,args...) printk(stderr, fmt, ##args)
# endif
#else
# define PDEBUG(fmt,args...) /* no debbuging message */
#endif

/*************************/
/* main device structure */
/*************************/
struct output_dev{
	char *name;		/* the name of the instance */
	int  loaded_output_num;/* number of the output, depends on load order*/
	struct cdev cdev;/* Char device structure */
	void * membase;  /* base address for instance  */
	dev_t devno;	 /* to store Major and minor numbers */
};

/******************************/
/* to read write output register */
/******************************/
ssize_t output_read(struct file *fildes, char __user *buff,
				 size_t count, loff_t *offp);

ssize_t output_write(struct file *fildes, const char __user *
					 buff,size_t count, loff_t *offp);
int output_open(struct inode *inode, struct file *filp);

int output_release(struct inode *, struct file *filp);

static struct file_operations output_fops = {
	.owner = THIS_MODULE,
	.read  = output_read,
	.write = output_write,
	.open  = output_open,
	.release = output_release,
};

/* output major number */
static int output_major = 0;
module_param(output_major, int, 0644);
MODULE_PARM_DESC(output_major, "Static major number (none = dynamic)");

/***********************************
 * characters file /dev operations
 * *********************************/
ssize_t output_read(struct file *fildes, char __user *buff,
					size_t count, loff_t *offp){
	struct output_dev *sdev = fildes->private_data;
	u16 data=0;
	PDEBUG("Read value\n");
	if(*offp != 0 ){ /* offset must be 0 */
		PDEBUG("offset %d\n",(int)*offp);
		return 0;
	}

	PDEBUG("count %d\n",count);
	if(count > 2){ /* 16bits max*/
		count = 2;
	}

	data = ioread16(sdev->membase+output_REG_OFFSET);
	PDEBUG("Read %d at %x\n",data,(int)(sdev->membase+output_REG_OFFSET));

	/* return data for user */
	if(copy_to_user(buff,&data,count)){
		printk(KERN_WARNING "read : copy to user data error\n");
		return -EFAULT;
	}
	return count;
}

ssize_t output_write(struct file *fildes, const char __user *
					 buff,size_t count, loff_t *offp){
	struct output_dev *sdev = fildes->private_data;
	u16 data=0;

	if(*offp != 0){ /* offset must be 0 */
		PDEBUG("offset %d\n",(int)*offp);
		return 0;
	}

	PDEBUG("count %d\n",count);
	if(count > 2){ /* 16 bits max)*/
		count = 2;
	}

	do{
		data = ioread16(sdev->membase+output_REG_OFFSET);
	}while(data&0x0100); /* while busy bit is one, wait*/

	if(copy_from_user(&data,buff,count)){
		printk(KERN_WARNING "write : copy from user error\n");
		return -EFAULT;
	}

	PDEBUG("Write %d at %x\n",
		   data,
		   (int)(sdev->membase+output_REG_OFFSET));
	iowrite16(data,sdev->membase+output_REG_OFFSET);

	return count;
}

int output_open(struct inode *inode, struct file *filp){
	/* Allocate and fill any data structure to be put in filp->private_data */
	filp->private_data = container_of(inode->i_cdev,struct output_dev, cdev);
	PDEBUG( "output opened\n");
	return 0;
}

/* ******************************
 * Init and release functions
 * ******************************/
int output_release(struct inode *inode, struct file *filp)
{
	struct output_dev *dev;

	dev = container_of(inode->i_cdev,struct output_dev,cdev);
	PDEBUG( "%s: released\n",dev->name);
	filp->private_data=NULL;

	return 0;
}

/**********************************
 * driver probe
 **********************************/
static int output_probe(struct platform_device *pdev)
{
	struct plat_output_port *dev = pdev->dev.platform_data;

	int result = 0;				 /* error return */
	int output_minor;
	u16 data;
	struct output_dev *sdev;

	PDEBUG("output probing\n");
	PDEBUG("Register %s num %d\n",dev->name,dev->num);

	/**************************/
	/* check if ID is correct */
	/**************************/
	data = ioread16(dev->membase+dev->idoffset);
	if(data != dev->idnum){
		result = -1;
		printk(KERN_WARNING "For %s id:%d doesn't match with "
			   "id read %d,\n is device present ?\n",
			   dev->name,dev->idnum,data);
		goto error_id;
	}

	/********************************************/
	/*	allocate memory for sdev structure	*/
	/********************************************/
	sdev = kmalloc(sizeof(struct output_dev),GFP_KERNEL);
	if(!sdev){
		result = -ENOMEM;
		goto error_sdev_alloc;
	}
	dev->sdev = sdev;
	sdev->membase = dev->membase;
	sdev->name = (char *)kmalloc((1+strlen(dev->name))*sizeof(char),
								 GFP_KERNEL);
	if (sdev->name == NULL) {
		printk("Kmalloc name space error\n");
		goto error_name_alloc;
	}
	if (strncpy(sdev->name,dev->name,1+strlen(dev->name)) < 0) {
		printk("copy error");
		goto error_name_copy;
	}

	/******************************************/
	/* Get the major and minor device numbers */
	/******************************************/

	output_minor = dev->num ;/* num come from plat_output_port data structure */

	sdev->devno = MKDEV(output_major, output_minor);
	result = alloc_chrdev_region(&(sdev->devno),output_minor, 1,dev->name);
	if (result < 0) {
		printk(KERN_WARNING "%s: Problem with major %d\n",dev->name,output_major);
		goto error_devno;
	}
	printk(KERN_INFO "%s: MAJOR: %d MINOR: %d\n",
		   dev->name,
		   MAJOR(sdev->devno),
		   MINOR(sdev->devno));

	/****************************/
	/* Init the cdev structure  */
	/****************************/
	PDEBUG("Init the cdev structure\n");
	cdev_init(&sdev->cdev, &output_fops);
	sdev->cdev.owner = THIS_MODULE;
	sdev->cdev.ops   = &output_fops;

	/* Add the device to the kernel, connecting cdev to major/minor number */
	PDEBUG("%s:Add the device to the kernel, "
		   "connecting cdev to major/minor number \n", dev->name);
	result = cdev_add(&sdev->cdev, sdev->devno, 1);
	if (result) {
		printk(KERN_WARNING "%s: can't add cdev\n", dev->name);
		goto error_cdev_add;
	}

	/* initialize output value */
	data=0;
	iowrite16(data,sdev->membase);
	PDEBUG("Wrote %x at %x\n", data,(int)( sdev->membase+output_REG_OFFSET));

	/* OK module inserted ! */
	printk(KERN_INFO "output module %s insered\n", dev->name);
	return 0;

	/*********************/
	/* Errors management */
	/*********************/
	/* delete the cdev structure */
	cdev_del(&sdev->cdev);
	PDEBUG("%s:cdev deleted\n",dev->name);
error_cdev_add:
	/* free major and minor number */
	unregister_chrdev_region(sdev->devno,1);
	printk(KERN_INFO "%s: output deleted\n",dev->name);
error_devno:
error_name_copy:
	kfree(sdev->name);
error_name_alloc:
	kfree(sdev);
error_sdev_alloc:
	printk(KERN_ERR "%s: not inserted\n", dev->name);
error_id:
	return result;
}

static int __devexit output_remove(struct platform_device *pdev)
{
	struct plat_output_port *dev = pdev->dev.platform_data;
	struct output_dev *sdev = (*dev).sdev;
	PDEBUG("Unregister %s, number %d\n",dev->name,dev->num);
	/* delete the cdev structure */
	PDEBUG("cdev name : %s\n",sdev->name);
	cdev_del(&sdev->cdev);
	PDEBUG("%s:cdev deleted\n",dev->name);
	/*error_cdev_add:*/
	/* free major and minor number */
	unregister_chrdev_region(sdev->devno,1);
	/*error_devno:*/
	/*error_name_copy:*/
	kfree(sdev->name);
	/*error_name_alloc:*/
	kfree(sdev);
	/*error_sdev_alloc:*/
	printk(KERN_INFO "%s: deleted with success\n", dev->name);
	return 0;
}

static struct platform_driver plat_output_driver = {
	.probe	  = output_probe,
	.remove	 = __devexit_p(output_remove),
	.driver	 = {
		.name	= "output",
		.owner   = THIS_MODULE,
	},
};

/**********************************
 * Module management
 **********************************/
static int __init output_init(void)
{
	int ret;

	PDEBUG("Platform driver name %s\n", plat_output_driver.driver.name);

	ret = platform_driver_register(&plat_output_driver);
	return ret;
}

static void output_exit(void)
{

	platform_driver_unregister(&plat_output_driver);
	PDEBUG("driver unregistered\n");
}

module_init(output_init);
module_exit(output_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Fabien Marteau <fabien.marteau@armadeus.com>-ARMadeus Systems");
MODULE_DESCRIPTION("output device driver");

