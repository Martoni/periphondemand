#
# Makefile for the Armadeus Wb_button drivers
#

ifneq ($(KERNELRELEASE),)

obj-$(CONFIG_POD_DRIVERS)	+= board_input.o ginput.o

else


ARMADEUS_BASE_DIR=../../../../../..
include $(ARMADEUS_BASE_DIR)/Makefile.in

KDIR := $(ARMADEUS_LINUX_DIR)
PWD  := $(shell pwd)

default:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules

test:
	$(ARMADEUS_TOOLCHAIN_PATH)/arm-linux-gcc testbutton.c -o testbutton

clean:
	rm -f *.*o \
	rm -f *.mod.c \
	rm -f *.cmd \
	rm -f *.o.d \
	rm -f *.order \
	rm -f .*.cmd \
	rm -rf .tmp_versions \
	rm -f Module.symvers

endif

