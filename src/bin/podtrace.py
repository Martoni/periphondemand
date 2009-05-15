#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     podtrace.py
# Purpose:  
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  12/09/2008
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

__doc__ = ""
__version__ = "1.0.0"
__versionTime__ = "12/09/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import trace, sys, os

from periphondemand.bin.commandline   import Cli
from periphondemand.bin.utils         import Settings
from periphondemand.bin.utils         import wrappersystem as sy
from periphondemand.bin.define import POD_PATH

def main():
    CLI = Cli()
    SETTINGS = Settings()
    SETTINGS.path = os.path.expanduser(POD_PATH)
    SETTINGS.projectpath = sy.pwd() 
    # load command file if in command params
    if len(sys.argv)==2:
        CLI.do_source(sys.argv[1])
    # infinite command loop
    CLI.cmdloop()

if __name__ == "__main__":
    scriptname = (sys.argv[1]).split("/")[-1]
    tracer = trace.Trace(ignoredirs= [sys.prefix, sys.exec_prefix],
                                     trace=0,
                                     count=1,
                                     outfile=r'./coverage/'+scriptname+r'/counts')
    tracer.run('main()')
    r = tracer.results()
    r.write_results(show_missing=True, coverdir=r'./coverage/'+scriptname)
    os.system("cd "+"coverage/"+scriptname+"; ../../cover2html.py ")
