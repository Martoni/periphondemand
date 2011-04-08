/*
 * Testing program for i2c-ocore driver
 *
 * Fabien Marteau <fabien.marteau@armadeus.com>
 *
 * Chips LIS3LV02DL (accelerometer) and DS28CZ04 (EEPROM)
 * must be present on i2c bus at addresses :
 * LIS3LV02DL : 0x1d
 * DS28CZ04   : 0x50
 *            : 0x51
 *
 * ------------------------------------------------------------------------
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation; version 2 of the License.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 * ------------------------------------------------------------------------
 */

#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "linux/i2c-dev.h"
#include "i2cbusses.h"

#define ACCELERO_ADDR 0x1d
#define EEPROM_ADDR_L 0x50
#define EEPROM_ADDR_H 0x51
#define VOID_ADDR     0x66

/* smbus_access read or write markers */
#define I2C_SMBUS_READ	1
#define I2C_SMBUS_WRITE	0


struct func
{
	long value;
	const char* name;
};

static const struct func all_func[] = {
	{ .value = I2C_FUNC_I2C,
	  .name = "I2C" },
	{ .value = I2C_FUNC_SMBUS_QUICK,
	  .name = "SMBus Quick Command" },
	{ .value = I2C_FUNC_SMBUS_WRITE_BYTE,
	  .name = "SMBus Send Byte" },
	{ .value = I2C_FUNC_SMBUS_READ_BYTE,
	  .name = "SMBus Receive Byte" },
	{ .value = I2C_FUNC_SMBUS_WRITE_BYTE_DATA,
	  .name = "SMBus Write Byte" },
	{ .value = I2C_FUNC_SMBUS_READ_BYTE_DATA,
	  .name = "SMBus Read Byte" },
	{ .value = I2C_FUNC_SMBUS_WRITE_WORD_DATA,
	  .name = "SMBus Write Word" },
	{ .value = I2C_FUNC_SMBUS_READ_WORD_DATA,
	  .name = "SMBus Read Word" },
	{ .value = I2C_FUNC_SMBUS_PROC_CALL,
	  .name = "SMBus Process Call" },
	{ .value = I2C_FUNC_SMBUS_WRITE_BLOCK_DATA,
	  .name = "SMBus Block Write" },
	{ .value = I2C_FUNC_SMBUS_READ_BLOCK_DATA,
	  .name = "SMBus Block Read" },
	{ .value = I2C_FUNC_SMBUS_BLOCK_PROC_CALL,
	  .name = "SMBus Block Process Call" },
	{ .value = I2C_FUNC_SMBUS_PEC,
	  .name = "SMBus PEC" },
	{ .value = I2C_FUNC_SMBUS_WRITE_I2C_BLOCK,
	  .name = "I2C Block Write" },
	{ .value = I2C_FUNC_SMBUS_READ_I2C_BLOCK,
	  .name = "I2C Block Read" },
	{ .value = 0, .name = "" }
};

/*
 * Print the installed i2c busses. The format is those of Linux 2.4's
 * /proc/bus/i2c for historical compatibility reasons.
 */
static void print_i2c_busses(void)
{
	struct i2c_adap *adapters;
	int count;

	adapters = gather_i2c_busses();
	if (adapters == NULL) {
		fprintf(stderr, "Error: Out of memory!\n");
		return;
	}

	for (count = 0; adapters[count].name; count++) {
		printf("i2c-%d\t%-10s\t%-32s\t%s\n",
			   adapters[count].nr, adapters[count].funcs,
			   adapters[count].name, adapters[count].algo);
	}

	free_adapters(adapters);
}

static void print_functionality(unsigned long funcs)
{
	int i;

	for (i = 0; all_func[i].value; i++) {
		printf("%-32s %s\n", all_func[i].name,
		       (funcs & all_func[i].value) ? "yes" : "no");
	}
}

static int set_i2c_slave_address(int file, int address)
{
	/* Set slave address */
	if (ioctl(file, I2C_SLAVE,address) < 0) {
		if (errno == EBUSY) {
			fprintf(stderr, "Error: i2c controler is busy\n");
			return -1;
		} else {
			fprintf(stderr, "Error: Could not set "
					"address to 0x%02x: %s\n",address,
					strerror(errno));
			return -1;
		}
	}
	return 0;
}

int main(int argc, char *argv[])
{
	int i2cbus;
	int ret;
	char filename[20];
	int file;
	unsigned long funcs;
	__s32 int_read;
	__u8  int_write;
	__u16 word_write;
	__s32 word_read;
	__u8 block[20];
	__u8  command;

	printf("* Testing program for i2c-ocore driver *\n");

	/* check args */
	if (argc <  2) {
		fprintf(stderr, "Please select the bus number:\n");
		print_i2c_busses();
		exit(1);
	}

	/* check bus number */
	i2cbus = lookup_i2c_bus(argv[1]);
	if (i2cbus < 0) {
		fprintf(stderr, "Wrong i2c bus number\n");
		exit(1);
	}

	/* open bus */
	file = open_i2c_dev(i2cbus, filename, 0);
	if (file < 0) {
		exit(1);
	}

	/* test adapter */
	if (ioctl(file, I2C_FUNCS, &funcs) < 0) {
		fprintf(stderr, "Error: Could not get the adapter "
			"functionality matrix: %s\n", strerror(errno));
		close(file);
		exit(1);
	}

	/* print functionnalities */
	print_functionality(funcs);
	printf("\n");

	/****************************************/
	/* I2C                              no  */

    /****************************************/
	/* SMBus Quick Command              yes */
	printf("* SMBus Quick Command\n");
	ret = set_i2c_slave_address(file,ACCELERO_ADDR);
	if (ret < 0)
		goto error;

	printf("write read bit test :\n");
	ret = i2c_smbus_write_quick(file,I2C_SMBUS_WRITE);
	if(ret < 0)
		goto error;
	printf("ok for accelero\n");
	/* write quick a 0 bit block some i2c slave component (LIS3LV02DL)
	ret = i2c_smbus_write_quick(file,I2C_SMBUS_READ);
	if(ret < 0)
		goto error;*/

	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_write_quick(file,I2C_SMBUS_WRITE);
	if(ret < 0)
		goto error;
	printf("ok for EEPROM_L\n");
	/* write quick a 0 bit block some i2c slave component (LIS3LV02DL)
	ret = i2c_smbus_write_quick(file,I2C_SMBUS_READ);
	if(ret < 0)
		goto error;*/

    /****************************************/
	/* SMBus Receive Byte               yes */
	printf("\n* SMBus Receive Byte:\n");
	ret = set_i2c_slave_address(file,ACCELERO_ADDR);
	if (ret < 0)
		goto error;
	int_read = i2c_smbus_read_byte(file);
	if (int_read < 0)
		goto error;
	printf("Read %02x on Accelerometer\n",int_read);
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	int_read = i2c_smbus_read_byte(file);
	if (int_read < 0)
		goto error;
	printf("Read %02x on EEPROM_L\n",int_read);

    /****************************************/
	/* SMBus Send Byte                  yes */
	int_write = 0x55;
	printf("\n* SMBus Send Byte:\n");
	ret = set_i2c_slave_address(file,ACCELERO_ADDR);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_write_byte(file,int_write);
	if (ret < 0)
		goto error;
	printf("Write %02x on Accelerometer\n",int_write);
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_write_byte(file,int_write);
	if (ret < 0)
		goto error;
	printf("Write %02x on EEPROM_L\n",int_write);


    /****************************************/
	/* SMBus Write Byte (data)          yes */
	command = 0x16; /* accelero calibration register */
	int_write = 0x55;
	printf("\n* SMBus Write Byte (data):\n");
	ret = set_i2c_slave_address(file,ACCELERO_ADDR);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_write_byte_data(file,command,int_write);
	if (ret < 0)
		goto error;
	printf("Write %02x at %02x on Accelerometer\n",int_write,command);

	command = 0x7a; /* EEPROM direction PIO */
	int_write = 0x40; /* select EEPROM in SMBus Mode */
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_write_byte_data(file,command,int_write);
	if (ret < 0)
		goto error;
	printf("Write %02x at %02x on EEPROM_L\n",int_write,command);

	command = 0x10; /* EEPROM*/
	int_write = 0x55;
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_write_byte_data(file,command,int_write);
	if (ret < 0)
		goto error;
	printf("Write %02x at %02x on EEPROM_L\n",int_write,command);

	sleep(1);/* wait for write completion */

    /****************************************/
	/* SMBus Read Byte  (data)          yes */
	printf("\n* SMBus Read Byte (data):\n");
	command = 0x16;
	ret = set_i2c_slave_address(file,ACCELERO_ADDR);
	if (ret < 0)
		goto error;
	int_read = i2c_smbus_read_byte_data(file,command);
	if (int_read < 0)
		goto error;
	printf("Read %02x at %02x on Accelerometer\n",int_read,command);
	command = 0x7a;
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	int_read = i2c_smbus_read_byte_data(file,command);
	if (int_read < 0)
		goto error;
	printf("Read %02x at %02x on EEPROM_L\n",int_read,command);
	command = 0x10;
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	int_read = i2c_smbus_read_byte_data(file,command);
	if (int_read < 0)
		goto error;
	printf("Read %02x at %02x on EEPROM_L\n",int_read,command);

    /****************************************/
	/* SMBus Write Word                 yes */
	printf("\n* SMBus Write Word :\n");
	command = 0x10; /* EEPROM*/
	word_write = 0x5555;
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_write_word_data(file,command,word_write);
	if (ret < 0)
		goto error;
	printf("Write %04x at %02x on EEPROM_L\n",word_write,command);
	sleep(1);
	command = 0x12; /* EEPROM*/
	word_write = 0xcaca;
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_write_word_data(file,command,word_write);
	if (ret < 0)
		goto error;
	printf("Write %04x at %02x on EEPROM_L\n",word_write,command);
	sleep(1);

    /****************************************/
	/* SMBus Read Word                  yes */
	printf("\n* SMBus Read Word :\n");
	command = 0x10;
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	word_read = i2c_smbus_read_word_data(file,command);
	if (word_read < 0)
		goto error;
	printf("Read %04x at %02x on EEPROM_L\n",word_read,command);
	command = 0x12;
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	word_read = i2c_smbus_read_word_data(file,command);
	if (word_read < 0)
		goto error;
	printf("Read %04x at %02x on EEPROM_L\n",word_read,command);
	command = 0x11;
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	word_read = i2c_smbus_read_word_data(file,command);
	if (word_read < 0)
		goto error;
	printf("Read %04x at %02x on EEPROM_L\n",word_read,command);

    /****************************************/
	/* SMBus Process Call               no  */
    /****************************************/
	/* SMBus Block Write                no  */
    /****************************************/
	/* SMBus Block Read                 no  */
    /****************************************/
	/* SMBus Block Process Call         no  */
    /****************************************/
	/* SMBus PEC                        no  */

    /****************************************/
	/* I2C Block Write                  yes */
	printf("\n* SMBus i2c Block Write :\n");
	command = 0x16;
	block[0]= 0x11;
	block[1]= 0x22;
	block[2]= 0x33;
	ret = set_i2c_slave_address(file,ACCELERO_ADDR);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_write_i2c_block_data(file,command,3,block);
	if (ret < 0)
		goto error;
	printf("write %02x%02x%02x at %02x on ACCELERO\n",block[0],
													 block[1],
													 block[2],
													 command);

    /****************************************/
	/* I2C Block Read                   yes */
	printf("\n* SMBus i2c Block Read :\n");
	command = 0x16;
	ret = set_i2c_slave_address(file,ACCELERO_ADDR);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_read_i2c_block_data(file,command,3,block);
	if (ret < 0)
		goto error;
	printf("Read %02x%02x%02x at %02x on ACCELERO\n",block[0],
													 block[1],
													 block[2],
													 command);
	command = 0x10;
	ret = set_i2c_slave_address(file,EEPROM_ADDR_L);
	if (ret < 0)
		goto error;
	ret = i2c_smbus_read_i2c_block_data(file,command,3,block);
	if (ret < 0)
		goto error;
	printf("Read %02x%02x%02x at %02x on EEPROM\n",block[0],
													 block[1],
													 block[2],
													 command);


	close(file);
	return 0;
error:
	fprintf(stderr,"Error on i2c bus\n");
	close(file);
	return 0;
}

