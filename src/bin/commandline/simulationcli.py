#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     SimulationCli.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  08/07/2008
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
""" Command line for simulation environement """

from periphondemand.bin.utils.basecli import BaseCli

from periphondemand.bin.utils.error import PodError
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.display import Display

from periphondemand.bin.toolchain.simulation import Simulation

SETTINGS = Settings()
DISPLAY = Display()


class SimulationCli(BaseCli):
    """ Commands line for simulation environment
    """

    def __init__(self, parent=None):
        BaseCli.__init__(self, parent)

    def complete_selecttoolchain(self, text, line, begidx, endidx):
        alist = []
        try:
            alist = self.completeargs(text, line,
                                      "[simulationtoolchain]")
        except PodError, error:
            print(str(error))
        return alist

    def do_selecttoolchain(self, line):
        """\
Usage : selecttoolchain [simulationtoolchain]
select toolchain used for simulation
        """
        try:
            self.checkargs(line, "[simulationtoolchain]")
        except PodError, error:
            print(str(error))
            return

        if line.strip() == "":
            if len(SETTINGS.active_project.get_simulation_toolchains()) == 1:
                SETTINGS.active_project.simulation_toolchain =\
                    SETTINGS.active_project.get_simulation_toolchains()[0]
            else:
                if SETTINGS.active_project.simulation_toolchain is None:
                    print "Choose a toolchain\n"
                    for toolchain in \
                          SETTINGS.active_project.get_simulation_toolchains():
                        print(str(toolchain))
                    return
        else:
            try:
                SETTINGS.active_project.simulation_toolchain = line
            except PodError, error:
                print(str(error))
                return

    def do_generateproject(self, line):
        """\
Usage : generateproject <simulationtoolchain>
Make projects files for simulation (makefile and testbench sources)
        """
        if line.strip() != "":
            try:
                self.do_selecttoolchain(line)
            except PodError, error:
                print(str(error))
                return
        elif SETTINGS.active_project.simulation is None:
            print PodError("Simulation toolchain must be selected before")
            return

        if SETTINGS.active_project.simulation_toolchain is None:
            print PodError("Choose a toolchain before", 0)
            for toolchain in \
                    SETTINGS.active_project.get_simulation_toolchains():
                print(str(toolchain.getName()))
            return
        try:
            filename = SETTINGS.active_project.simulation.generateTemplate()
            filename = SETTINGS.active_project.simulation.generateMakefile()
        except PodError, error:
            print(str(error))
            return
        print(str(DISPLAY))
        print("Testbench with name : " + filename + " Done")
        print("Makefile generated with name : " + filename + " Done")

if __name__ == "__main__":
    print "SimulationCli class test\n"
    print SimulationCli.__doc__
