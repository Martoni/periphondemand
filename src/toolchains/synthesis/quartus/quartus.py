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

import os

from periphondemand.bin.utils.synthesiswrapper import SynthesisWrapper

from periphondemand.bin.define import SYNTHESISPATH
from periphondemand.bin.define import TCLEXT
from periphondemand.bin.define import OBJSPATH
from periphondemand.bin.define import COLOR_SHELL
from periphondemand.bin.define import COLOR_END
from periphondemand.bin.define import BINARY_PREFIX
from periphondemand.bin.define import ALTERA_BITSTREAM_SUFFIX
from periphondemand.bin.define import ALTERA_BINARY_SUFFIX
from periphondemand.bin.define import BINARYPROJECTPATH

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils import wrappersystem as sy

settings = Settings()
display = Display()


class Quartus(SynthesisWrapper):
    """ Manage specific synthesis part for
        quartus toolchain
    """
    def __init__(self, project, parent):
        SynthesisWrapper.__init__(self, project, parent)

    @classmethod
    def constraints_file_extension(cls):
        return ("sdc")

    def needqsys(self):
        """ Check if design need to generate a qsys file
        """
        list_qsys_comp = []
        for component in self.project.instances:
            qsys_node = component.get_nodes("qsys")
            if not (len(qsys_node) == 0):
                list_qsys_comp.append(component)
        return list_qsys_comp

    def generate_qsys_script(self, component):
        """ Generate block design script """
        project_name = component.name + "_qsys"

        platform = self.project.platform
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

        qsys_node = component.get_nodes("qsys")
        for qsys_component in qsys_node[0].get_subnodes("qsys_components",
                                                        "qsys_component"):
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
        for connection in qsys_node[0].get_subnodes("connections",
                                                    "connection"):
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

        for export in qsys_node[0].get_subnodes("exports", "export"):
            export_name = export.get_attr_value("name")
            out += "add_interface " + export_name + " " + \
                export.get_attr_value("type") + "\n"
            out += "set_interface_property " + export_name + \
                " EXPORT_OF " + export.get_attr_value("src") + "\n"

        out += "\n"
        out += "# disabled instances\n"

        out += "save_system " + project_name + ".qsys\n"
        tclfile = open(self.project.projectpath + SYNTHESISPATH + "/" +
                       project_name + ".tcl", "w")
        tclfile.write(out)

    def add_constraints_file(self, filename):
        """ return line for constraints file insertion
        """
        out = self.add_file_to_tcl(".." + filename + ".sdc")
        return out

    @classmethod
    def addforcepinout(cls, port):
        """ return line for pin forced
        """
        out = 'set_location_assignment ' + \
            str(port.position) + \
            ' -to force_' + str(port.name) + ";\n"
        return out

    def addpinconstraints(self, connect, port, portdest):
        """ return pin constraint definition
        """
        out = ""
        tag = port.get_attr_value("tag")
        dest_conn = connect["instance_dest"] + "_" + \
            connect["port_dest"]
        if portdest.size != "1":
            dest_conn = dest_conn + "[" + connect["pin_dest"] + "]"
        if port.position is not None:
            out = out + 'set_location_assignment ' + \
                port.position + " -to " + dest_conn
            out = out + ';\n'
        out = out + "set_instance_assignment "
        out = out + '-name IO_STANDARD "'
        if portdest.standard is not None:
            out = out + portdest.standard
        else:
            out = out + port.standard
        out = out + '" -to ' + dest_conn
        if tag is not None:
            out = out + " -tag " + tag
        out = out + ";\n"

        # port_option
        if port.port_option is not None:
            out = out + "set_instance_assignment "
            out = out + "-name " + str(port.port_option) + \
                " -to " + dest_conn + ";\n"

        # port options
        options = port.get_subnodes("options", "option")
        for option in options:
            opt_name = option.get_attr_value("name")
            opt_val = option.get_attr_value("value")
            out = out + "set_instance_assignment "
            out = out + "-name " + opt_name
            if opt_val:
                out = out + ' "' + opt_val + '"'
            out = out + " -to " + dest_conn
            if tag is not None:
                out = out + " -tag " + tag
            out = out + ";\n"
        return out

    def generate_pinout(self, filename=None):
        """ Generate the constraint file in tcl for quartus fpga
        """
        if filename is None:
            filename = self.project.projectpath + \
                SYNTHESISPATH + "/" + \
                self.project.name + "_pinout" + TCLEXT
        self.project = self.project
        out = "# Pinout file, automaticaly generated by pod\n"
        out = out + "package require ::quartus::project\n"
        out = out + self.generatepinoutcontent()
        out = out + "#end\n"
        try:
            file_constr = open(filename, "w")
        except IOError, error:
            raise PodError(str(error), 0)
        file_constr.write(out)
        file_constr.close()
        display.msg("Constraint file generated with name :" + filename)
        return filename

    def generate_sdc(self, filename=None):
        """ Generate the sdc file
            for clock constraints
        """
        out = "# sdc file, automaticaly generated by pod\n"
        out = out + "#*********************\n"
        out = out + "# Create Clock\n"
        out = out + "#*********************\n"
        platform = self.project.platform

        for clock in platform.clocks:
            out = out + "create_clock -period " + \
                "%g" % ((1000 / float(clock["frequency"]))) + \
                "ns " + "[get_ports " + clock["name"] + "]\n"
        for component in self.project.instances:
            for interface in component.interfaces:
                for port in interface.ports:
                    frequency = port.get_attr_value("frequency")
                    if frequency is not None:
                        portname = component.instancename + "_" + \
                            port.name
                        out = out + "create_clock -period " + \
                            "%g" % ((1000 / float(frequency))) + \
                            "ns " + "[get_ports " + portname + "]\n"
        out = out + "#*********************\n"
        out = out + "# Create Generated Clock\n"
        out = out + "#*********************\n"
        out = out + "derive_pll_clocks\n"
        out = out + "#*********************\n"
        out = out + "# Set Clock Uncertainty\n"
        out = out + "#*********************\n"
        out = out + "derive_clock_uncertainty\n"
        try:
            sdc_file = open(filename, "w")
        except IOError, error:
            raise PodError(str(error), 0)
        sdc_file.write(out)
        sdc_file.close()
        display.msg("Clocks Constraint file generated with name :" + filename)
        return filename

    def project_base_creation(self):
        """ return string
            for project creation
        """
        out = "package require ::quartus::project\n"
        out += "package require ::quartus::flow\n"
        out += "project_new -revision " + \
            " top_" + self.project.name + \
            " top_" + self.project.name + "\n"
        return out

    def generatelibraryconstraints(self):
        return ""

    def project_base_configuration(self):
        """ return basic project
            configuration
        """
        platform = self.project.platform
        out = 'set_global_assignment -name FAMILY "' + \
            platform.family + '"\n'
        out += "set_global_assignment -name DEVICE " + \
            platform.device + "\n"
        out += "set_global_assignment -name PROJECT_OUTPUT_DIRECTORY " + \
            self.project.projectpath + BINARYPROJECTPATH + "/\n"
        platform_option = self.project.platform.get_node("toolchain")
        if platform_option:
            for option in platform_option.get_nodes("option"):
                out += "set_global_assignment -name " + \
                    option.name + " " + option.text + "\n"

        # component constraints
        for component in self.project.instances:
            contraints = component.constraints
            for constraint in contraints:
                tag = constraint.get_attr_value("tag")
                assignment_type = constraint.get_attr_value("type")
                value = constraint.get_attr_value("value")
                out += "set_" + assignment_type + \
                    "_assignment -name " + \
                    constraint.get_attr_value("name")
                if assignment_type == "instance":
                    out += " -to " + component.instancename
                else:
                    out += " "
                out += value
                if tag is not None:
                    out += " -tag " + tag
                out += "\n"
        out += "set_global_assignment -name TOP_LEVEL_ENTITY top_" + \
            self.project.name + "\n"
        return out
        # tclfile.write("project set package "+platform.package+"\n")
        # tclfile.write("project set speed "+platform.speed+"\n")
        # tclfile.write("project set {Preferred Language} VHDL\n")
        # tclfile.write('project set "Create Binary Configuration File" TRUE\n');
        # Source files
        # tclfile.write("## add components sources file\n")
        # tclfile.write("# add top level sources file\n")

    @classmethod
    def add_file_to_tcl(cls, filename):
        """ return line according to the
            synthesis tool
        """
        file_split = os.path.splitext(filename)
        file_extension = file_split[-1][1:]
        out = "set_global_assignment -name "
        if file_extension == "vhd":
            out += "VHDL_FILE"
        elif file_extension == "v":
            out += "VERILOG_FILE"
        elif file_extension == "qip":
            out += "QIP_FILE"
        elif file_extension == "sdc":
            out += "SDC_FILE"
        else:
            out += "SOURCE_FILE"

        out += " " + filename + "\n"
        print out
        return out

    def insert_tools_specific_commands(self):
        """ return lines for misc stuff
            specific to a tool
        """
        platform = self.project.platform
        # Create clocks constraints
        sdcfile = self.project.projectpath + SYNTHESISPATH + "/" + \
            self.project.name + ".sdc"
        self.generate_sdc(sdcfile)
        out = ""

        list_qsys_comp = self.needqsys()
        if len(list_qsys_comp):
            for qsys_component in list_qsys_comp:
                self.generate_qsys_script(qsys_component)
                out += "set_global_assignment -name QSYS_FILE " + \
                    ".." + SYNTHESISPATH + "/" + qsys_component.name + \
                    "_qsys.qsys\n"

        # device details
        if platform.package:
            out += "set_global_assignment -name DEVICE_FILTER_PACKAGE " + \
                platform.package + "\n"
        if platform.pin_count:
            out += "set_global_assignment -name DEVICE_FILTER_PIN_COUNT " + \
                platform.pin_count + "\n"
        if platform.speed:
            out += "set_global_assignment -name DEVICE_FILTER_SPEED_GRADE " + \
                platform.speed + "\n"
        out += self.generatepinoutcontent()
        return out

    @classmethod
    def insert_tools_gen_cmds(cls):
        """ return lines for bitstream generation
        """
        # Commit assignments
        out = "export_assignments\n"
        out += "execute_flow -compile\n"

        # Close project
        out += "project_close\n"
        return out

    @classmethod
    def launch_as_shell(cls, commandname, option):
        """ Display messages from toolchain
        """
        for line in sy.launch_as_shell(commandname, option):
            if settings.color() == 1:
                print COLOR_SHELL + line + COLOR_END,
            else:
                print "SHELL>" + line,

    def generate_bitstream(self, commandname, scriptname):
        """ generate the bitstream """
        default_path = self.parent.get_synthesis_value("default_path")
        rbf_commandname = default_path + "/" + \
            self.parent.get_synthesis_value("rbf")

        result_file = self.project.projectpath + BINARYPROJECTPATH + "/" + \
            BINARY_PREFIX + self.project.name + \
            ALTERA_BITSTREAM_SUFFIX

        cnv_result_file = self.project.projectpath + BINARYPROJECTPATH + "/" + \
            BINARY_PREFIX + self.project.name + \
            ALTERA_BINARY_SUFFIX

        pwd = sy.pwd()
        sy.del_all(self.project.projectpath + OBJSPATH)
        sy.chdir(self.project.projectpath + SYNTHESISPATH)
        commandname = commandname + " -t "

        list_qsys_comp = self.needqsys()
        if len(list_qsys_comp):
            qsys_path = self.parent.get_synthesis_value("qsys_path")
            qsys_script = self.parent.get_synthesis_value("qsys_script")
            qsys_commandname = default_path + "/" + qsys_path + "/" + \
                qsys_script
            for component in list_qsys_comp:
                self.launch_as_shell(qsys_commandname,
                                     " --script=" + self.project.projectpath +
                                     SYNTHESISPATH + "/" +
                                     component.name + "_qsys.tcl")

        self.launch_as_shell(commandname, scriptname)

        try:
            output_format = self.project.platform.output_format
            commandarg = "-c " + result_file + " " + cnv_result_file
            if output_format == "cvp":
                self.launch_as_shell(rbf_commandname, "--cvp " + commandarg)
            elif output_format == "rbf":
                self.launch_as_shell(rbf_commandname, commandarg)
            elif output_format == "rbfComp":
                self.launch_as_shell(rbf_commandname,
                                     "--option=bitstream_compression=on " +
                                     commandarg)
        except IOError:
            raise PodError("Can't copy bitstream")
        sy.chdir(pwd)
