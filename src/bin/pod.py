#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     pod.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  02/06/2008
# ----------------------------------------------------------------------------
#  Copyright (2008)  Armadeus Systems
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# ----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
# ----------------------------------------------------------------------------
""" Starting point of POD """

from periphondemand.bin.commandline.projectcli import ProjectCli
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.version import VERSION

import sys
import os
import getopt

SETTINGS = Settings()
TMPFILENAME = "podtmp"


def usage():
    """ print POD arg usage """
    print("""\
Usage: pod [OPTION...]

    -h, --help             give this help list
    -s, --source=filename  load a script
    -l, --load=projectname load a project
    -v, --version          print program version

Report bugs to http://periphondemand.sourceforge.net/
""")


def main(argv):
    """ Main command line prog for pod """
    try:
        opts, _ = getopt.getopt(argv[1:], "hvs:l:", ["help",
                                                     "version",
                                                     "source=",
                                                     "load="])
    except getopt.GetoptError as error:
        print(error)
        usage()
        sys.exit(2)
    options = [arg[0] for arg in opts]

    if "help" in options or "-h" in options:
        usage()
        sys.exit(0)

    if "version" in options or "-v" in options:
        print("Peripherals On Demand version " + VERSION)
        sys.exit(0)

    cli = ProjectCli()
    SETTINGS.projectpath = sy.pwd()
    SETTINGS.version = VERSION

    # load command file if in command params
    if "--source" in options or "-s" in options:
        for opt, arg in opts:
            if opt == "--source" or opt == "-s":
                argument = arg
                break
        if not os.path.exists(argument):
            print("[ERROR] script " + argument + " doesn't exist")
            usage()
            return
        cli.do_source(argument)
    elif "--load" in options or "-l" in options:
        for opt, arg in opts:
            if opt == "--load" or opt == "-l":
                argument = arg.strip('/')
                break
            if not os.path.exists(argument):
                print("[ERROR] project " + argument +
                      " doesn't exist")
                usage()
                return

        tmpfile = open(TMPFILENAME, "w")
        tmpfile.write("load " + argument)
        tmpfile.close()
        print("Loading project " + argument + " :\n")
        cli.do_source(TMPFILENAME)

    # infinite command loop
    cli.cmdloop()

if __name__ == "__main__":
    main(sys.argv)
