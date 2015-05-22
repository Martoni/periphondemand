#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     quartus.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  21/07/2008
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
""" generate specifics scripts for Quartus """

import time
import datetime

from periphondemand.bin.define import ONETAB
from periphondemand.bin.define import SYNTHESISPATH
from periphondemand.bin.define import TCLEXT
from periphondemand.bin.define import OBJSPATH
from periphondemand.bin.define import VHDLEXT
from periphondemand.bin.define import COLOR_SHELL
from periphondemand.bin.define import COLOR_END
from periphondemand.bin.define import BINARY_PREFIX
from periphondemand.bin.define import ALTERA_BITSTREAM_SUFFIX
from periphondemand.bin.define import BINARYPROJECTPATH

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils import wrappersystem as sy

from periphondemand.bin.core.component import Component
from periphondemand.bin.core.port import Port
from periphondemand.bin.core.interface import Interface
from periphondemand.bin.core.hdl_file import Hdl_file

settings = Settings()
display = Display()
ONETAB = "    "


def generatepinoutContent(self):
    out = ""
    for interface in self.project.platform.getInterfacesList():
        for port in interface.ports:
            if port.force_defined():
                out = out + ONETAB + 'set_location_assignment ' + \
                    str(port.position) + \
                    ' -to force_' + str(port.getName()) + ";\n"
            else:
                for pin in port.pins:
                    if pin.getConnections() != []:
                        connect = pin.getConnections()
                        out = out + ONETAB + 'set_location_assignment ' + \
                            port.position + " -to " + \
                            connect[0]["instance_dest"] + "_" + \
                            connect[0]["port_dest"]
                        if self.project.get_instance(
                            connect[0]["instance_dest"]).getInterface(
                                connect[0]["interface_dest"]).getPort(
                                    connect[0]["port_dest"]).size != "1":
                            out = out + "[" + connect[0]["pin_dest"] + "]"
                        out = out + ';\n'
    return out


def generate_pinout(self, filename=None):
    """ Generate the constraint file in tcl for quartus fpga
    """
    if filename is None:
        filename = settings.projectpath + \
            SYNTHESISPATH + "/" + \
            settings.active_project.getName() + "_pinout" + TCLEXT
    self.project = settings.active_project
    out = "# Pinout file, automaticaly generated by pod\n"
    out = out + "package require ::quartus::project\n"
    out = out + generatepinoutContent(self)
    out = out + "#end\n"
    try:
        file = open(filename, "w")
    except IOError, error:
        raise PodError(str(error), 0)
    file.write(out)
    file.close()
    display.msg("Constraint file generated with name :" + filename)
    return filename


def generate_tcl(self, filename=None):
    """ generate tcl script for quartus
    """
    if filename is None:
        filename = settings.active_project.getName() + TCLEXT
    self.project = settings.active_project
    tclfile = open(settings.projectpath + SYNTHESISPATH + "/" + filename, "w")
    tclfile.write("# TCL script automaticaly generated by POD\n")
    tclfile.write("cd .." + OBJSPATH + "\n")
    tclfile.write("# Pinout file, automatical ienerated by pod\n")
    tclfile.write("package require ::quartus::project\n")
    tclfile.write("package require ::quartus::flow\n")
    tclfile.write("project_new -revision " +
                  " top_" + settings.active_project.getName() +
                  " top_" + settings.active_project.getName() + "\n")
    tclfile.write("# configure platform params\n")
    platform = settings.active_project.platform
    tclfile.write("set_global_assignment -name FAMILY \"" +
                  platform.getFamily() + "\"\n")
    tclfile.write("set_global_assignment -name DEVICE " +
                  platform.getDevice() + "\n")
    # tclfile.write("project set package "+platform.getPackage()+"\n")
    # tclfile.write("project set speed "+platform.getSpeed()+"\n")
    # tclfile.write("project set {Preferred Language} VHDL\n")
    # tclfile.write('project set "Create Binary Configuration File" TRUE\n');
    tclfile.write("set_global_assignment -name TOP_LEVEL_ENTITY top_"
                  + settings.active_project.getName() + "\n")

    # Source files
    tclfile.write("## add components sources file\n")
    tclfile.write("# add top level sources file\n")
    tclfile.write("set_global_assignment -name VHDL_FILE .." +
                  SYNTHESISPATH + "/top_" +
                  settings.active_project.getName() + VHDLEXT + "\n")

    for directory in sy.listDirectory(settings.projectpath + SYNTHESISPATH):
        for file in sy.listFiles(settings.projectpath +
                                 SYNTHESISPATH +
                                 "/" + directory):
            tclfile.write("set_global_assignment -name VHDL_FILE .." +
                          SYNTHESISPATH + "/" + directory +
                          "/" + file + "\n")

    tclfile.write(generatepinoutContent(self))
    # Commit assignments
    tclfile.write("export_assignments\n")
    tclfile.write("execute_flow -compile\n")

    # Close project
    tclfile.write("project_close\n")
    display.msg("TCL script generated with name : " +
                settings.active_project.getName() + TCLEXT)
    return settings.active_project.getName() + TCLEXT


def generate_bitstream(self, commandname, scriptname):
    """ generate the bitstream """
    pwd = sy.pwd()
    sy.deleteAll(settings.projectpath + OBJSPATH)
    sy.chdir(settings.projectpath + SYNTHESISPATH)
    commandname = commandname + " -t "

    for line in sy.launchAShell(commandname, scriptname):
        if settings.color() == 1:
            print COLOR_SHELL + line + COLOR_END,
        else:
            print "SHELL>" + line,
    try:
        print(settings.projectpath + OBJSPATH + "/" +
              BINARY_PREFIX + settings.active_project.getName() +
              ALTERA_BITSTREAM_SUFFIX)
        sy.copyFile(settings.projectpath + OBJSPATH + "/" +
                    BINARY_PREFIX + settings.active_project.getName() +
                    ALTERA_BITSTREAM_SUFFIX,
                    settings.projectpath + BINARYPROJECTPATH + "/")
    except IOError:
        raise PodError("Can't copy bitstream")
    sy.chdir(pwd)
