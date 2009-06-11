/* 
 * A simple program to test Wishbone button driver
 *
 * (c) Copyright 2008    Armadeus project
 * Fabien Marteau <fabien.marteau@armadeus.com>
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

int fbutton;

void quit(int pouet) {
  close(fbutton);
  exit(0);
}

void usage(char *exe) {
  if (exe) {
    printf("\nUsage:\n");
    printf("%s <button_device>\n", exe);
  }
}

int main(int argc, char *argv[])
{
  unsigned short i, j=0;

  /* quit when Ctrl-C pressed */
  signal(SIGINT, quit);

  printf( "Testing button driver\n" );

  if (argc < 2) {
    printf("invalid arguments number\n");
    usage(argv[0]);
    exit(EXIT_FAILURE);
  }

  fbutton = open(argv[1], O_RDWR);
  if (fbutton < 0) {
    perror("can't open file");
    exit(EXIT_FAILURE);
  }

  while (1) {
    /* read value */
    if (read(fbutton, &j, 1) < 0) {
      perror("read error");
      exit(EXIT_FAILURE);
    }
    printf("Read %d\n",j);

    if (lseek(fbutton, 0, SEEK_SET) < 0) {
      perror("lseek error\n");
      exit(EXIT_FAILURE);
    }
  }

  close(fbutton);
  exit(0);
}

