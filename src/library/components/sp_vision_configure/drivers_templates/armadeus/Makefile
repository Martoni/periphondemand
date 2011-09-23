#
# Makefile for the Armadeus FPGA loader driver
#

ifneq ($(KERNELRELEASE),)

obj-$(CONFIG_ARMADEUS_FPGA_POD_SPVISION_PROBER_DRIVER) += pod_sploader_prober.o

# Part executed when called from standard make in this directory:
# (preferably use Makefile in parent directory)

else
ARMADEUS_BASE_DIR=../../../../../../
include $(ARMADEUS_BASE_DIR)/Makefile.in
KDIR := $(ARMADEUS_KERNEL_DIR)
PWD	 := $(shell pwd)
CC:=$(ARMADEUS_TOOLCHAIN_PATH)/arm-linux-gcc

default:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) clean
	rm -f modules.order Module.markers
 
endif

