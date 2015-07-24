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
from periphondemand.bin.core.hdl_file import HdlFile

settings = Settings()
display = Display()
ONETAB = "    "


def needqsys(self):
    for component in self.parent.instances:
        qsys_node = component.get_nodes("qsys")
        if not (len(qsys_node) == 0):
            return 1
    return 0


def generateQsysScript(self):
    project_name = "imx6_sp_wrapper_qsys"

    platform = settings.active_project.platform
    out = "\n"
    out += "package require -exact qsys 12.0\n"
    out += "# module properties ('module' here means 'system' " + \
        "or 'top level module')\n"
    out += "set_module_property NAME {" + project_name + "}\n"
    out += "set_module_property GENERATION_ID {0x00000000}\n"
    out += "\n"
    out += "# project properties\n"
    out += "set_project_property DEVICE_FAMILY {" + platform.family + "}\n"
    out += "set_project_property DEVICE {" + platform.device + "}\n"
    out += "\n"
    out += "# instances and instance parameters\n"

    for component in self.parent.instances:
        qsys_node = component.get_nodes("qsys")
        if not (len(qsys_node) == 0):
            qsys_components = qsys_node[0].get_subnodes("qsys_components",
                                                        "qsys_component")
            for qsys_component in qsys_components:
                instance_name = qsys_component.get_attr_value("instance_name")
                out += "add_instance " + instance_name + \
                    " " + qsys_component.get_attr_value("name") + "\n"
                for parameter in qsys_component.get_nodes("parameter"):
                    out += "set_instance_parameter_value " + instance_name + \
                        " " + parameter.get_attr_value("name") + \
                        " {" + parameter.text + "}\n"

            out += "\n"
            out += "# connections and connection parameters"
            out += "\n"
            qsys_connections = qsys_node[0].get_subnodes("connections",
                                                         "connection")
            for connection in qsys_connections:
                src_inst = connection.get_attr_value("src")
                dest_inst = connection.get_attr_value("dest")
                out += "add_connection " + src_inst + " " + dest_inst + "\n"
                for parameter in connection.get_nodes("parameter"):
                    out += "set_connection_parameter_value " + src_inst + \
                        "/" + dest_inst + " " + parameter.get_attr_value("name") + \
                        " {" + parameter.text + "}\n"

            out += "\n"
            out += "# exported interfaces"
            out += "\n"

            exports = qsys_node[0].get_subnodes("exports", "export")
            for export in exports:
                export_name = export.get_attr_value("name")
                out += "add_interface " + export_name + " " + \
                    export.get_attr_value("type") + "\n"
                out += "set_interface_property " + export_name + \
                    " EXPORT_OF " + export.get_attr_value("src") + "\n"

    out += "\n"
    out += "# disabled instances\n"

    out += "save_system " + project_name + ".qsys\n"
    tclfile = open(settings.projectpath + SYNTHESISPATH + "/" +
                   project_name + ".tcl", "w")
    tclfile.write(out)


def generatepinoutContent(self):
    out = ""
    for interface in self.project.platform.interfaces:
        for port in interface.ports:
            port_standard = port.get_attr_value("standard")
            if port.force_defined():
                out = out + ONETAB + 'set_location_assignment ' + \
                    str(port.position) + \
                    ' -to force_' + str(port.name) + ";\n"
            else:
                for pin in port.pins:
                    if pin.connections != []:
                        connect = pin.connections
                        out = out + ONETAB + 'set_location_assignment ' + \
                            port.position + " -to " + \
                            connect[0]["instance_dest"] + "_" + \
                            connect[0]["port_dest"]
                        if self.project.get_instance(
                            connect[0]["instance_dest"]).get_interface(
                                connect[0]["interface_dest"]).get_port(
                                    connect[0]["port_dest"]).size != "1":
                            out = out + "[" + connect[0]["pin_dest"] + "]"
                        out = out + ';\n'
                        out = out + "set_instance_assignment "
                        out = out + '-name IO_STANDARD "'+port_standard
                        out = out + '" -to ' + connect[0]["instance_dest"] + \
                            "_" + connect[0]["port_dest"] + ";\n"

    return out


def generate_pinout(self, filename=None):
    """ Generate the constraint file in tcl for quartus fpga
    """
    if filename is None:
        filename = settings.projectpath + \
            SYNTHESISPATH + "/" + \
            settings.active_project.name + "_pinout" + TCLEXT
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
        filename = settings.active_project.name + TCLEXT
    self.project = settings.active_project
    tclfile = open(settings.projectpath + SYNTHESISPATH + "/" + filename, "w")
    tclfile.write("# TCL script automaticaly generated by POD\n")
    tclfile.write("cd .." + OBJSPATH + "\n")
    tclfile.write("# Pinout file, automatical ienerated by pod\n")
    tclfile.write("package require ::quartus::project\n")
    tclfile.write("package require ::quartus::flow\n")
    tclfile.write("project_new -revision " +
                  " top_" + settings.active_project.name +
                  " top_" + settings.active_project.name + "\n")
    tclfile.write("# configure platform params\n")
    platform = settings.active_project.platform
    tclfile.write("set_global_assignment -name FAMILY \"" +
                  platform.family + "\"\n")
    tclfile.write("set_global_assignment -name DEVICE " +
                  platform.device + "\n")
    # tclfile.write("project set package "+platform.package+"\n")
    # tclfile.write("project set speed "+platform.speed+"\n")
    # tclfile.write("project set {Preferred Language} VHDL\n")
    # tclfile.write('project set "Create Binary Configuration File" TRUE\n');
    tclfile.write("set_global_assignment -name TOP_LEVEL_ENTITY top_"
                  + settings.active_project.name + "\n")

    # Source files
    tclfile.write("## add components sources file\n")
    tclfile.write("# add top level sources file\n")
    tclfile.write("set_global_assignment -name VHDL_FILE .." +
                  SYNTHESISPATH + "/top_" +
                  settings.active_project.name + VHDLEXT + "\n")

    for directory in sy.list_dir(settings.projectpath + SYNTHESISPATH):
        for file in sy.list_files(settings.projectpath +
                                  SYNTHESISPATH +
                                  "/" + directory):
            tclfile.write("set_global_assignment -name VHDL_FILE .." +
                          SYNTHESISPATH + "/" + directory +
                          "/" + file + "\n")

    if needqsys(self):
        generateQsysScript(self)
        tclfile.write("set_global_assignment -name QSYS_FILE " +
                      ".." + SYNTHESISPATH + "/imx6_sp_wrapper_qsys.qsys\n")

    tclfile.write(generatepinoutContent(self))
    # Commit assignments
    tclfile.write("export_assignments\n")
    tclfile.write("execute_flow -compile\n")

    # Close project
    tclfile.write("project_close\n")
    display.msg("TCL script generated with name : " +
                settings.active_project.name + TCLEXT)
    return settings.active_project.name + TCLEXT


def launch_as_shell(self, commandname, option):
    for line in sy.launch_as_shell(commandname, option):
        if settings.color() == 1:
            print COLOR_SHELL + line + COLOR_END,
        else:
            print "SHELL>" + line,


def generate_bitstream(self, commandname, scriptname):
    """ generate the bitstream """
    pwd = sy.pwd()
    sy.del_all(settings.projectpath + OBJSPATH)
    sy.chdir(settings.projectpath + SYNTHESISPATH)
    commandname = commandname + " -t "

    launch_as_shell(self, commandname, scriptname)
    try:
        print(settings.projectpath + OBJSPATH + "/" +
              BINARY_PREFIX + settings.active_project.name +
              ALTERA_BITSTREAM_SUFFIX)
        sy.copyFile(settings.projectpath + OBJSPATH + "/" +
                    BINARY_PREFIX + settings.active_project.name +
                    ALTERA_BITSTREAM_SUFFIX,
                    settings.projectpath + BINARYPROJECTPATH + "/")
    except IOError:
        raise PodError("Can't copy bitstream")
    sy.chdir(pwd)
