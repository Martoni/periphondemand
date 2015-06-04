#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Synthesis.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/05/2008
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
""" Synthesis toolchain """

import sys

from periphondemand.bin.define import SYNTHESISPATH
from periphondemand.bin.define import XMLEXT
from periphondemand.bin.define import TOOLCHAINPATH
from periphondemand.bin.define import COMPONENTSPATH

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.display import Display

SETTINGS = Settings()
DISPLAY = Display()


class Synthesis(WrapperXml):
    """ Manage synthesis
    """

    def __init__(self, parent):
        self.parent = parent
        filepath = SETTINGS.projectpath +\
            "/" + SYNTHESISPATH +\
            "/synthesis" + XMLEXT
        if not sy.fileExist(filepath):
            raise PodError("No synthesis project found", 3)
        WrapperXml.__init__(self, file=filepath)
        # adding path for toolchain plugin
        sys.path.append(SETTINGS.path + TOOLCHAINPATH +
                        SYNTHESISPATH + "/" + self.name)

    def save(self):
        """ Save xml """
        self.saveXml(SETTINGS.projectpath +
                     "/synthesis/synthesis" + XMLEXT)

    @property
    def synthesis_toolname(self):
        """ return synthesis tool name """
        return self.getAttributeValue(key="name", subnodename="tool")

    @property
    def synthesis_toolcommandname(self):
        """ Test if command exist and return it """
        try:
            # try if .podrc exists
            return SETTINGS.get_synthesis_tool_command(
                self.synthesis_toolname)
        except PodError:
            # else use toolchain default
            command_name = self.getAttributeValue(key="command",
                                                  subnodename="tool")
            command_path = self.getAttributeValue(key="default_path",
                                                  subnodename="tool")
            command_name = command_path + "/" + command_name
            if not sy.commandExist(command_name):
                raise PodError("Synthesis tool tcl shell command named " +
                               command_name + " doesn't exist in PATH")
            return command_name

    def generate_project(self):
        """ copy all hdl file in synthesis project directory
        """
        for component in self.parent.instances:
            if component.num == "0":
                # Make directory
                compdir = SETTINGS.projectpath +\
                    SYNTHESISPATH + "/" +\
                    component.name
                if sy.dirExist(compdir):
                    DISPLAY.msg("Directory " + compdir +
                                " exist, will be deleted")
                    sy.delDirectory(compdir)
                sy.makeDirectory(compdir)
                DISPLAY.msg("Make directory for " + component.name)
                # copy hdl files
                for hdlfile in component.hdl_files:
                    try:
                        sy.copyFile(
                            SETTINGS.projectpath +
                            COMPONENTSPATH + "/" +
                            component.instancename +
                            "/hdl/" + hdlfile.filename,
                            compdir + "/")
                    except IOError, error:
                        print DISPLAY
                        raise PodError(str(error), 0)

    def generate_tcl(self, filename=None):
        """ generate tcl script to drive synthesis tool """
        try:
            plugin = __import__(self.name)
        except ImportError, error:
            sys.path.remove(SETTINGS.path + TOOLCHAINPATH +
                            SYNTHESISPATH + "/" + self.name)
            raise PodError(str(error), 0)
        sys.path.append(SETTINGS.path + TOOLCHAINPATH +
                        SYNTHESISPATH + "/" + self.name)
        filename = plugin.generate_tcl(self)
        self.tcl_scriptname = str(filename)
        return None

    @property
    def tcl_scriptname(self):
        """ get the tcl script filename """
        try:
            return self.getAttributeValue(key="filename",
                                          subnodename="script")
        except PodError:
            raise PodError("TCL script must be generated before")

    @tcl_scriptname.setter
    def tcl_scriptname(self, filename):
        """ set the tcl script filename """
        if self.getNode("script") is None:
            self.addNode(nodename="script",
                         attributename="filename",
                         value=str(filename))
        else:
            self.setAttribute(key="filename",
                              value=filename,
                              subname="script")

    def generate_pinout(self, filename):
        """ Generate pinout constraints file """
        try:
            plugin = __import__(self.name)
        except ImportError, error:
            sy.delFile(SETTINGS.path + TOOLCHAINPATH +
                       SYNTHESISPATH + "/" + self.name)
            raise PodError(str(error))
        sy.delFile(SETTINGS.path + TOOLCHAINPATH +
                   SYNTHESISPATH + "/" + self.name)

        plugin.generate_pinout(self, filename)
        return None

    def generate_bitstream(self):
        """ Generate the bitstream for fpga configuration """
        try:
            plugin = __import__(self.name)
        except ImportError, error:
            raise PodError(str(error), 0)
        scriptpath = SETTINGS.projectpath +\
            SYNTHESISPATH +\
            "/" + self.tcl_scriptname
        try:
            plugin.generate_bitstream(self,
                                      self.synthesis_toolcommandname,
                                      scriptpath)
        except PodError, error:
            raise PodError("Can't generate bitstream for this synthesis" +
                           " toolchain:" + self.synthesis_toolname +
                           ", not implemented. (" + str(error) + ")")
