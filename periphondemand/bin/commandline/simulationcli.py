#! /usr/bin/python3
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
# pylint: disable=W0613
# ----------------------------------------------------------------------------
""" Command line for simulation environement """

from periphondemand.bin.utils.basecli import BaseCli

from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.display import Display

SETTINGS = Settings()
DISPLAY = Display()


class SimulationCli(BaseCli):
    """ Commands line for simulation environment
    """

    def __init__(self, parent=None, project=None):
        BaseCli.__init__(self, parent, project)

    def complete_selecttoolchain(self, text, line, begidx, endidx):
        """ selecttoolchain command completion """
        alist = []
        try:
            alist = self.completeargs(text, line,
                                      "[simulationtoolchain]")
        except PodError as error:
            print(str(error))
        return alist

    def do_selecttoolchain(self, line):
        """\
Usage : selecttoolchain [simulationtoolchain]
select toolchain used for simulation
        """
        try:
            self.checkargs(line, "[simulationtoolchain]")
        except PodError as error:
            print(str(error))
            return

        if line.strip() == "":
            if len(self._project.get_simulation_toolchains()) == 1:
                self._project.simulation_toolchain =\
                    self._project.get_simulation_toolchains()[0]
            else:
                if self._project.simulation_toolchain is None:
                    print("Choose a toolchain\n")
                    project = self._project
                    for toolchain in \
                            project.get_simulation_toolchains():
                        print(str(toolchain))
                    return
        else:
            try:
                self._project.simulation_toolchain = line
            except PodError as error:
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
            except PodError as error:
                print(str(error))
                return
        elif self._project.simulation is None:
            print(PodError("Simulation toolchain must be selected before"))
            return

        if self._project.simulation_toolchain is None:
            print(PodError("Choose a toolchain before", 0))
            for toolchain in \
                    self._project.get_simulation_toolchains():
                print(str(toolchain.name))
            return
        try:
            filename = self._project.simulation.generate_template()
            filename = self._project.simulation.generate_makefile()
        except PodError as error:
            print(str(error))
            return
        print(str(DISPLAY))
        print("Testbench with name : " + filename + " Done")
        print("Makefile generated with name : " + filename + " Done")

if __name__ == "__main__":
    print("SimulationCli class test\n")
    print(SimulationCli.__doc__)
