/*
 * ARMadeus driver for the POD component anybus_interface
 *
 * (C) Copyright 2011 - Armadeus Systems <support@armadeus.com>
 * Author: Kevin JOLY joly.kevin25@gmail.com
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

#include <linux/platform_device.h>
#include <linux/cdev.h>
#include <linux/io.h>
#include <linux/fs.h>
#include <linux/mm.h>
#include <linux/slab.h>

#include "pod_anybus_interface.h"

#define ANYBUS_ID_REGISTER 0x00

struct anybus_device {
	struct class *anybus_class;
	void __iomem *reg_base;
	struct cdev *cdev;
	unsigned long start_register;
} *anybus_dev;

static u16 pod_anybus_interface_read_reg(int reg)
{
	return ioread16(anybus_dev->reg_base + reg);
}

static int mmap_anybus(struct file *file, struct vm_area_struct *vma)
{
	vma->vm_pgoff = anybus_dev->start_register >> PAGE_SHIFT;

	vma->vm_page_prot = pgprot_noncached(vma->vm_page_prot);

	if (remap_pfn_range(vma, vma->vm_start, vma->vm_pgoff,vma->vm_end - vma->vm_start, vma->vm_page_prot)) {
		return -EAGAIN;
	}

	return 0;
}

static const struct file_operations anybus_fops = {
	.mmap = mmap_anybus,
};

static int pod_anybus_interface_probe(struct platform_device *pdev)
{
	struct resource *resource_memory, *resource_irq;
	/*struct anybus_device *anybus_dev;*/
	u16 id;
	/*struct cdev *cdev = cdev_alloc();*/
	int err;

	resource_memory = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	resource_irq = platform_get_resource(pdev, IORESOURCE_IRQ, 0);

	if (!resource_memory) {
		err = -ENODEV;
		dev_err(&pdev->dev, "Device Anybus not found\n");
		goto exit;
	}

	anybus_dev = kzalloc(sizeof(struct anybus_device), GFP_KERNEL);
	anybus_dev->reg_base = ioremap_nocache(resource_memory->start, resource_size(resource_memory));
	anybus_dev->start_register = resource_memory->start;

	/*dev_set_drvdata(&pdev->dev, anybus_dev);*/

	if (!request_mem_region(resource_memory->start,
	resource_size(resource_memory), ANYBUS_INTERFACE_DRIVER_NAME)) {
		dev_err(&pdev->dev, "Can't request memory region %x to %x\n",
		resource_memory->start, resource_memory->start +
			resource_memory->end);
		err = -ENOMEM;
		goto exit_free;
	}

	/*Check if ID is correct*/
	id = pod_anybus_interface_read_reg(ANYBUS_ID_REGISTER);
	if (pdev->id != id) {
		dev_err(&pdev->dev,
			"Driver id %d doesn't match with the device id %d\n",
			pdev->id, id);
		err = -ENODEV;
		goto exit_iounmap;
	}

	anybus_dev->cdev = cdev_alloc();
	err = alloc_chrdev_region(&anybus_dev->cdev->dev, 1, 1, ANYBUS_INTERFACE_DRIVER_NAME);
	if (err) {
		dev_err(&pdev->dev, "Unable to allocate device numbers\n");
		goto exit_iounmap;
	}

	anybus_dev->cdev->owner = THIS_MODULE;
	anybus_dev->cdev->ops = &anybus_fops;
	err = cdev_add(anybus_dev->cdev, anybus_dev->cdev->dev, 256);
	if(err) {
		dev_err(&pdev->dev, "Unable to add cdev\n");
		goto exit_unreg;
	}

	anybus_dev->anybus_class = class_create(THIS_MODULE, ANYBUS_INTERFACE_DRIVER_NAME);
	if (IS_ERR(anybus_dev->anybus_class)) {
		dev_err(&pdev->dev, "Unable to create anybus class device\n");
		err = PTR_ERR(anybus_dev->anybus_class);
		goto exit_unreg;
	}

	if(device_create(anybus_dev->anybus_class, NULL, anybus_dev->cdev->dev, NULL, ANYBUS_INTERFACE_DRIVER_NAME) == NULL) {
		dev_err(&pdev->dev, "Unable to create device\n");
		goto exit_class_destroy;
	}

	dev_info(&pdev->dev, "Anybus interface probed.\n");

	return 0;

exit_class_destroy :
	class_destroy(anybus_dev->anybus_class);
exit_unreg :
	unregister_chrdev_region(anybus_dev->cdev->dev, 1);
exit_iounmap:
	iounmap(anybus_dev->reg_base);
	release_mem_region(resource_memory->start,
				resource_size(resource_memory));
exit_free:
	kfree(anybus_dev);
exit:
	return err;
}

static int pod_anybus_interface_remove(struct platform_device *pdev)
{
	struct resource *resource_memory, *resource_irq;
	/*struct anybus_device *anybus_dev = dev_get_drvdata(&pdev->dev);*/

	device_destroy(anybus_dev->anybus_class, anybus_dev->cdev->dev);
	class_destroy(anybus_dev->anybus_class);
	unregister_chrdev_region(anybus_dev->cdev->dev, 1);

	resource_memory = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	resource_irq = platform_get_resource(pdev, IORESOURCE_IRQ, 0);

	iounmap(anybus_dev->reg_base);

	release_mem_region(resource_memory->start,
		resource_size(resource_memory));

	dev_set_drvdata(&pdev->dev, NULL);

	return 0;
}

static struct platform_driver pod_anybus_interface_drv = {
	.driver = {
		.name = ANYBUS_INTERFACE_DRIVER_NAME,
		.owner = THIS_MODULE,
	},
	.probe = pod_anybus_interface_probe,
	.remove = pod_anybus_interface_remove
};

static int __init pod_anybus_interface_init(void)
{
	return platform_driver_register(&pod_anybus_interface_drv);
}
module_init(pod_anybus_interface_init);

static void __exit pod_anybus_interface_exit(void)
{
	platform_driver_unregister(&pod_anybus_interface_drv);
}
module_exit(pod_anybus_interface_exit);

MODULE_AUTHOR("Kevin Joly <joly.kevin25@gmail.com>");
MODULE_DESCRIPTION("Driver for anybus_interface component of POD");
MODULE_LICENSE("GPL");
