/*
 * Driver for the IRQ manager (OpenCore/Wishbone based) IP
 *
 * (C) Copyright 2008-2011 ARMadeus Systems
 * Author: Julien Boibessot <julien.boibessot@armadeus.com>
 *
 * Inspired of linux/arch/arm/mach-imx/irq.c
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */

/*#define DEBUG*/

#include <linux/module.h>
#include <linux/init.h>
#include <linux/list.h>
#include <linux/timer.h>
#include <linux/interrupt.h>
#include <linux/platform_device.h>
#include <linux/version.h>
#if LINUX_VERSION_CODE > KERNEL_VERSION(2,6,29)
#include <linux/slab.h>		/* kmalloc */
#endif

#include <mach/hardware.h>
#include <mach/irqs.h>
#include <asm/irq.h>
#include <asm/io.h> /* readb() & Co */
#include <asm/mach/irq.h>

#include "irq_mng.h"

#ifndef CONFIG_MACH_APF9328
# include <mach/fpga.h> /* To remove when MX1 platform is merged */
#endif

#define ID_OFFSET	(0x02 *(16/8))
#define NB_IT		16
#define FPGA_IMR	0x00 /* Interrupt Mask Register relative @*/
#define FPGA_ISR	0x02 /* Interrupt Status Register relative @*/

#define DRIVER_NAME	"ocore_irq_mng"

struct irq_mng {
	void *membase;
	struct resource *mem_res;
	struct resource *irq_res;
};

#if LINUX_VERSION_CODE <= KERNEL_VERSION(2,6,36)
struct irq_mng global_mng;
#endif


static int imx_fpga_irq_type(unsigned int _irq, unsigned int type)
{
	return 0;
}

#if LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)
static void imx_fpga_ack_irq(struct irq_data *data)
{
	struct irq_mng *mng = irq_data_get_irq_chip_data(data);
	unsigned int irq = data->irq;
#else
static void imx_fpga_ack_irq(unsigned int irq)
{
	struct irq_mng *mng = &global_mng;
#endif
	int shadow;

	shadow = 1 << ((irq - IRQ_FPGA_START) % NB_IT);
	pr_debug("%s: irq %d ack:0x%x\n", __FUNCTION__, irq, shadow);
	writew(shadow, mng->membase + FPGA_ISR);
}

#if LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)
static void imx_fpga_mask_irq(struct irq_data *data)
{
	struct irq_mng *mng = irq_data_get_irq_chip_data(data);
	unsigned int irq = data->irq;
#else
static void imx_fpga_mask_irq(unsigned int irq)
{
	struct irq_mng *mng = &global_mng;
#endif
	int shadow;

	shadow = readw(mng->membase + FPGA_IMR);
	shadow &= ~( 1 << ((irq - IRQ_FPGA_START) % NB_IT));
	pr_debug("%s: irq %d mask:0x%x\n", __FUNCTION__, irq, shadow);
	writew(shadow, mng->membase + FPGA_IMR);
}

#if LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)
static void imx_fpga_unmask_irq(struct irq_data *data)
{
	struct irq_mng *mng = irq_data_get_irq_chip_data(data);
	unsigned int irq = data->irq;
#else
static void imx_fpga_unmask_irq(unsigned int irq)
{
	struct irq_mng *mng = &global_mng;
#endif
	int shadow;

	shadow = readw(mng->membase + FPGA_IMR);
	shadow |= 1 << ((irq - IRQ_FPGA_START) % NB_IT);
	pr_debug("%s: irq %d mask:0x%x\n", __FUNCTION__, irq, shadow);
	writew(shadow, mng->membase + FPGA_IMR);
}

static irqreturn_t ocore_irq_mng_interrupt(int irq, void *data)
{
	struct irq_mng *mng = data;
	struct irq_desc *desc;
	unsigned int mask;

	mask = readw(mng->membase + FPGA_ISR);
	irq = IRQ_FPGA_START;

	pr_debug("%s: mask:0x%04x\n", __FUNCTION__, mask);
#if LINUX_VERSION_CODE > KERNEL_VERSION(2,6,29)
	desc = irq_to_desc(irq);
#else
	desc = irq_desc + irq;
#endif
	/* handle irqs */
	while (mask) {
		if (mask & 1) {
			pr_debug("handling irq %d 0x%08x\n", irq,
					(unsigned int)desc);
			desc_handle_irq(irq, desc);
		}
		irq++;
		desc++;
		mask >>= 1;
	}

	return IRQ_HANDLED;
}

static struct irq_chip imx_fpga_chip = {
	.name		= "FPGA",
#if LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)
	.irq_ack	= imx_fpga_ack_irq,
	.irq_mask	= imx_fpga_mask_irq,
	.irq_unmask	= imx_fpga_unmask_irq,
#else
	.ack		= imx_fpga_ack_irq,
	.mask		= imx_fpga_mask_irq,
	.unmask		= imx_fpga_unmask_irq,
#endif
	.set_type	= imx_fpga_irq_type,
};

#ifdef CONFIG_PM
static int ocore_irq_mng_suspend(struct platform_device *pdev, pm_message_t state)
{
	dev_dbg(&pdev->dev, "suspended\n");

	return 0;
}

static int ocore_irq_mng_resume(struct platform_device *pdev)
{
	dev_dbg(&pdev->dev, "resumed\n");

	return 0;
}
#else
# define ocore_irq_mng_suspend NULL
# define ocore_irq_mng_resume NULL
#endif /* CONFIG_PM */

static int __devinit ocore_irq_mng_probe(struct platform_device *pdev)
{
	struct ocore_irq_mng_pdata *pdata = pdev->dev.platform_data;
	unsigned int irq;
	u16 id;
	int ret = 0;
	struct resource *mem_res;
	struct resource *irq_res;
	struct irq_mng *mng;

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

	mem_res = request_mem_region(mem_res->start, resource_size(mem_res), pdev->name);
	if (!mem_res) {
		dev_err(&pdev->dev, "iomem already in use\n");
		return -EBUSY;
	}

	/* allocate memory for private structure */
#if LINUX_VERSION_CODE > KERNEL_VERSION(2,6,36)
	mng = kmalloc(sizeof(struct irq_mng), GFP_KERNEL);
#else
	mng = &global_mng;
#endif
	if (!mng) {
		ret = -ENOMEM;
		goto out_release_mem;
	}

	mng->membase = ioremap(mem_res->start, resource_size(mem_res));
	if (!mng->membase) {
		dev_err(&pdev->dev, "ioremap failed\n");
		ret = -ENOMEM;
		goto out_dev_free;
	}
	mng->mem_res = mem_res;
	mng->irq_res = irq_res;

	/* check if ID is correct */
	id = readw(mng->membase + ID_OFFSET);
	if (id != pdata->idnum) {
		printk(KERN_WARNING "For irq_mngr id:%d doesn't match with id"
			"read %d,\n is device present ?\n", pdata->idnum, id);
		ret = -ENODEV;
		goto out_iounmap;
	}

	/* Mask all interrupts initially */
	writew(0, mng->membase + FPGA_IMR);

	for (irq = IRQ_FPGA(0); irq < IRQ_FPGA(NB_IT); irq++) {
		printk("IRQ %d\n", irq);
		set_irq_chip_data(irq, mng);
		set_irq_chip_and_handler(irq, &imx_fpga_chip, handle_edge_irq);
		set_irq_flags(irq, IRQF_VALID);
	}
	/* clear pending interrupts */
	writew(0xffff, mng->membase + FPGA_ISR);

	ret = request_irq(mng->irq_res->start, ocore_irq_mng_interrupt,
				IRQF_SAMPLE_RANDOM, "ocore_irq_mng", mng);

	if (ret < 0) {
		printk(KERN_ERR "Can't register irq %d\n",
			   mng->irq_res->start);
		goto request_irq_error;
	}

	pr_debug("FPGA IRQs initialized (Parent=%d)\n", mng->irq_res->start);

	return 0;

request_irq_error:
out_iounmap:
	iounmap(mng->membase);
out_dev_free:
	kfree(mng);
out_release_mem:
	release_mem_region(mem_res->start, resource_size(mem_res));

	return ret;
}

static int __devexit ocore_irq_mng_remove(struct platform_device *pdev)
{
	struct ocore_irq_mng_pdata *pdata = pdev->dev.platform_data;
	struct irq_mng *mng = (*pdata).mng;
	unsigned int irq;

	for (irq = IRQ_FPGA(0); irq < IRQ_FPGA(NB_IT); irq++) {
		set_irq_chip(irq, NULL);
		set_irq_handler(irq,NULL);
		set_irq_flags(irq, 0);
	}
	free_irq(mng->irq_res->start, mng);
	release_mem_region(mng->mem_res->start, resource_size(mng->mem_res));
	iounmap(mng->membase);
	kfree(mng);

	return 0;
}

static struct platform_driver ocore_irq_mng_driver = {
	.probe      = ocore_irq_mng_probe,
	.remove     = ocore_irq_mng_remove,
	.suspend    = ocore_irq_mng_suspend,
	.resume     = ocore_irq_mng_resume,
	.driver     = {
		.name   = DRIVER_NAME,
	},
};

static int __init ocore_irq_mng_init(void)
{
	return platform_driver_register(&ocore_irq_mng_driver);
}

static void __exit ocore_irq_mng_exit(void)
{
	platform_driver_unregister(&ocore_irq_mng_driver);
}

module_init(ocore_irq_mng_init);
module_exit(ocore_irq_mng_exit);

MODULE_AUTHOR("Julien Boibessot, <julien.boibessot@armadeus.com>");
MODULE_DESCRIPTION("Armadeus OpenCore IRQ manager");
MODULE_LICENSE("GPL");

