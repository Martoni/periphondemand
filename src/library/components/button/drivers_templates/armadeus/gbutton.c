/*
 * Generic driver for Wishbone button IP
 *
 * (c) Copyright 2008-2011    The Armadeus Project - ARMadeus Systems
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
#include <linux/fs.h>		/* for file  operations */
#include <linux/cdev.h>
#include <linux/ioport.h>	/* request_mem_region */
#include <linux/platform_device.h>
#include <linux/interrupt.h>
#if LINUX_VERSION_CODE > KERNEL_VERSION(2,6,29)
#include <linux/slab.h>		/* kmalloc */
#endif

#include <asm/uaccess.h>	/* copy_to_user function */
#include <asm/io.h>		/* readw() writew() */

#include "button.h"

struct button_dev {
	char *name;		/* name of the instance */
	struct cdev cdev;	/* char device structure */
	struct semaphore sem;	/* mutex */
	void *membase;		/* base address for instance  */
	dev_t devno;		/* to store Major and minor numbers */
	u8 read_in_wait;	/* user is waiting for value to read */
	struct resource *mem_res;
	struct resource *irq_res;
};

ssize_t button_read(struct file *fildes, char __user * buff,
		    size_t count, loff_t * offp)
{
	struct button_dev *ldev = fildes->private_data;
	u16 data = 0;
	ssize_t retval = 0;

	ldev->read_in_wait = 1;

	if (*offp + count >= 1)	/* Only one word can be read */
		count = 1 - *offp;

	if ((retval = down_interruptible(&ldev->sem)) < 0) {
		goto out;
	}

	data = readw(ldev->membase + BUTTON_REG_OFFSET);
	pr_debug("Read %d at 0x%x\n", data,
		 (unsigned int)ldev->membase + BUTTON_REG_OFFSET);

	/* return data for user */
	if (copy_to_user(buff, &data, 2)) {
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

int button_open(struct inode *inode, struct file *filp)
{
	/* Allocate and fill any data structure to be put in filp->private_data */
	filp->private_data =
	    container_of(inode->i_cdev, struct button_dev, cdev);

	return 0;
}

int button_release(struct inode *inode, struct file *filp)
{
	struct button_dev *dev;

	dev = container_of(inode->i_cdev, struct button_dev, cdev);
	filp->private_data = NULL;

	return 0;
}

static struct file_operations button_fops = {
	.owner = THIS_MODULE,
	.read = button_read,
	.open = button_open,
	.release = button_release,
};

static irqreturn_t button_interrupt(int irq, void *dev_id)
{
	struct button_dev *ldev = dev_id;

	/* wake up reading process */
	if (ldev->read_in_wait)
		up(&ldev->sem);

	return IRQ_HANDLED;
}

static int button_probe(struct platform_device *pdev)
{
	struct plat_button_port *pdata = pdev->dev.platform_data;
	int ret = 0;
	int button_major, button_minor;
	u16 ip_id;
	struct button_dev *sdev;
	struct resource *mem_res;
	struct resource *irq_res;

	pr_debug("Button probing\n");
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
	irq_res = platform_get_resource(pdev, IORESOURCE_IRQ, 0);
	if (!irq_res) {
		dev_err(&pdev->dev, "can't find irq resource\n");
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
	sdev = kmalloc(sizeof(struct button_dev), GFP_KERNEL);
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
	sdev->irq_res = irq_res;

	/* check if ID is correct */
	ip_id = readw(sdev->membase + BUTTON_ID_OFFSET);
	if (ip_id != pdata->idnum) {
		ret = -ENODEV;
		dev_warn(&pdev->dev, "For %s id:%d doesn't match "
			 "with id read %d,\n is device present ?\n",
			 pdata->name, pdata->idnum, ip_id);
		goto out_iounmap;
	}

	pdata->sdev = sdev;

	sdev->name = (char *)kmalloc((1 + strlen(pdata->name)) * sizeof(char),
				     GFP_KERNEL);
	if (sdev->name == NULL) {
		dev_err(&pdev->dev, "Kmalloc name space error\n");
		goto out_iounmap;
	}
	if (strncpy(sdev->name, pdata->name, 1 + strlen(pdata->name)) < 0) {
		printk("copy error");
		goto out_name_free;
	}

	/* Get the major and minor device numbers */
	button_major = 251;
	button_minor = pdata->num;

	sdev->devno = MKDEV(button_major, button_minor);
	ret = alloc_chrdev_region(&(sdev->devno), button_minor, 1, pdata->name);
	if (ret < 0) {
		dev_warn(&pdev->dev, "%s: can't get major %d\n",
			 pdata->name, button_major);
		goto out_name_free;
	}
	dev_info(&pdev->dev, "%s: MAJOR: %d MINOR: %d\n",
		 pdata->name, MAJOR(sdev->devno), MINOR(sdev->devno));

	/* initiate mutex locked */
	sdev->read_in_wait = 0;
	sema_init(&sdev->sem, 0);

	/* Init the cdev structure  */
	cdev_init(&sdev->cdev, &button_fops);
	sdev->cdev.owner = THIS_MODULE;
	sdev->cdev.ops = &button_fops;

	pr_debug("%s: Add the device to the kernel, "
		 "connecting cdev to major/minor number \n", pdata->name);
	ret = cdev_add(&sdev->cdev, sdev->devno, 1);
	if (ret < 0) {
		dev_warn(&pdev->dev, "%s: can't add cdev\n", pdata->name);
		goto out_cdev_free;
	}

	/* irq registering */
	ret = request_irq(sdev->irq_res->start,
			  button_interrupt,
			  IRQF_SAMPLE_RANDOM, sdev->name, sdev);
	if (ret < 0) {
		printk(KERN_ERR "Can't register irq %d\n",
		       sdev->irq_res->start);
		goto request_irq_error;
	}

	/* OK driver ready ! */
	printk(KERN_INFO "%s loaded\n", pdata->name);
	return 0;

	free_irq(sdev->irq_res->start, sdev);
request_irq_error:
	cdev_del(&sdev->cdev);
	pr_debug("%s:cdev deleted\n", pdata->name);
out_cdev_free:
	unregister_chrdev_region(sdev->devno, 1);
	printk(KERN_INFO "%s: button deleted\n", pdata->name);
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

static int __devexit button_remove(struct platform_device *pdev)
{
	struct plat_button_port *pdata = pdev->dev.platform_data;
	struct button_dev *sdev = (*pdata).sdev;

	free_irq(sdev->irq_res->start, sdev);

	cdev_del(&sdev->cdev);
	pr_debug("%s:cdev deleted\n", pdata->name);

	unregister_chrdev_region(sdev->devno, 1);
	printk(KERN_INFO "%s: button deleted\n", pdata->name);

	kfree(sdev->name);
	iounmap(sdev->membase);
	kfree(sdev);
	release_mem_region(sdev->mem_res->start, resource_size(sdev->mem_res));
	printk(KERN_INFO "%s: deleted with success\n", pdata->name);

	return 0;
}

static struct platform_driver plat_button_driver = {
	.probe = button_probe,
	.remove = __devexit_p(button_remove),
	.driver = {
		   .name = "button",
		   .owner = THIS_MODULE,
		   },
};

static int __init button_init(void)
{
	int ret;

	pr_debug("Platform driver name %s", plat_button_driver.driver.name);
	ret = platform_driver_register(&plat_button_driver);
	if (ret) {
		printk(KERN_ERR "Platform driver register error\n");
		return ret;
	}

	return 0;
}

static void __exit button_exit(void)
{
	platform_driver_unregister(&plat_button_driver);
}

module_init(button_init);
module_exit(button_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Fabien Marteau <fabien.marteau@armadeus.com>");
MODULE_DESCRIPTION("Wishbone button IP generic driver");
