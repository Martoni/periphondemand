/*
 * Generic driver for Wishbone LED IP
 *
 * (c) Copyright 2008	Armadeus project
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
#include <linux/init.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/ioport.h>	/* request_mem_region */
#include <linux/platform_device.h>
#if LINUX_VERSION_CODE > KERNEL_VERSION(2,6,29)
#include <linux/slab.h>		/* kmalloc */
#endif

#include <asm/uaccess.h>	/* copy_to_user function */
#include <asm/io.h>		/* readw() writew() */
#include <mach/hardware.h>

#include "led.h"

/* main device structure */
struct led_dev {
	char *name;		/* the name of the instance */
	int  loaded_led_num;/* number of the led, depends on load order*/
	struct cdev cdev;/* Char device structure */
	void * membase;  /* base address for instance  */
	dev_t devno;	 /* to store Major and minor numbers */
	struct resource *mem_res;
};

ssize_t led_read(struct file *fildes, char __user *buff,
				 size_t count, loff_t *offp);

ssize_t led_write(struct file *fildes, const char __user *
				  buff,size_t count, loff_t *offp);
int led_open(struct inode *inode, struct file *filp);

int led_release(struct inode *, struct file *filp);

struct file_operations led_fops = {
	.owner = THIS_MODULE,
	.read  = led_read,
	.write = led_write,
	.open  = led_open,
	.release = led_release,
};

/***********************************
 * characters file /dev operations
 * *********************************/
ssize_t led_read(struct file *fildes, char __user *buff,
				 size_t count, loff_t *offp)
{
	struct led_dev *sdev = fildes->private_data;
	u16 data=0;

	pr_debug("Read value\n");
	if (*offp != 0) { /* offset must be 0 */
		pr_debug("offset %d\n", (int)*offp);
		return 0;
	}

	pr_debug("count %d\n", count);
	if (count > 2) { /* 16bits max*/
		count = 2; 
	}

	data = readw(sdev->membase + LED_REG_OFFSET);
	pr_debug("Read %d at %x\n", data, (int)(sdev->membase + LED_REG_OFFSET));

	/* return data for user */
	if (copy_to_user(buff, &data, count)) {
		printk(KERN_WARNING "read : copy to user data error\n");
		return -EFAULT;
	}
	return count;
}

ssize_t led_write(struct file *fildes, const char __user *
				  buff,size_t count, loff_t *offp)
{
	struct led_dev *sdev = fildes->private_data;
	u16 data = 0;

	if (*offp != 0) { /* offset must be 0 */
		pr_debug("offset %d\n", (int)*offp);
		return 0;
	}

	pr_debug("count %d\n", count);
	if (count > 2) { /* 16 bits max)*/
		count = 2;
	}

	if (copy_from_user(&data, buff, count)) {
		printk(KERN_WARNING "write : copy from user error\n");
		return -EFAULT;
	}

	pr_debug("Write %d at %x\n",
		   data,
		   (int)(sdev->membase + LED_REG_OFFSET));
	writew(data, sdev->membase + LED_REG_OFFSET);

	return count;
}

int led_open(struct inode *inode, struct file *filp)
{
	/* Allocate and fill any data structure to be put in filp->private_data */
	filp->private_data = container_of(inode->i_cdev, struct led_dev, cdev);
	pr_debug("LED opened\n");
	return 0;
}

int led_release(struct inode *inode, struct file *filp)
{
	struct led_dev *dev;

	dev = container_of(inode->i_cdev, struct led_dev, cdev);
	pr_debug("%s: released\n", dev->name);
	filp->private_data=NULL;

	return 0;
}

static int led_probe(struct platform_device *pdev)
{
	struct plat_led_port *pdata = pdev->dev.platform_data;
	int ret = 0;
	int led_major, led_minor;
	u16 ip_id;
	struct led_dev *sdev;
	struct resource *mem_res;

	pr_debug("LED probing\n");
	pr_debug("Register %s num %d\n", pdata->name, pdata->num);

	if (!pdata) {
		dev_err(&pdev->dev, "Platform data required !\n");
		return -ENODEV;
	}

	/* get resources */
	mem_res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	if (!mem_res) {
		dev_err(&pdev->dev, "can't find mem resource\n");
		return -EINVAL;
	}

	mem_res =
	    request_mem_region(mem_res->start, resource_size(mem_res),
			       pdev->name);
	if (!mem_res) {
		dev_err(&pdev->dev, "iomem already in use\n");
		return -EBUSY;
	}

	/* allocate memory for private structure */
	sdev = kmalloc(sizeof(struct led_dev), GFP_KERNEL);
	if (!sdev) {
		ret = -ENOMEM;
		goto out_release_mem;
	}

	sdev->membase = ioremap(mem_res->start, resource_size(mem_res));
	if (!sdev->membase) {
		dev_err(&pdev->dev, "ioremap failed\n");
		ret = -ENOMEM;
		goto out_dev_free;
	}
	sdev->mem_res = mem_res;

	/* check if ID is correct */
	ip_id = readw(sdev->membase + pdata->idoffset);
	if (ip_id != pdata->idnum) {
		ret = -ENODEV;
		printk(KERN_WARNING "For %s id:%d doesn't match with "
			   "id read %d,\n is device present ?\n",
			   pdata->name, pdata->idnum, ip_id);
		goto out_iounmap;
	}

	pdata->sdev = sdev;
	sdev->name = (char *)kmalloc((1+strlen(pdata->name))*sizeof(char), 
								 GFP_KERNEL);
	if (sdev->name == NULL) {
		printk("Kmalloc name space error\n");
		goto out_iounmap;
	}
	if (strncpy(sdev->name, pdata->name, 1+strlen(pdata->name)) < 0) {
		printk("copy error");
		goto out_name_free;
	}

	/* Get the major and minor device numbers */
	led_major = 252;
	led_minor = pdata->num;

	sdev->devno = MKDEV(led_major, led_minor);
	ret = alloc_chrdev_region(&(sdev->devno), led_minor, 1, pdata->name);
	if (ret < 0) {
		printk(KERN_WARNING "%s: can't get major %d\n", pdata->name, led_major);
		goto out_name_free;
	}
	printk(KERN_INFO "%s: MAJOR: %d MINOR: %d\n",
		   pdata->name,
		   MAJOR(sdev->devno),
		   MINOR(sdev->devno));

	/* Init the cdev structure  */
	pr_debug("Init the cdev structure\n");
	cdev_init(&sdev->cdev, &led_fops);
	sdev->cdev.owner = THIS_MODULE;
	sdev->cdev.ops   = &led_fops;

	/* Add the device to the kernel, connecting cdev to major/minor number */
	pr_debug("%s:Add the device to the kernel, "
		   "connecting cdev to major/minor number \n", pdata->name);
	ret = cdev_add(&sdev->cdev, sdev->devno, 1);
	if (ret) {
		printk(KERN_WARNING "%s: can't add cdev\n", pdata->name);
		goto out_cdev_free;
	}

	/* initialize LED value */
	writew(1, sdev->membase);

	/* OK module inserted ! */
	printk(KERN_INFO "LED module %s inserted\n", pdata->name);
	return 0;

	cdev_del(&sdev->cdev);
out_cdev_free:
	unregister_chrdev_region(sdev->devno, 1);
	printk(KERN_INFO "%s: LED deleted\n", pdata->name);
out_name_free:
	kfree(sdev->name);
out_iounmap:
	iounmap(sdev->membase);
out_dev_free:
	kfree(sdev);
out_release_mem:
	release_mem_region(mem_res->start, resource_size(mem_res));

	return ret;
}

static int __devexit led_remove(struct platform_device *pdev)
{
	struct plat_led_port *dev = pdev->dev.platform_data;
	struct led_dev *sdev = (*dev).sdev;

	pr_debug("Unregister %s, number %d\n", dev->name, dev->num);
	pr_debug("cdev name : %s\n", sdev->name);
	cdev_del(&sdev->cdev);
	pr_debug("%s:cdev deleted\n", dev->name);
	unregister_chrdev_region(sdev->devno, 1);
	kfree(sdev->name);
	iounmap(sdev->membase);
	kfree(sdev);
	release_mem_region(sdev->mem_res->start, resource_size(sdev->mem_res));
	printk(KERN_INFO "%s: deleted with success\n", dev->name);

	return 0;
}

static struct platform_driver plat_led_driver = {
	.probe	  = led_probe,
	.remove	 = __devexit_p(led_remove),
	.driver	 = {
		.name	= "led",
		.owner   = THIS_MODULE,
	},
};

static int __init led_init(void)
{
	int ret;

	pr_debug("Platform driver name %s\n", plat_led_driver.driver.name);
	ret = platform_driver_register(&plat_led_driver);
	return ret;
}

static void led_exit(void)
{
	platform_driver_unregister(&plat_led_driver);
	pr_debug("driver unregistered\n");
}

module_init(led_init);
module_exit(led_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Fabien Marteau <fabien.marteau@armadeus.com>");
MODULE_DESCRIPTION("Wishbone IP LED device driver");

