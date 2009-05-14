/* a program to write/read values on gpio
 * Fabien Marteau <fabien.marteau@armadeus.com>
 * 7 april 2008
 * fpgaaccess.h
 *
 * (c) Copyright 2008    Armadeus project
 * Fabien Marteau <fabien.marteau@armadeus.com>
 *
 * A simple driver for reading and writing on
 * fpga throught a character file /dev/fpgaaccess
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
 **********************************************************************
 */

#include <stdio.h>
#include <stdlib.h>

/* file management */
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <fcntl.h>

/* as name said */
#include <signal.h>

/* sleep */
#include <unistd.h>

/* ioctl */
#define SGPIO_IORDIRECTION (0x80048200)
#define SGPIO_IOWDIRECTION (0x40048201)

int fled;

void quit(int pouet){
    close(fled);
    exit(0);
}

int main(int argc, char *argv[])
{
    unsigned short i,j;
	int ret;

    /* quit when Ctrl-C pressed */
    signal(SIGINT, quit);

    j=0;

    printf( "Testing simpleGPIO driver\n" );

    if(argc < 2){
        perror("invalid arguments number\ntestled <simpleGPIO_filename>\n");
        exit(EXIT_FAILURE);
    }

    while(1){
        i = (i==0)?1:0;
        fflush(stdout);

        fled=open(argv[1],O_RDWR);
        if(fled<0){
            perror("can't open file \n");
            exit(EXIT_FAILURE);
        }

		/* configure i/o port */
        j = 0xfeff;
		if(ioctl(fled,SGPIO_IOWDIRECTION,j))
		{
            perror("ioctl write error\n");
            exit(EXIT_FAILURE);
        }
		ret = ioctl(fled,SGPIO_IORDIRECTION,j);
		if(ret < 0)
		{
			perror("ioctl read error\n");
			exit(EXIT_FAILURE);
		}
		printf("ioctl wrote 0x%04x\n\n",ret);


		j = 0x0001;	
		printf("write 0x%04x\n\n",j);
        if(write(fled,&j,2)<=0)
		{
            perror("write error\n");
            exit(EXIT_FAILURE);
        }
	

        /* read value, must be 0xFFFF*/
        if(read(fled,&j,2)<0){
            perror("read error\n");
            exit(EXIT_FAILURE);
        }
        printf("Read 0x%04x\n\n",j);
        close(fled);
        sleep(1);

    }

    close(fled);
    exit(0);
}
