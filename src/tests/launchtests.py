#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     launchtests.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  19/12/2008
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
""" Launch functionnals tests """

import os  # to list directory
import re  # for regexp
import getopt  # for commands arguments
import sys  # for argv


def usage():
    """ print POD arg usage """
    print """\
Usage: launchtests [OPTION...]

    -h, --help          give this help list
    -r, --reset         reset output checker

Report bugs to http://periphondemand.sourceforge.net/
"""


def diff(output, testname):
    tmpfile = open("tmp_chk", "w")
    tmpfile.write(output)
    tmpfile.close()
    out = os.popen("diff tmp_chk " + testname).read()
    out = out.strip()
    if out != "":
        return out
    else:
        return None


def main():
    reset = None
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hr", ["help", "reset"])
    except getopt.GetoptError, error:
        print(str(error))
        usage()
        sys.exit(2)
    options = [arg[0] for arg in opts]

    if "help" in options or "-h" in options:
        usage()
        sys.exit(2)

    if "reset" in options or "-r" in options:
        reset = 1

    # list files under tests/ directory
    dirlist = os.listdir(".")

    # keep testscript only
    testlist = [test for test in dirlist if re.match("\d\d*", test)]
    testlist.sort()
    number_of_tests = int(testlist[-1][0:2])

    for i in range(number_of_tests):
        print " Test number " + str(i + 1) + " : " + testlist[i][3:],
        out = os.popen("pod -s "+testlist[i]).read()
        # if -r, create output files
        if reset:
            file_chk = open("chk_" + testlist[i], "w")
            file_chk.write(out)
            file_chk.close()
            print "chk_" + testlist[i] + " written"
        else:
            if not os.path.exists("chk_" + testlist[i]):
                print("[ERROR] chk_" + testlist[i] + " doesn't exist. " +
                      "Maybe you should use -r option to generate chk file ?")
                sys.exit(-1)
            testout = diff(out, "chk_" + testlist[i])
            if testout is None:
                print " Check"
            else:
                print " Not Check"
                print testout

if __name__ == "__main__":
    main()
