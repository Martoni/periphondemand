#! /usr/bin/python3
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

import importlib

SETTINGS = Settings()
DISPLAY = Display()


class Synthesis(WrapperXml):
    """ Manage synthesis
    """

    def __init__(self, parent):
        self.parent = parent
        filepath = self.parent.projectpath + \
            "/" + SYNTHESISPATH + \
            "/synthesis" + XMLEXT
        if not sy.file_exist(filepath):
            raise PodError("No synthesis project found", 3)
        WrapperXml.__init__(self, file=filepath)
        # adding path for toolchain plugin
        sys.path.append(SETTINGS.path + TOOLCHAINPATH +
                        SYNTHESISPATH + "/" + self.name)

        # specific tool instanciation
        try:
            base_lib = "periphondemand.toolchains.synthesis"
            module_name = str.upper(self.name[0]) + self.name[1:]
            module = importlib.import_module(base_lib + "." +
                                             self.name + "." +
                                             self.name)
            my_class = getattr(module, module_name)
            self._plugin = my_class(parent, self)

        except ImportError as error:
            sy.rm_file(SETTINGS.path + TOOLCHAINPATH +
                       SYNTHESISPATH + "/" + self.name)
            raise PodError(str(error))

    @property
    def plugin(self):
        """ return synthesis generator instance
        """
        return self._plugin

    def save(self):
        """ Save xml """
        self.save_xml(self.parent.projectpath +
                      "/synthesis/synthesis" + XMLEXT)

    @property
    def synthesis_toolname(self):
        """ return synthesis tool name """
        return self.get_attr_value(key="name", subnodename="tool")

    @property
    def synthesis_toolcommandname(self):
        """ Test if command exist and return it """
        try:
            # try if .podrc exists
            return SETTINGS.get_synthesis_tool_command(
                self.synthesis_toolname)
        except PodError:
            # else use toolchain default
            command_name = self.get_attr_value(key="command",
                                               subnodename="tool")
            command_path = self.get_attr_value(key="default_path",
                                               subnodename="tool")
            if command_path is not None:
                if command_path != "":
                    command_name = command_path + "/" + command_name
            if not sy.cmd_exist(command_name):
                raise PodError("Synthesis tool tcl shell command named " +
                               command_name + " doesn't exist in PATH")
            return command_name

    def get_synthesis_value(self, value):
        """ Return toolchain config content
        """
        try:
            return SETTINGS.get_synthesis_value(self.synthesis_toolname,
                                                value)
        except PodError:
            raise PodError("sais pas quoi faire")

    def generate_project(self):
        """ copy all hdl file in synthesis project directory
        """
        for component in self.parent.instances:
            if component.num == "0":
                # Make directory
                compdir = self.parent.projectpath +\
                    SYNTHESISPATH + "/" +\
                    component.name
                if sy.dir_exist(compdir):
                    DISPLAY.msg("Directory " + compdir +
                                " exist, will be deleted")
                    sy.rm_dir(compdir)
                sy.mkdir(compdir)
                DISPLAY.msg("Make directory for " + component.name)
                # copy hdl files
                for hdlfile in component.hdl_files:
                    try:
                        sy.cp_file(self.parent.projectpath +
                                   COMPONENTSPATH + "/" +
                                   component.instancename +
                                   "/hdl/" + hdlfile.filename,
                                   compdir + "/")
                    except IOError as error:
                        print(DISPLAY)
                        raise PodError(str(error), 0)

    def generate_tcl(self, filename=None):
        """ generate tcl script to drive synthesis tool """
        sys.path.append(SETTINGS.path + TOOLCHAINPATH +
                        SYNTHESISPATH + "/" + self.name)
        filename = self.plugin.generate_tcl()
        self.tcl_scriptname = str(filename)
        return None

    @property
    def tcl_scriptname(self):
        """ get the tcl script filename """
        try:
            return self.get_attr_value(key="filename",
                                       subnodename="script")
        except PodError:
            raise PodError("TCL script must be generated before")

    @tcl_scriptname.setter
    def tcl_scriptname(self, filename):
        """ set the tcl script filename """
        if self.get_node("script") is None:
            self.add_node(nodename="script",
                          attributename="filename",
                          value=str(filename))
        else:
            self.set_attr(key="filename",
                              value=filename,
                              subname="script")

    def generate_pinout(self, filename):
        """ Generate pinout constraints file """
        sy.rm_file(SETTINGS.path + TOOLCHAINPATH +
                   SYNTHESISPATH + "/" + self.name)

        print(self.plugin)
        self.plugin.generate_pinout(filename)
        return None

    def generate_bitstream(self):
        """ Generate the bitstream for fpga configuration """
        scriptpath = self.parent.projectpath + \
            SYNTHESISPATH + \
            "/" + self.tcl_scriptname
        try:
            cmd = self.synthesis_toolcommandname
            self.plugin.generate_bitstream(cmd, scriptpath)
        except PodError as error:
            raise PodError("Can't generate bitstream for this synthesis" +
                           " toolchain:" + self.synthesis_toolname +
                           ", not implemented. (" + str(error) + ")")
