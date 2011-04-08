/*
 ***********************************************************************
 *
 * (c) Copyright 2008    Armadeus project
 * Fabien Marteau <fabien.marteau@armadeus.com>
 * Generic driver for Wishbone input IP
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
 *
 * TODO: - Manage configuration bus speed and read frequency
 *	     - Clean major system
 */

#include <linux/version.h>
#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,20)
#include <linux/config.h>
#endif

/* kobj */
#include <linux/kobject.h>

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

/* input */
#include "input.h"


/* for debugging messages*/
//#define input_DEBUG

#undef PDEBUG
#ifdef input_DEBUG
# ifdef __KERNEL__
/* for kernel spage */
#   define PDEBUG(fmt,args...) printk(KERN_DEBUG "input : " fmt, ##args)
# else
/* for user space */
#   define PDEBUG(fmt,args...) printk(stderr, fmt, ##args)
# endif
#else
# define PDEBUG(fmt,args...) /* no debbuging message */
#endif

/********************************
 * main device structure
 * ******************************/
struct input_dev{
    char *name;           /* name of the instance */
	struct kobject kobj;  /* kobj test */
    struct cdev cdev;     /* char device structure */
    struct semaphore sem; /* mutex */
	void * membase;		  /* base address for instance  */
	int    interrupt;     /* boolean value, read with interrupt or not */
    dev_t devno;          /* to store Major and minor numbers */
    u8 read_in_wait;      /* user is waiting for value to read */
};


/***********************************
 * sysfs attributes
 ***********************************/

static ssize_t show_input_bus_speed(struct device *dev,
									struct device_attribute *attr,
									char * buf)
{
	u16 data;
	struct plat_input_port *plat_data = dev->platform_data;

	data = ioread16(plat_data->membase+INPUT_BUS_PER_OFFSET);
	
	return snprintf(buf,PAGE_SIZE,"%d\n",data);
}

static ssize_t store_input_bus_speed(struct device *dev,
									 struct device_attribute *attr,
									 const char * buf,
									 size_t count)
{
	u16 data;
	struct plat_input_port *plat_data = dev->platform_data;

	data = (u16)simple_strtol(buf,NULL,0);
		
	iowrite16(data,plat_data->membase+INPUT_BUS_PER_OFFSET);
	return count;
}

static ssize_t show_input_read_per(struct device *dev,
								   struct device_attribute *attr,
								   char * buf)
{
	/* TODO */
	u16 data;
	struct plat_input_port *plat_data = dev->platform_data;

	data = ioread16(plat_data->membase+INPUT_READ_PER_OFFSET);

	return snprintf(buf,PAGE_SIZE,"%d\n",data);
}

static ssize_t store_input_read_per(struct device *dev,
									struct device_attribute *attr,
									const char * buf,
									size_t count)
{
	u16 data;
	struct plat_input_port *plat_data = dev->platform_data;

	data = (u16)simple_strtol(buf,NULL,0);

	iowrite16(data,plat_data->membase+INPUT_READ_PER_OFFSET);
	return count;
}


/* if set at 1, reading /dev file will block until
 * entry value change */
static ssize_t show_interrupt(struct device *dev,
							  struct device_attribute *attr,
							  char * buf)
{
	struct plat_input_port *plat_data = dev->platform_data;
	return snprintf(buf,PAGE_SIZE,"%d\n",plat_data->sdev->interrupt);
}

static ssize_t store_interrupt(struct device *dev,
							   struct device_attribute *attr,
							   const char * buf,
							   size_t count)
{
	int data;
	struct plat_input_port *plat_data = dev->platform_data;
	data = (int)simple_strtol(buf,NULL,0);

	if (data == 0){
		plat_data->sdev->interrupt = 0;
		/* if read in wait, wake up */
		if(plat_data->sdev->read_in_wait)up(&plat_data->sdev->sem);
		iowrite16(0,plat_data->membase+INPUT_REG_OFFSET);
		return count;
	}else{
		plat_data->sdev->interrupt = 1;
		iowrite16(1<<8,plat_data->membase+INPUT_REG_OFFSET);
		return count;
	}
}
static DEVICE_ATTR(bus_speed, 0644, show_input_bus_speed, store_input_bus_speed);
static DEVICE_ATTR(read_per, 0644, show_input_read_per, store_input_read_per);
static DEVICE_ATTR(interrupt, 0644, show_interrupt, store_interrupt);

/***********************************
 * characters file /dev operations
 * *********************************/
ssize_t input_read(struct file *fildes, char __user *buff,
				   size_t count, loff_t *offp)
{
	struct input_dev *ldev = fildes->private_data;

	u16 data=0;
	ssize_t retval = 0;

	ldev->read_in_wait = 1;

	if(*offp + count >= 1)               /* Only one word can be read */
		count = 1 - *offp;


	if(ldev->interrupt==1)
		if((retval=down_interruptible(&ldev->sem))<0)
		{
			goto out;
		}

	data=0x00ff&ioread16(ldev->membase+INPUT_REG_OFFSET);
	PDEBUG("Read %d at 0x%x\n",data,(unsigned int)ldev->membase+INPUT_REG_OFFSET);

	/* return data for user */
	if(copy_to_user(buff,&data,2)){
		printk(KERN_WARNING "read : copy to user data error\n");
		retval = -EFAULT;
		goto out;
	}

	*offp = *offp + count;
	retval = 1;

out:
	ldev->read_in_wait = 0;
	return retval;
}


int input_open(struct inode *inode, struct file *filp){
	/* Allocate and fill any data structure to be put in filp->private_data */
	filp->private_data = container_of(inode->i_cdev,struct input_dev, cdev);
	return 0;
}

int input_release(struct inode *inode, struct file *filp)
{
	struct input_dev *dev;

	dev = container_of(inode->i_cdev,struct input_dev,cdev);
	filp->private_data=NULL;

	return 0;
}


static struct file_operations input_fops = {
	.owner = THIS_MODULE,
	.read  = input_read,
	.open  = input_open,
	.release = input_release,
};

/**********************************
 * irq management
 * awake read process
 * ********************************/

static irqreturn_t input_interrupt(int irq,void *dev_id){
	struct input_dev *ldev = dev_id;
	/* wake up reading process */
	if(ldev->interrupt == 1)
		if(ldev->read_in_wait)up(&ldev->sem);
	/* acknowledge irq_mngr */
	return IRQ_HANDLED;
}


/**********************************
 * driver probe
 **********************************/
static int input_probe(struct platform_device *pdev)
{
	struct plat_input_port *dev = pdev->dev.platform_data;

	int result = 0;        /* error return */
	int input_major,input_minor;
	u16 data;
	struct input_dev *sdev;

	PDEBUG("input probing\n");
	PDEBUG("Register %s num %d\n",dev->name,dev->num);

	/**************************/
	/* check if ID is correct */
	/**************************/
	data = ioread16(dev->membase+INPUT_ID_OFFSET);
	if(data != dev->idnum){
		result = -1;
		printk(KERN_WARNING "For %s id:%d doesn't match "
			   "with id read %d,\n is device present ?\n",
			   dev->name,dev->idnum,data);
		goto error_id;
	}

	/********************************************/
	/*	allocate memory for sdev structure	*/
	/********************************************/
	sdev = kmalloc(sizeof(struct input_dev),GFP_KERNEL);
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
	input_major = 251;
	input_minor = dev->num;

	sdev->devno = MKDEV(input_major, input_minor);
	result = alloc_chrdev_region(&(sdev->devno),input_minor, 1,dev->name);
	if (result < 0) {
		printk(KERN_WARNING "%s: can't get major %d\n",
			   dev->name,input_major);
		goto error_devno;
	}
	printk(KERN_INFO "%s: major %d and minor: %d\n",
		   dev->name,
		   MAJOR(sdev->devno),
		   MINOR(sdev->devno));

	/* initiate mutex locked */
	sdev->read_in_wait = 0;
	init_MUTEX_LOCKED(&sdev->sem);

	/****************************/
	/* Init the cdev structure  */
	/****************************/
	PDEBUG("Init the cdev structure\n");
	cdev_init(&sdev->cdev,&input_fops);
	sdev->cdev.owner = THIS_MODULE;
	sdev->cdev.ops   = &input_fops;

	/* Add the device to the kernel, connecting cdev to major/minor number */
	PDEBUG("%s: Add the device to the kernel, "
		   "connecting cdev to major/minor number \n",dev->name);
	result = cdev_add(&sdev->cdev,sdev->devno,1);
	if(result < 0){
		printk(KERN_WARNING "%s: can't add cdev\n",dev->name);
		goto error_cdev_add;
	}

	/* irq registering */
	result = request_irq(dev->interrupt_number,
						 input_interrupt,
						 IRQF_SAMPLE_RANDOM,
						 sdev->name,
						 sdev);
	if(result < 0){
		printk(KERN_ERR "Can't register irq %d\n",
			   dev->interrupt_number);
		goto request_irq_error;
	}
	printk(KERN_INFO "input: irq registered : %d\n",
		   dev->interrupt_number);
	/*******************************
	 * disable interrupt from input
	 *******************************/
	iowrite16(0,dev->membase+INPUT_REG_OFFSET);
	dev->sdev->interrupt = 0;

	/*********************
	 * sysfs attributes
	 *********************/
	result = device_create_file(&pdev->dev, &dev_attr_read_per);
	if (result < 0){
		printk(KERN_ERR "input: can't create sysfs read_per\n");
		goto read_per_sys_error;
	}
	result = device_create_file(&pdev->dev, &dev_attr_bus_speed);
	if (result < 0){
		printk(KERN_ERR "input: can't create sysfs bus_speed\n");
		goto bus_speed_sys_error;
	}
	result = device_create_file(&pdev->dev, &dev_attr_interrupt);
	if (result < 0){
		printk(KERN_ERR "input: can't create sysfs interrupt\n");
		goto interrupt_sys_error;
	}

	/************************/
    /* OK module inserted ! */
	/************************/
    printk(KERN_INFO "%s insered\n",dev->name);
    return 0;

	/*********************/
	/* Errors management */
	/*********************/

	device_remove_file(&pdev->dev,&dev_attr_interrupt);
interrupt_sys_error:
	device_remove_file(&pdev->dev,&dev_attr_read_per);
read_per_sys_error:
	device_remove_file(&pdev->dev,&dev_attr_bus_speed);
bus_speed_sys_error:
	/* freeing irq */
	free_irq(dev->interrupt_number,sdev);
request_irq_error:
	/* delete the cdev structure */
	cdev_del(&sdev->cdev);
	PDEBUG("%s:cdev deleted\n",dev->name);
error_cdev_add:
	/* free major and minor number */
	unregister_chrdev_region(sdev->devno,1);
	printk(KERN_INFO "%s: Led deleted\n",dev->name);
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

static int __devexit input_remove(struct platform_device *pdev)
{
	struct plat_input_port *dev = pdev->dev.platform_data;
	struct input_dev *sdev = (*dev).sdev;

	/* remove sysfs files */
	device_remove_file(&pdev->dev,&dev_attr_read_per);
	device_remove_file(&pdev->dev,&dev_attr_bus_speed);

	/* freeing irq */
	free_irq(dev->interrupt_number,sdev);
//request_irq_error:
	/* delete the cdev structure */
	cdev_del(&sdev->cdev);
	PDEBUG("%s:cdev deleted\n",dev->name);
//error_cdev_add:
	/* free major and minor number */
	unregister_chrdev_region(sdev->devno,1);
	printk(KERN_INFO "%s: Led deleted\n",dev->name);
//error_devno:
//error_name_copy:
	kfree(sdev->name);
//error_name_alloc:
	kfree(sdev);
//error_sdev_alloc:
	printk(KERN_INFO "%s: deleted with success\n", dev->name);
//error_id:
	return 0;

}

static struct platform_driver plat_input_driver =
{
    .probe      = input_probe,
    .remove     = __devexit_p(input_remove),
    .driver     =
    {
        .name    = "input",
        .owner   = THIS_MODULE,
    },
};

/**********************************
 * Module management
 **********************************/
static int __init input_init(void)
{
    int ret;


    PDEBUG("Platform driver name %s",plat_input_driver.driver.name);
    ret = platform_driver_register(&plat_input_driver);
    if (ret) {
        printk(KERN_ERR "Platform driver register error\n");
        return ret;
    }
    return 0;
}

static void __exit input_exit(void)
{
    platform_driver_unregister(&plat_input_driver);
}

module_init(input_init);
module_exit(input_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Fabien Marteau <fabien.marteau@armadeus.com> "
			  "- ARMadeus Systems");
MODULE_DESCRIPTION("input device generic driver");


