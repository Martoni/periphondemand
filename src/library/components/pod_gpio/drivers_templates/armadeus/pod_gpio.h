/*
 * ARMadeus definitions for the POD component pod_gpio
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

#ifndef LINUX_pod_gpio
#define LINUX_pod_gpio

#ifndef CONFIG_MACH_APF9328
# include <mach/fpga.h> /* To remove when MX1 platform is merged */
#endif

#define IRQ_GPIO_POD(x) IRQ_FPGA(x+16)

#define pod_gpio_DRIVER_NAME "pod_gpio"

#endif
