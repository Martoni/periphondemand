#
# Makefile for the Armadeus Wb_button drivers
#

BASE_DIR="../../../../../buildroot/"

REL=`grep "BR2_PACKAGE_LINUX_VERSION=" $(BASE_DIR).config | \
      sed "s/BR2_PACKAGE_LINUX_VERSION=\\"//" | sed "s/\\"//"`

ARMADEUS_KERNEL_DIR=$(BASE_DIR)build_arm/linux-$(REL)

ifneq ($(KERNELRELEASE),)

obj-$(CONFIG_POD_DRIVERS)	+= board_buttons.o gbutton.o

# Part executed when called from standard make in this directory:
# (preferably use Makefile in parent directory)

else

KDIR    := $(ARMADEUS_KERNEL_DIR)
PWD	:= $(shell pwd)

default:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules
	-cp button.ko /tftpboot/

test:
	~/armadeus/buildroot/build_arm/staging_dir/bin/arm-linux-gcc testbutton.c -o testbutton
	chmod 755 testbutton

clean:
	rm -f *.*o \
	rm -f Module.symvers

endif

