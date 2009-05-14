/*
 ***********************************************************************
 *
 * (c) Copyright 2008	Armadeus project
 * Fabien Marteau <fabien.marteau@armadeus.com>
 * Generic driver for Wishbone simplegpio IP
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

/* simplegpio */
#include "simplegpio.h"

/* sysfs */
#include <linux/sysfs.h>
#include <linux/string.h>


/* for debugging messages*/
//#define simplegpio_DEBUG

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

/*************************/
/* main device structure */
/*************************/
struct simplegpio_dev{
	char *name;		/* the name of the instance */
	int  loaded_simplegpio_num;/* number of the simplegpio, depends on load order*/
	struct cdev cdev;/* Char device structure */
	void * membase;  /* base address for instance  */
	dev_t devno;	 /* to store Major and minor numbers */
};

/***********************************
 * characters file /dev operations
 * *********************************/
ssize_t simplegpio_read(struct file *fildes, char __user *buff,
				 size_t count, loff_t *offp){
	struct simplegpio_dev *sdev = fildes->private_data;
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

	data = ioread16(sdev->membase+SIMPLEGPIO_REG_OFFSET);
	PDEBUG("Read %d at %x\n",data,(int)(sdev->membase+SIMPLEGPIO_REG_OFFSET));

	/* return data for user */
	if(copy_to_user(buff,&data,count)){
		printk(KERN_WARNING "read : copy to user data error\n");
		return -EFAULT;
	}
	return count;
}

/* write */
ssize_t simplegpio_write(struct file *fildes, const char __user *
				  buff,size_t count, loff_t *offp){
	struct simplegpio_dev *sdev = fildes->private_data;
	u16 data=0;

	if(*offp != 0){ /* offset must be 0 */
		PDEBUG("offset %d\n",(int)*offp);
		return 0;
	}

	PDEBUG("count %d\n",count);
	if(count > 2){ /* 16 bits max)*/
		count = 2;
	}

	if(copy_from_user(&data,buff,count)){
		printk(KERN_WARNING "write : copy from user error\n");
		return -EFAULT;
	}

	PDEBUG("Write %d at %x\n",
		   data,
		   (int)(sdev->membase+SIMPLEGPIO_REG_OFFSET));
	iowrite16(data,sdev->membase+SIMPLEGPIO_REG_OFFSET);

	return count;
}

int simplegpio_open(struct inode *inode, struct file *filp){
	/* Allocate and fill any data structure to be put in filp->private_data */
	filp->private_data = container_of(inode->i_cdev,struct simplegpio_dev, cdev);
	PDEBUG( "simplegpio opened\n");
	return 0;
}

/*release functions*/
int simplegpio_release(struct inode *inode, struct file *filp)
{
	struct simplegpio_dev *dev;

	dev = container_of(inode->i_cdev,struct simplegpio_dev,cdev);
	PDEBUG( "%s: released\n",dev->name);
	filp->private_data=NULL;

	return 0;
}

/* ioctl */
int simplegpio_ioctl(struct inode *inode, 
					 struct file *filp, 
					 unsigned int cmd, 
					 unsigned long arg )
{
    int err = 0; int ret = 0;
	struct simplegpio_dev *sdev = filp->private_data;

	/* */
//	if(_IOC_TYPE(cmd)!= SGPIO_MAGIC)return -ENOTTY;
//	if(_IOC_NR(cmd) != SGPIO_IOC_MAX)return -ENOTTY;
    
    switch(cmd) 
    {
        case SGPIO_IORDIRECTION:
			if(!capable(CAP_SYS_RAWIO))
				return -EPERM;
			return (int)ioread16(sdev->membase+SIMPLEGPIO_STATUS_OFFSET);
        break;

        case SGPIO_IOWDIRECTION:
			if(!capable(CAP_SYS_RAWIO))
				return -EPERM;
			iowrite16((int)arg,sdev->membase+SIMPLEGPIO_STATUS_OFFSET);
			PDEBUG("wrote 0x%04x, at 0x%04x\n",(int)arg,(int)sdev->membase+SIMPLEGPIO_STATUS_OFFSET);
			return 0;
        break;

        default:
            return -ENOTTY;
        break;
    }
    return ret;

}
struct file_operations simplegpio_fops = {
	.owner = THIS_MODULE,
	.read  = simplegpio_read,
	.write = simplegpio_write,
	.ioctl = simplegpio_ioctl,
	.open  = simplegpio_open,
	.release = simplegpio_release,
};


/**********************************
 * driver probe
 **********************************/
static int simplegpio_probe(struct platform_device *pdev)
{
	struct plat_simplegpio_port *dev = pdev->dev.platform_data;

	int result = 0;				 /* error return */
	int simplegpio_major,simplegpio_minor;
	u16 data;
	struct simplegpio_dev *sdev;

	PDEBUG("simplegpio probing\n");
	PDEBUG("Register %s num %d\n",dev->name,dev->num);

	/**************************/
	/* check if ID is correct */
	/**************************/
	PDEBUG("membase 0x%x\n",(unsigned int)dev->membase);
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
	sdev = kmalloc(sizeof(struct simplegpio_dev),GFP_KERNEL);
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

	simplegpio_major = 250; 
	simplegpio_minor = dev->num ;/* num come from plat_simplegpio_port data structure */

	PDEBUG("%s:Get the major and minor device numbers\n",dev->name);
	if (simplegpio_major) {
		sdev->devno = MKDEV(simplegpio_major, simplegpio_minor);
		result = register_chrdev_region(sdev->devno, 1,dev->name);
	} else {
		result = alloc_chrdev_region(&sdev->devno, simplegpio_minor, 1, dev->name);
		simplegpio_major = MAJOR(sdev->devno);
	}
	if (result < 0) {
		printk(KERN_WARNING "%s: can't get major %d\n",dev->name,simplegpio_major);
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
	cdev_init(&sdev->cdev, &simplegpio_fops);
	sdev->cdev.owner = THIS_MODULE;
	sdev->cdev.ops   = &simplegpio_fops;

	/* Add the device to the kernel, connecting cdev to major/minor number */
	PDEBUG("%s:Add the device to the kernel, "
		   "connecting cdev to major/minor number \n", dev->name);
	result = cdev_add(&sdev->cdev, sdev->devno, 1);
	if (result) {
		printk(KERN_WARNING "%s: can't add cdev\n", dev->name);
		goto error_cdev_add;
	}

	/* OK module inserted ! */
	printk(KERN_INFO "simplegpio module %s insered\n", dev->name);
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
	printk(KERN_INFO "%s: simplegpio deleted\n",dev->name);
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

static int __devexit simplegpio_remove(struct platform_device *pdev)
{
	struct plat_simplegpio_port *dev = pdev->dev.platform_data;
	struct simplegpio_dev *sdev = (*dev).sdev;
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

static struct platform_driver plat_simplegpio_driver = {
	.probe	  = simplegpio_probe,
	.remove	 = __devexit_p(simplegpio_remove),
	.driver	 = {
		.name	= "simplegpio",
		.owner   = THIS_MODULE,
	},
};

/**********************************
 * Module management
 **********************************/
static int __init simplegpio_init(void)
{
	int ret;
	printk(KERN_INFO "ioctl code for SGPIO_IORDIRECTION : %x\n",SGPIO_IORDIRECTION);
	printk(KERN_INFO "ioctl code for SGPIO_IOWDIRECTION : %x\n",SGPIO_IOWDIRECTION);
	PDEBUG("Platform driver name %s\n", plat_simplegpio_driver.driver.name);
	ret = platform_driver_register(&plat_simplegpio_driver);
	return ret;
}

static void simplegpio_exit(void)
{
	platform_driver_unregister(&plat_simplegpio_driver);
	PDEBUG("driver unregistered\n");
}

module_init(simplegpio_init);
module_exit(simplegpio_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Fabien Marteau <fabien.marteau@armadeus.com>-ARMadeus Systems");
MODULE_DESCRIPTION("simplegpio device driver");

