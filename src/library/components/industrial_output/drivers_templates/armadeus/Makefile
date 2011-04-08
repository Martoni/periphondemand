#
# Makefile for the Armadeus FPGA led driver
#

ifneq ($(KERNELRELEASE),)

obj-$(CONFIG_POD_DRIVERS)	+= board_output.o goutput.o

else

ARMADEUS_BASE_DIR=../../../../../..
include $(ARMADEUS_BASE_DIR)/Makefile.in

KDIR := $(ARMADEUS_LINUX_DIR)
PWD  := $(shell pwd)


default:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules

test:
	~/armadeus/buildroot/build_arm/staging_dir/bin/arm-linux-gcc -Wall testled.c -o testled
	chmod 755 testled

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

