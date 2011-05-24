/*
 * Platform data for IRQ manager generic driver
 *
 * (c) Copyright 2011    The Armadeus Project - ARMadeus Systems
 * Author: Julien Bibessot <julien.boibessot@armadeus.com>
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

#ifndef __IRQ_MNG_H__
#define __IRQ_MNG_H__

struct ocore_irq_mng_pdata {
	int num;		/* instance number */
	int idnum;		/* identity number */
	int idoffset;		/* identity register relative address */
	struct irq_mng *mng;
};

#endif /* __IRQ_MNG_H__ */
