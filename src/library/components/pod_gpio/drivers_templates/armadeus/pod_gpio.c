/*
 * ARMadeus driver for the POD component pod_gpio
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

#include <linux/gpio.h>
#include <linux/io.h>
#include <linux/platform_device.h>
#include <linux/slab.h>
#include <linux/irq.h>
#include <linux/interrupt.h>

#include "pod_gpio.h"

#define GPIO_ID 0x00
#define GPIO_CONFIG 0x02
#define GPIO_VALUE 0x04
#define GPIO_ENABLE_INTERRUPT 0x06
#define GPIO_INTERRUPT_STATUS 0x08
#define GPIO_INTERRUPT_EDGE_TYPE 0x0A

struct pod_gpio_chip {
	struct gpio_chip chip;
	struct irq_chip interrupt_chip;
	struct platform_device *pdev;
	void __iomem *reg_base;
	int irq_base;
};

static u16 cg_read_reg(const struct pod_gpio_chip *cg_chip, int reg)
{
	return ioread16(cg_chip->reg_base + reg);
}

static void cg_write_reg(const struct pod_gpio_chip *cg_chip, int reg,
			 u16 val)
{
	iowrite16(val, cg_chip->reg_base + reg);
}

static void pod_gpio_ack_irq(struct irq_data *data)
{
	struct irq_chip *chip = get_irq_chip(data->irq);
	struct pod_gpio_chip *cg_chip =
		container_of(chip, struct pod_gpio_chip, interrupt_chip);

	cg_write_reg(cg_chip , GPIO_INTERRUPT_STATUS,
					(1 << (data->irq - IRQ_GPIO_POD(0))));
}

static void pod_gpio_mask_irq(struct irq_data *data)
{
	struct irq_chip *chip = get_irq_chip(data->irq);
	struct pod_gpio_chip *cg_chip =
		container_of(chip, struct pod_gpio_chip, interrupt_chip);

	u16 enable_interrupt_config;
	enable_interrupt_config = cg_read_reg(cg_chip, GPIO_ENABLE_INTERRUPT);

	cg_write_reg(cg_chip , GPIO_ENABLE_INTERRUPT, enable_interrupt_config &
					~(1 << (data->irq - IRQ_GPIO_POD(0))));
}

static void pod_gpio_unmask_irq(struct irq_data *data)
{
	struct irq_chip *chip = get_irq_chip(data->irq);
	struct pod_gpio_chip *cg_chip =
		container_of(chip, struct pod_gpio_chip, interrupt_chip);

	u16 enable_interrupt_config;
	enable_interrupt_config = cg_read_reg(cg_chip, GPIO_ENABLE_INTERRUPT);

	cg_write_reg(cg_chip, GPIO_ENABLE_INTERRUPT, enable_interrupt_config |
					(1 << (data->irq - IRQ_GPIO_POD(0))));
}

static int pod_gpio_irq_type(unsigned int _irq, unsigned int type)
{
	struct irq_chip *chip = get_irq_chip(_irq);
	struct pod_gpio_chip *cg_chip =
			container_of(chip, struct pod_gpio_chip,
							interrupt_chip);
	u16 edge_config;

	edge_config = cg_read_reg(cg_chip, GPIO_INTERRUPT_EDGE_TYPE);

	/* Only falling and rising edge are supporter by pod_gpio */
	if (type == IRQ_TYPE_EDGE_RISING) {
		cg_write_reg(cg_chip, GPIO_INTERRUPT_EDGE_TYPE, edge_config |
					(1 << (_irq - IRQ_GPIO_POD(0))));
	} else if (type == IRQ_TYPE_EDGE_FALLING) {
		cg_write_reg(cg_chip, GPIO_INTERRUPT_EDGE_TYPE, edge_config &
					~(1 << (_irq - IRQ_GPIO_POD(0))));
	} else {
		dev_err(&cg_chip->pdev->dev,
		"The selected edge type is not supported by the driver.\n");
		return -EINVAL;
	}

	return 0;
}

static irqreturn_t pod_gpio_interrupt(int irq, void *data)
{
	struct pod_gpio_chip *cg_chip = data;
	struct irq_desc *desc;
	u16 pending_interrupts;

	irq = IRQ_GPIO_POD(0);
	desc = irq_to_desc(irq);

	pending_interrupts = cg_read_reg(cg_chip, GPIO_INTERRUPT_STATUS);

	while (pending_interrupts) {
		if (pending_interrupts & 1) {
			/* Get irq handle */
			desc_handle_irq(irq, desc);
		}
		irq++;
		desc++;
		pending_interrupts >>= 1;
	}

	return IRQ_HANDLED;
}

static int pod_gpio_get(struct gpio_chip *chip, unsigned gpio_num)
{
	struct pod_gpio_chip *cg_chip =
			container_of(chip, struct pod_gpio_chip, chip);
		u16 io_config;

	io_config = cg_read_reg(cg_chip, GPIO_CONFIG) | (1 << gpio_num);

	if (cg_read_reg(cg_chip, GPIO_VALUE) & (1 << gpio_num))
		return 1;
	else
		return 0;
}

static int pod_gpio_direction_in(struct gpio_chip *chip,
						unsigned gpio_num)
{
	struct pod_gpio_chip *cg_chip =
			container_of(chip, struct pod_gpio_chip, chip);
	u16 io_config;

	io_config = cg_read_reg(cg_chip, GPIO_CONFIG) | (1 << gpio_num);
	cg_write_reg(cg_chip, GPIO_CONFIG, io_config);

	return 0;
}

static void pod_gpio_set(struct gpio_chip *chip, unsigned gpio_num,
					int val)
{
	struct pod_gpio_chip *cg_chip =
			container_of(chip, struct pod_gpio_chip, chip);
	u16 io_value;

	if (val == 1)
		io_value = cg_read_reg(cg_chip, GPIO_VALUE) | (1 << gpio_num);
	else
		io_value = cg_read_reg(cg_chip, GPIO_VALUE) & ~(1 << gpio_num);

	cg_write_reg(cg_chip, GPIO_VALUE, io_value);
}

static int pod_gpio_direction_out(struct gpio_chip *chip,
						unsigned gpio_num, int val)
{
	struct pod_gpio_chip *cg_chip =
			container_of(chip, struct pod_gpio_chip, chip);
	u16 io_config;

	io_config = cg_read_reg(cg_chip, GPIO_CONFIG) & ~(1 << gpio_num);
	cg_write_reg(cg_chip, GPIO_CONFIG, io_config);

	return 0;
}

static int pod_gpio_to_irq(struct gpio_chip *chip, unsigned offset)
{

	struct pod_gpio_chip *cg_chip =
			container_of(chip, struct pod_gpio_chip, chip);


	return cg_chip->irq_base + offset;
}

static int pod_gpio_probe(struct platform_device *pdev)
{
	int err;
	struct pod_gpio_chip *cg_chip;
	struct resource *resource_memory, *resource_irq;
	unsigned int irq;
	u16 id;

	resource_memory = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	resource_irq = platform_get_resource(pdev, IORESOURCE_IRQ, 0);

	if (!resource_memory || !resource_irq) {
		err = -ENODEV;
		dev_err(&pdev->dev, "Device pod_gpio not found\n");
		goto exit;
	}

	if (!request_mem_region(resource_memory->start,
	resource_size(resource_memory), pod_gpio_DRIVER_NAME)) {
		dev_err(&pdev->dev, "Can't request memory region %x to %x\n",
		resource_memory->start, resource_memory->start +
			resource_memory->end);
		err = -ENOMEM;
		goto exit;
	}

	/*Allocate memory for pod_gpio chip*/
	cg_chip = kzalloc(sizeof(struct pod_gpio_chip), GFP_KERNEL);
	if (!cg_chip) {
		err = -ENOMEM;
		dev_err(&pdev->dev,
			"Can't allocate memory for pod_gpio_chip\n");
		goto release_region;
	}

	dev_set_drvdata(&pdev->dev, cg_chip);

	/*Chip configuration*/
	cg_chip->chip.label		= pod_gpio_DRIVER_NAME;
	cg_chip->chip.owner		= THIS_MODULE;
	cg_chip->chip.ngpio		= 16;
	cg_chip->chip.base		= -1;
	cg_chip->chip.get		= pod_gpio_get;
	cg_chip->chip.direction_input	= pod_gpio_direction_in;
	cg_chip->chip.set		= pod_gpio_set;
	cg_chip->chip.direction_output	= pod_gpio_direction_out;
	cg_chip->chip.to_irq		= pod_gpio_to_irq;
	cg_chip->irq_base		= IRQ_GPIO_POD(0);
	cg_chip->pdev			= pdev;

	/*Interrupt chip configuration*/
	cg_chip->interrupt_chip.name = pod_gpio_DRIVER_NAME;
	cg_chip->interrupt_chip.irq_ack = pod_gpio_ack_irq;
	cg_chip->interrupt_chip.irq_mask = pod_gpio_mask_irq;
	cg_chip->interrupt_chip.irq_unmask = pod_gpio_unmask_irq;
	cg_chip->interrupt_chip.set_type = pod_gpio_irq_type;

	/* Add virtual interrupts from GPIO*/
	for (irq = IRQ_GPIO_POD(0) ; irq < IRQ_GPIO_POD(16) ; irq++) {
		set_irq_chip_data(irq, cg_chip);
		set_irq_chip_and_handler(irq, &cg_chip->interrupt_chip,
							handle_edge_irq);
		set_irq_flags(irq, IRQF_VALID);
	}

	cg_chip->reg_base = ioremap_nocache(resource_memory->start,
					resource_size(resource_memory));

	if (!cg_chip->reg_base) {
		err = -EIO;
		goto free_chip;
	}

	/*Check if ID is correct*/
	id = cg_read_reg(cg_chip, GPIO_ID);
	if (pdev->id != id) {
		dev_err(&pdev->dev,
			"Driver id %d doesn't match with the device id %d\n",
			pdev->id, id);
		err = -ENODEV;
		goto exit_iounmap;
	}

	/* Clear all pending interrupts */
	cg_write_reg(cg_chip, GPIO_INTERRUPT_STATUS, 0xFF);

	/* Disable all interrupts */
	cg_write_reg(cg_chip, GPIO_ENABLE_INTERRUPT, 0x00);

	/* Add the GPIO chip*/
	err = gpiochip_add(&cg_chip->chip);
	if (err) {
		dev_err(&pdev->dev, "Can't add the gpio chip\n");
		goto exit_iounmap;
	}

	/* Request irq pin */
	err = request_irq(resource_irq->start, pod_gpio_interrupt,
			0 , "pod_gpio", cg_chip);

	if (err) {
		dev_err(&pdev->dev, "Can't request irq %d\n",
					resource_irq->start);
		goto exit_iounmap;
	}

	dev_info(&pdev->dev, "pod_gpio probed. GPIO used: %d..%d\n",
	cg_chip->chip.base, cg_chip->chip.base + cg_chip->chip.ngpio-1);

	return 0;

 exit_iounmap:
	iounmap(cg_chip->reg_base);
free_chip:
	kfree(cg_chip);
release_region:
	release_mem_region(resource_memory->start,
				resource_size(resource_memory));
exit:
return err;
}

static int pod_gpio_remove(struct platform_device *pdev)
{
	struct resource *resource_memory, *resource_irq;
	struct pod_gpio_chip *cg_chip = dev_get_drvdata(&pdev->dev);
	unsigned int irq;

	/* Remove the GPIO chip */
	if (gpiochip_remove(&cg_chip->chip))
		dev_err(&pdev->dev, "gpio_chip remove failed\n");

	if (cg_chip->reg_base)
		iounmap(cg_chip->reg_base);

	kfree(cg_chip);

	resource_memory = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	resource_irq = platform_get_resource(pdev, IORESOURCE_IRQ, 0);

	release_mem_region(resource_memory->start,
		resource_size(resource_memory));

	for (irq = IRQ_GPIO_POD(0) ; irq < IRQ_GPIO_POD(16) ; irq++) {
		set_irq_chip(irq, NULL);
		set_irq_handler(irq, NULL);
		set_irq_flags(irq, 0);
	}

	free_irq(resource_irq->start, cg_chip);

	dev_set_drvdata(&pdev->dev, NULL);

	return 0;
}

static struct platform_driver pod_gpio_drv = {
	.driver = {
		.name = pod_gpio_DRIVER_NAME,
		.owner = THIS_MODULE,
	},
	.probe = pod_gpio_probe,
	.remove = pod_gpio_remove,
};

static int __init pod_gpio_init(void)
{
	return platform_driver_register(&pod_gpio_drv);
}
module_init(pod_gpio_init);

static void __exit pod_gpio_exit(void)
{
	platform_driver_unregister(&pod_gpio_drv);
}
module_exit(pod_gpio_exit);

MODULE_AUTHOR("Kevin Joly <joly.kevin25@gmail.com>");
MODULE_DESCRIPTION("GPIO driver for pod_gpio component of POD");
MODULE_LICENSE("GPL");
