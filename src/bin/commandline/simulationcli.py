#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     SimulationCli.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  08/07/2008
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

__version__ = "1.0.0"
__versionTime__ = "08/07/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import periphondemand.bin.define
from   periphondemand.bin.define import *
from   periphondemand.bin.utils.basecli           import BaseCli

from   periphondemand.bin.utils.error    import Error
from   periphondemand.bin.utils.settings import Settings
from   periphondemand.bin.utils.display  import Display

from   periphondemand.bin.toolchain.simulation import Simulation

settings = Settings()
display  = Display()

class SimulationCli(BaseCli):
    """
    """

    def __init__(self,parent=None):
        BaseCli.__init__(self,parent)

    def complete_selecttoolchain(self,text,line,begidx,endidx):
        list = []
        try:
            list = self.completeargs(text,line,"[simulationtoolchain]")
        except Exception,e:
            print e
        return list

    def do_selecttoolchain(self,line):
        """\
Usage : selecttoolchain [simulationtoolchain]
select toolchain used for simulation
        """
        try:
            self.checkargs(line,"[simulationtoolchain]")
        except Error,e:
            print e
            return

        if line.strip() == "":
            if len(settings.active_project.getSimulationToolChainList())==1:
                settings.active_project.setSimulationToolChain(
                    settings.active_project.getSimulationToolChainList()[0])
            else:
                if settings.active_project.getSimulationToolChain() == None:
                    print "Choose a toolchain\n"
                    for toolchain in \
                            settings.active_project.getSimulationToolChainList():
                        print toolchain
                    return
        else:
            try:
                settings.active_project.setSimulationToolChain(line)
            except Error,e:
                print e
                return

    def do_generateproject(self,line):
        """\
Usage : generateproject
Make projects files for simulation (makefile and testbench sources)
        """
        self.do_generatetestbench(line)
        self.do_generatemakefile(line)



    def do_generatetestbench(self,line):
        """\
Usage : generatetestbench
Make a template for testbench simulation
        """
        if line.strip() != "":
            try:
                self.do_selecttoolchain(line)
            except Error,e:
                print e
                return
        elif settings.active_project.simulation == None:
            print Error("Simulation toolchain must be selected before")
            return

        if settings.active_project.getSimulationToolChain() == None:
            print Error("Choose a toolchain before",0)
            for toolchain in settings.active_project.getSimulationToolChainList():
                print toolchain.getName()
            return
        try:
            filename = settings.active_project.simulation.generateTemplate()
        except Error,e:
            print e
            return
        print display
        print "Testbench with name : "+filename+" Done"

    def do_generatemakefile(self,line):
        """\
Usage : generatemakefile
Make a Makefile to ease simulation
        """
        if line.strip() != "":
            try:
                self.do_selecttoolchain(line)
            except Error,e:
                print e
                return
        elif settings.active_project.simulation == None:
            print Error("simulation toolchain must be selected before")
            return

        if settings.active_project.getSimulationToolChain() == None:
            print Error("Choose a toolchain before")
            for toolchain in settings.active_project.getSimulationToolChainList():
                print toolchain.getName()
            return
        try:
            filename = settings.active_project.simulation.generateMakefile()
        except Error,e:
            print e
            return
        print display
        print "Makefile generated with name : "+filename+" Done"



if __name__ == "__main__":
    print "SimulationCli class test\n"
    print SimulationCli.__doc__

