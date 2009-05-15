/* a program to write/read values on fpga address map
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
#include <fcntl.h>

/* as name said */
#include <signal.h>

/* sleep */
#include <unistd.h>

int fled;

void quit(int pouet){
  close(fled);
  exit(0);
}

int main(int argc, char *argv[])
{
  unsigned short i,j;

  /* quit when Ctrl-C pressed */
  signal(SIGINT, quit);

  j=0;

  printf( "Testing button driver\n" );

  if(argc < 2){
    perror("invalide arguments number\ntestled <button_filename>\n");
    exit(EXIT_FAILURE);
  }

  fled=open(argv[1],O_RDWR);
  if(fled<0){
    perror("can't open file\n");
    exit(EXIT_FAILURE);
  }

  while(1){
    i = (i==0)?1:0;
    fflush(stdout);

    /* read value */
    if(read(fled,&j,1)<0){
      perror("read error\n");
      exit(EXIT_FAILURE);
    }
    printf("Read %d\n",j);

    if(lseek(fled,0,SEEK_SET)<0){
      perror("lseek error\n");
      exit(EXIT_FAILURE);
    }
  }

  close(fled);
  exit(0);
}

