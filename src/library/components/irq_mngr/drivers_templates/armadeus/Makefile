#
# Makefile for the Armadeus FPGA OpenCore IRQ manager IP
#

ifneq ($(KERNELRELEASE),)

# Part executed when called from kernel build system:

obj-$(CONFIG_POD_DRIVERS) += irq_ocore.o board_irq_mng.o
irq_ocore-objs	:= main.o

else

ARMADEUS_BASE_DIR=../../../../../..
include $(ARMADEUS_BASE_DIR)/Makefile.in

KDIR := $(ARMADEUS_LINUX_DIR)
PWD  := $(shell pwd)

# Armadeus custom drivers common targets (default, clean, etc...)
include ../../../Makefile.in

endif

