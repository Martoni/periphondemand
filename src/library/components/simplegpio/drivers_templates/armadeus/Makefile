#
# Makefile for the Armadeus GPIO drivers
#

# Part executed when called from kernel build system:
ifneq ($(KERNELRELEASE),)

obj-$(CONFIG_POD_DRIVERS)	+= board_simplegpio.o gsimplegpio.o

# Part executed when called from standard make in this directory:
# (preferably use Makefile in parent directory)
else

BASE_DIR="../../../../buildroot"
REL=`grep "BR2_PACKAGE_LINUX_VERSION=" $(BASE_DIR)/.config | \
      sed "s/BR2_PACKAGE_LINUX_VERSION=\\"//" | sed "s/\\"//"`
BUILD_ARM=`ls $(BASE_DIR) | grep "^build_arm"`
ARMADEUS_KERNEL_DIR=$(BASE_DIR)/$(BUILD_ARM)/linux-$(REL)
KDIR    := $(ARMADEUS_KERNEL_DIR)
PWD	:= $(shell pwd)

default:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules

clean:
	rm -f *.*o \
	rm -f Module.symvers
	rm -f .*.cmd
	rm -f *.mod.c
	rm -rf .tmp_versions/
endif

