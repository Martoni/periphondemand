#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     DriverCli.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  16/07/2008
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
""" Commandline for driver environment """

from periphondemand.bin.utils.basecli import BaseCli
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils import wrappersystem as sy

DISPLAY = Display()


class DriverCli(BaseCli):
    """ Manage driver command line environment
    """

    def __init__(self, parent, project=None):
        BaseCli.__init__(self, parent, project)
        self.driver = self._project.driver

    def testIfToolChainSelected(self):
        """ test if toolchain selected """
        if self.driver is None:
            raise PodError("No toolchain selected " +
                           "(use selecttoolchain command)")

    def complete_generateproject(self, text, line, begidx, endidx):
        """ complete generate project """
        toollist = []
        try:
            toollist = self.completeargs(text, line, "[drivertoolchain]")
        except PodError as error:
            print(error)
        return toollist

    def do_generateproject(self, line):
        """\
Usage : generateproject
generate a project drivers directory with templates
        """
        try:
            self.testIfToolChainSelected()
            self.driver.generate_project()
            self.driver.fill_all_templates()
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def do_filltemplates(self, line):
        """\
Usage : filltemplates
fill drivers templates
        """
        try:
            self.testIfToolChainSelected()
            self.driver.fill_all_templates()
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def do_copydrivers(self, line):
        """\
Usage : copydrivers
copy drivers file in software developpement tree. Developpement tree
directory must be selected with setprojecttree
        """
        try:
            self.testIfToolChainSelected()
            self.driver.copy_bsp_drivers()
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_selectprojecttree(self, text, line, begidx, endidx):
        """complete selectprojecttree command directories """
        path = line.split(" ")[1]
        if path.find("/") == -1:  # sub
            path = ""
        elif text.split() == "":  # sub/sub/
            path = "/".join(path) + "/"
        else:  # sub/sub
            path = "/".join(path.split("/")[0:-1]) + "/"
        listdir = sy.list_dir(path)
        return self.completelist(line, text, listdir)

    def do_selectprojecttree(self, line):
        """\
Usage : setprojecttree [directory]
select software developpement tree, to copy driver
        """
        try:
            self.testIfToolChainSelected()
            self.driver.set_bsp_directory(line)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_selecttoolchain(self, text, line, begidx, endidx):
        toolchainlist = []
        try:
            toolchainlist = self.completeargs(text, line, "[drivertoolchain]")
        except PodError as error:
            print(error)
        return toolchainlist

    def do_selecttoolchain(self, line):
        """\
Usage : selecttoolchain [drivertoolchain]
select operating system to generate drivers
        """
        try:
            self.checkargs(line, "[drivertoolchain]")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        if line.strip() == "":
            if len(self._project.get_driver_toolchains()) == 1:
                self._project.driver_toolchain =\
                    self._project.get_driver_toolchains()[0]
            else:
                if self._project.driver_toolchain is None:
                    print("Choose a toolchain\n")
                    for toolchain in \
                            self._project.get_driver_toolchains():
                        print(toolchain)
                    return
        else:
            try:
                self._project.driver_toolchain = line
            except PodError as error:
                print(error)
                return
        self.driver = self._project.driver
