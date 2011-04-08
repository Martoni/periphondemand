CC=arm-linux-gcc

nfs : .nfs

.nfs : i2c_testbench
	cp i2c_testbench /local/export/
	@touch $@

i2c_testbench : i2c_testbench.o i2cbusses.o
	$(CC) i2c_testbench.o i2cbusses.o -o i2c_testbench

%.o : %.c
	$(CC) -Wall $< -c

clean :
	rm *.o
	rm i2c_testbench
