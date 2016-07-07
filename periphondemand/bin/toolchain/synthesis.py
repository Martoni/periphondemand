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

from periphondemand.bin.define import SYNTHESISPATH
from periphondemand.bin.define import TCLEXT
from periphondemand.bin.define import OBJSPATH
from periphondemand.bin.define import VHDLEXT
from periphondemand.bin.define import COMPONENTSPATH

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.display import Display

import importlib

SETTINGS = Settings()
DISPLAY = Display()


class Synthesis(object):
    """ Synthesis tool generator
    """
    def __init__(self, parent):
        self._parent = parent
        self.project = parent
        self.tcl_scriptname = None

    @property
    def parent(self):
        """ Return parent object """
        return self._parent

    @classmethod
    def constraints_file_extension(cls):
        """ return file constraints extension
        """
        raise NotImplementedError("method must be implemented", 0)

    def project_base_creation(self):
        """ return string
            for project creation
        """
        raise NotImplementedError("method must be implemented", 0)

    def project_base_configuration(self):
        """ return basic project
            configuration
        """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def add_file_to_tcl(cls, filename):
        """ return line according to the
            synthesis tool
        """
        raise NotImplementedError("method must be implemented", 0)

    def add_constraints_file(self, filename):
        """ return line for constraints file insertion
        """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def addforcepinout(cls, port):
        """ return line for pin forced
        """
        raise NotImplementedError("method must be implemented", 0)

    def addpinconstraints(self, connect, port):
        """ return pin constraint definition
        """
        raise NotImplementedError("method must be implemented", 0)

    def addclockconstraints(self, connect, frequency):
        """ return clock constraints line definition
        """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def insert_tools_specific_commands(cls):
        """ return lines for misc stuff
            specific to a tool
        """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def insert_tools_gen_cmds(cls):
        """ return lines for bitstream generation
        """
        raise NotImplementedError("method must be implemented", 0)

    def ext_files(self):
        """ return list of bitstream files extension
        """
        raise NotImplementedError("method must be implemented", 0)

    def generate_bitstream(self):
        """ generate the bitstream """
        raise NotImplementedError("method must be implemented", 0)

    def generatelibraryconstraints(self):
        """ Adds constraints specified by a component,
            such as placement for a PLL,
            multiplier, etc. or clock informations
            about PLL output signals
        """
        out = "# components constraints \n"
        for instance in self.project.instances:
            for constraint in instance.constraints:
                instance_name = instance.instancename
                attr_val = str(constraint.get_attr_value("name"))
                if constraint.get_attr_value("type") == "clk":
                    out += "NET \"" + instance_name + "/" + attr_val + \
                           "\" TNM_NET = " + instance_name + "/" +\
                           attr_val + ";\n"
                    out += "TIMESPEC TS_" + instance_name + "_" + \
                           attr_val.replace('/', '_') + " = PERIOD \"" + \
                           instance_name + "/" + attr_val + "\""
                    out += " %g" %\
                        (1000 /
                            float(constraint.get_attr_value("frequency"))) + \
                        " ns HIGH 50%;\n"
                elif constraint.get_attr_value("type") == "placement":
                    out += "INST \"" + instance_name + "/" +\
                        attr_val + "\" LOC=" +\
                        constraint.get_attr_value("loc") + ";\n"
                else:
                    raise PodError("component " + instance.name +
                                   " has an unknown type " +
                                   constraint.get_attr_value("type"), 0)
        return out

    def generate_pinout(self, filename=None):
        """ Generate the constraint file .ucf for xilinx fpga
        """
        if filename is None:
            filename = self.project.projectpath + SYNTHESISPATH + "/" + \
                self.project.name + "." + \
                self.constraints_file_extension()

        out = "# Constraint file, automaticaly generated by pod \n"
        out += self.generatepinoutcontent()

        try:
            afile = open(filename, "w")
        except IOError as error:
            raise PodError(str(error), 0)
        afile.write(out)
        afile.close()
        DISPLAY.msg("Constraint file generated with name : " + filename)
        return filename

    def generatepinoutcontent(self):
        """ generate pinout definition
            constraints
        """
        out = ""
        for interface in self.project.platform.interfaces:
            for port in interface.ports:
                if port.force_defined():
                    out += self.addforcepinout(port)
                elif port.pins != []:
                    pin = port.pins
                    # Platform ports are all 1-sized, raise error if not
                    if len(pin) != 1:
                        raise PodError("Platform port " + port.name +
                                       " has size different of 1", 0)
                    pin = pin[0]
                    # Only one connection per platform pin can be branched.
                    # If several connections found, only first is used
                    if pin.connections != []:
                        # XXX use getConnectedPinList
                        connect = pin.connections
                        if len(connect) > 1:
                            same_connections_ports = []
                            DISPLAY.msg("severals pin connected to " +
                                        port.name, 2)
                            for connection in connect:
                                DISPLAY.msg("      -> " +
                                            connection["instance_dest"] +
                                            "." +
                                            connection["interface_dest"] +
                                            "." +
                                            connection["port_dest"] + "." +
                                            connection["pin_dest"])
                                same_connections_ports.append(
                                    connection["instance_dest"] + "_" +
                                    connection["port_dest"])

                            same_connections_ports.sort()
                            for connection in connect:
                                if connection["instance_dest"] +\
                                        "_" + connection["port_dest"] ==\
                                        same_connections_ports[0]:
                                    connect = connection
                            DISPLAY.msg("Connection name: " +
                                        connect["instance_dest"] +
                                        "." +
                                        connect["interface_dest"] +
                                        "." +
                                        connect["port_dest"] + "." +
                                        connect["pin_dest"], 3)
                        else:
                            connect = connect[0]

                        out += self.addpinconstraints(connect, port)

                        # if port as frequency parameters, it's a clock.
                        # then had xilinx clock constraint
                        try:
                            frequency = port.frequency
                            out += self.addclockconstraints(connect, frequency)
                        except PodError:
                            pass

        out += self.generatelibraryconstraints()
        return out

    def generate_tcl(self, filename=None):
        """ generate tcl script
        """
        if filename is None:
            filename = self.project.name + TCLEXT

        tclfile = open(self.project.projectpath + SYNTHESISPATH + "/" +
                       filename, "w")
        tclfile.write("# TCL script automaticaly generated by POD\n")
        # create project
        tclfile.write("cd .." + OBJSPATH + "\n")
        tclfile.write(self.project_base_creation())

        # Configuration
        tclfile.write("# configure platform params\n")
        tclfile.write(self.project_base_configuration())

        # Source files
        tclfile.write("## add components sources file\n")
        tclfile.write("# add top level sources file\n")
        tclfile.write(self.add_file_to_tcl(".." + SYNTHESISPATH + "/top_" +
                      self.project.name + VHDLEXT))

        for directory in sy.list_dir(self.project.projectpath + SYNTHESISPATH):
            for afile in sy.list_files(self.project.projectpath +
                                       SYNTHESISPATH + "/" + directory):
                tclfile.write(self.add_file_to_tcl(".." + SYNTHESISPATH + "/" +
                              directory + "/" + afile))

        # Constraints files
        tclfile.write("# add constraint file\n")
        tclfile.write(self.add_constraints_file(SYNTHESISPATH + "/" +
                                                self.project.name))
        tclfile.write(self.insert_tools_specific_commands())

        tclfile.write(self.insert_tools_gen_cmds())

        DISPLAY.msg("TCL script generated with name : " +
                    self.project.name + TCLEXT)

        self.tcl_scriptname = self.project.name + TCLEXT
        return self.tcl_scriptname

    @property
    def synthesis_toolcommandname(self):
        """ Test if command exist and return it """
        try:
            # try if .podrc exists
            return SETTINGS.get_synthesis_tool_command(
                self.name)
        except PodError:
            return self.SYNTH_CMD

    def get_synthesis_value(self, value):
        """ Return toolchain config content
        """
        return SETTINGS.get_synthesis_value(self.name, value)

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

#    def generate_pinout(self, filename):
#        """ Generate pinout constraints file """
#        sy.rm_file(SETTINGS.path + TOOLCHAINPATH +
#                   SYNTHESISPATH + "/" + self.name)
#
#        self.generate_pinout(filename)
#        return None


def synthesis_factory(parent, toolchainname):
    """ return the toolchain object """
    base_lib = "periphondemand.toolchains.synthesis"
    module_name = str.upper(toolchainname[0]) + toolchainname[1:]
    module = importlib.import_module(base_lib + "." + toolchainname + "." +
                                     toolchainname)
    my_class = getattr(module, module_name)

    return my_class(parent)
