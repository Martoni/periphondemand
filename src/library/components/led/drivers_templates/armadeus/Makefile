#
# Makefile for the Armadeus FPGA led driver
#

ifneq ($(KERNELRELEASE),)

obj-$(CONFIG_ARMADEUS_FPGA_POD_LED_DRIVER) += pod_leds.o 

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

test:
	$(CC) $(CFLAGS) testled.c -o testled
	chmod 755 testled

clean:
	rm -f *.*o \
	rm -f Module.symvers
	rm -rf .*.cmd
	rm -f *.mod.c

endif

