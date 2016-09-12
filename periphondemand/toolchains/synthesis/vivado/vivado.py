#! /usr/bin/python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:     ise.py
# Purpose:
# Author:   Gwenhael Goavec-Merou <gwenhael.goavec-merou@trabucayre.com>
# Created:  21/07/2015
# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
# -----------------------------------------------------------------------------
""" Manage Vivado toolchain """

import os

from periphondemand.bin.define import BINARYPROJECTPATH
from periphondemand.bin.define import BINARY_PREFIX
from periphondemand.bin.define import SYNTHESISPATH
from periphondemand.bin.define import OBJSPATH
from periphondemand.bin.define import VHDLEXT
from periphondemand.bin.define import TCLEXT
from periphondemand.bin.define import XILINX_BITSTREAM_SUFFIX
from periphondemand.bin.define import XILINX_BINARY_SUFFIX
from periphondemand.bin.define import COLOR_END
from periphondemand.bin.define import COLOR_SHELL

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils import wrappersystem as sy

from periphondemand.bin.toolchain.synthesis import Synthesis


SETTINGS = Settings()
DISPLAY = Display()


class Vivado(Synthesis):
    """ Manage specific synthesis part for
        vivado toolchain
    """

    SYNTH_CMD = "vivado"
    name = "vivado"

    def __init__(self, parent):
        """ constructor
        """
        Synthesis.__init__(self, parent)

        tool = self.synthesis_toolcommandname
        command = "-version"

        cont = []
        cont = list(os.popen(tool + " " + command))
        self.version = cont[0].split(" ")[1][1:]
        self.base_version = self.version.split(".")[0]

    @classmethod
    def constraints_file_extension(cls):
        return ("xdc")

    def need_block_design(self):
        """ Check if design need to generate a block
            design file
        """
        list_bd_comp = []
        for component in self.project.instances:
            bd_node = component.get_nodes("vivado")
            if not (len(bd_node) == 0):
                list_bd_comp.append(component)
        return list_bd_comp

    def generate_block_design(self, component):
        """ Generate the block design file for xilinx fpga """

        out = "set design_name " + component.name + "_bd\n\n"
        out += "# CHECKING IF PROJECT EXISTS\n"
        out += 'if { [get_projects -quiet] eq "" } {\n'
        out += '   puts "ERROR: Please open or create a project!"\n'
        out += "   return 1\n"
        out += "}\n\n\n"

        out += "# Creating design if needed\n\n"
        out += "   # USE CASES:\n"
        out += "   #    8) No opened design, design_name not in project.\n"
        out += "   #    9) Current opened design, has components, but " + \
            "diff names, design_name not in project.\n\n"
        out += '   puts "INFO: Currently there is no design ' + \
            '<$design_name> in project, so creating one..."\n\n'
        out += "   create_bd_design $design_name\n\n"
        out += '   puts "INFO: Making design <$design_name> as ' + \
            'current_bd_design."\n'
        out += "   current_bd_design $design_name\n\n"
        out += 'puts "INFO: Currently the variable <design_name> ' + \
            'is equal to \\"$design_name\\"."\n\n'
        out += "\n\n\n"

        out += \
            "# Procedure to create entire design; Provide " + \
            "argument to make\n" + \
            '# procedure reusable. If parentCell is "", will ' + \
            'use root.\n' + \
            "proc create_root_design { parentCell } {\n\n" + \
            '  if { $parentCell eq "" } {\n' + \
            "     set parentCell [get_bd_cells /]\n" + \
            "  }\n\n" + \
            "  # Get object for parentCell\n" + \
            "  set parentObj [get_bd_cells $parentCell]\n" + \
            '  if { $parentObj == "" } {\n' + \
            '     puts "ERROR: Unable to find parent cell ' + \
            ' <$parentCell>!"\n' + \
            "     return\n" + \
            "  }\n\n"
        out += \
            "  # Make sure parentObj is hier blk\n" + \
            "  set parentType [get_property TYPE $parentObj]\n" + \
            '  if { $parentType ne "hier" } {\n' + \
            '     puts "ERROR: Parent <$parentObj> has TYPE = ' + \
            ' <$parentType>. ' + \
            'Expected to be <hier>."\n' + \
            "     return\n" + \
            "  }\n\n" + \
            "  # Save current instance; Restore later\n" + \
            "  set oldCurInst [current_bd_instance .]\n\n" + \
            "  # Set parent object as current\n" + \
            "  current_bd_instance $parentObj\n"
        out += "\n\n"

        out += "  # Create interface ports\n"
        vivado_node = component.get_nodes("vivado")
        for vivado_if in vivado_node[0].get_subnodes("vivado_interfaces",
                                                     "vivado_interface"):
            if_params = vivado_if.get_nodes("parameter")
            out += "  set " + vivado_if.get_attr_value("instance_name") + \
                " [ create_bd_intf_port -mode " + \
                vivado_if.get_attr_value("mode") + " " + \
                vivado_if.get_attr_value("options") + " " + \
                vivado_if.get_attr_value("name") + " " + \
                vivado_if.get_attr_value("instance_name") + " ]\n"
            if if_params != []:
                out += "  set_property -dict [ list "
                for param in if_params:
                    out += "    CONFIG." + param.get_attr_value("name") + \
                        " {" + param.text + "} "
                out += " ] $" + \
                    vivado_if.get_attr_value("instance_name") + "\n"
        out += "\n"

        out += "  # Create ports\n"
        for vivado_if in vivado_node[0].get_subnodes("vivado_ports",
                                                     "vivado_port"):
            if_params = vivado_if.get_nodes("parameter")
            out += "  set " + vivado_if.get_attr_value("instance_name") + \
                " [ create_bd_port -dir " + \
                vivado_if.get_attr_value("direction")

            # if if_from != None:
            #    out += " -from " + if_from)
            # if if_to != None:
            #    out += " -to " + if_to)
            out += " -type " + vivado_if.get_attr_value("type") + \
                " " + vivado_if.get_attr_value("instance_name") + " ]\n"
            if if_params != []:
                out += "  set_property -dict [ list "
                for param in if_params:
                    out += "CONFIG." + param.get_attr_value("name") + \
                        " {" + param.text + "} "
                out += " ] $" + vivado_if.get_attr_value("instance_name") + \
                    "\n"
        out += "\n"

        vivado_comps = vivado_node[0].get_subnodes("vivado_components",
                                                   "vivado_component")
        for comp in vivado_comps:
            cp_params = comp.get_nodes("parameter")
            out += "  # Create instance: " + \
                comp.get_attr_value("instance_name") + \
                ", and set properties\n"
            out += "  set " + comp.get_attr_value("instance_name") + \
                " [ create_bd_cell " + \
                "-type " + comp.get_attr_value("type") + " " + \
                comp.get_attr_value("options") + " " + \
                comp.get_attr_value("name") + \
                " " + comp.get_attr_value("instance_name") + " ]\n"
            if cp_params != []:
                out += "  set_property -dict [ list "
                for param in cp_params:
                    out += "CONFIG." + param.get_attr_value("name") + \
                        " {" + param.text + "} \\\n"
                out += " ] $" + comp.get_attr_value("instance_name") + "\n"
            out += "\n"

        out += "  # Create interface connections\n"
        vivado_conns = vivado_node[0].get_subnodes("ifs_connections",
                                                   "connection")
        for conn in vivado_conns:
            out += "  connect_bd_intf_net -intf_net " + \
                conn.get_attr_value("src")
            for dest in conn.get_nodes("dest"):
                dest_type = dest.get_attr_value("type")
                out += " [get_bd_intf_"
                if dest_type == "port":
                    out += "ports"
                else:
                    out += "pins"
                out += " " + dest.get_attr_value("name") + "]"
            out += "\n"
        out += "\n"

        out += "  # Create port connections\n"
        vivado_conns = vivado_node[0].get_subnodes("ports_connections",
                                                   "connection")
        for conn in vivado_conns:
            out += "  connect_bd_net -net " + conn.get_attr_value("src")
            for dest in conn.get_nodes("dest"):
                dest_type = dest.get_attr_value("type")
                out += " [get_bd_"
                if dest_type == "port":
                    out += "ports"
                else:
                    out += "pins"
                out += " " + dest.get_attr_value("name") + "]"
            out += "\n"
        out += "\n"

        out += "  # Create address segments\n" + \
            "  create_bd_addr_seg -range 0x10000 -offset 0x43C00000 " + \
            "[get_bd_addr_spaces processing_system7_0/Data] " + \
            "[get_bd_addr_segs M00_AXI/Reg] SEG_M00_AXI_Reg\n  \n\n"
        out += "  # Restore current instance\n" + \
            "  current_bd_instance $oldCurInst\n\n" + \
            "  save_bd_design\n"
        out += "}\n"
        out += "# End of create_root_design()\n\n\n"
        out += "#####################################################\n"
        out += "# MAIN FLOW\n"
        out += "#####################################################\n"
        out += "\n"
        out += 'create_root_design ""\n\n\n'

        tclfile = open(self.project.projectpath + SYNTHESISPATH + "/" +
                       component.name + "_bd.tcl", "w")
        tclfile.write(out)

    def add_constraints_file(self, filename):
        """ return line for constraints file insertion
        """
        out = "# Set 'constrs_1' fileset object\n"
        out += "set obj [get_filesets constrs_1]\n"
        out += "\n"
        out += "# Add/Import constrs file and set constrs file properties\n"
        out += 'set file "[file normalize "..' + SYNTHESISPATH + "/" + \
            self.project.name + '.xdc"]"\n'
        out += "set file_added [add_files -norecurse -fileset $obj $file]\n"
        out += 'set file "..' + SYNTHESISPATH + "/" + \
            self.project.name + '.xdc"\n'
        out += "set file [file normalize $file]\n"
        out += 'set file_obj [get_files -of_objects ' + \
            '[get_filesets constrs_1] [list "*$file"]]\n'
        out += 'set_property "file_type" "XDC" $file_obj\n'
        out += "\n"
        out += "\n"
        return out

    def generatelibraryconstraints(self):
        # TODO
        """ Adds constraints specified by a component, such as placement
            for a PLL, multiplier, etc. or clock informations about PLL
            output signals
        """
        out = "# components constraints \n"
        for instance in self.project.instances:
            if instance.constraints != []:
                for constraint in instance.constraints:
                    inst_name = instance.instancename
                    attr_name = str(constraint.get_attr_value("name"))
                    constr_type = constraint.get_attr_value("type")
                    sig_type = constraint.get_attr_value("sig_type")

                    if sig_type is None:
                        sig_type = "ports"
                    if constr_type == "clk":
                        frequency = constraint.get_attr_value("frequency")
                        freq = " %g" % ((1000 / float(frequency)))
                        out += "create_clock -period " + freq + \
                            " -name " + inst_name + "_" + attr_name + \
                            " [get_" + sig_type + " " + inst_name
                        if sig_type == "ports":
                            out += "_"
                        else:
                            out += "/"
                        out += attr_name + "]\n"
                    elif constr_type == "placement":
                        out += 'INST "' + inst_name + "/" + \
                            attr_name + '" LOC=' + \
                            constraint.get_attr_value("loc") + ";\n"
                    elif constr_type == "false_path":
                        # GGM : add verification : this attributes are
                        # mandatory for false_path
                        src_type = constraint.get_attr_value("src_type")
                        dest_type = constraint.get_attr_value("dest_type")
                        out += "set_false_path -from [get_"
                        if src_type == "clocks" or src_type == "inst_clocks":
                            out += "clocks "
                        else:
                            out += src_type
                        if src_type == "inst_clocks":
                            out += inst_name + "_"
                        elif src_type == "pins":
                            out += inst_name + "/"
                        out += constraint.get_attr_value("src") + \
                            "] -to [get_"
                        if dest_type == "clocks" or dest_type == "inst_clocks":
                            out += "clocks "
                        else:
                            out += src_type
                        if dest_type == "inst_clocks":
                            out += inst_name + "_"
                        elif dest_type == "pins":
                            out += inst_name + "/"
                        out += constraint.get_attr_value("dest") + "]\n"
                    elif constr_type == "input_delay":
                        out += "set_input_delay -clock " + inst_name + "_" + \
                            constraint.get_attr_value("src") + " " + \
                            constraint.get_attr_value("value") + " " + \
                            "[get_" + sig_type + " " + inst_name
                        if sig_type == "ports":
                            out += "_"
                        else:
                            out += "/"
                        out += constraint.get_attr_value("dest") + "]\n"
                    else:
                        raise PodError("component " + instance.name +
                                       " has an unknown type " +
                                       constr_type, 0)
        return out

    @classmethod
    def addforcepinout(cls, port):
        """ Generate line for pin
        """
        constr = port.get_attr_value("constr_hidden")
        if constr is not None and constr == "1":
            return ""

        out = 'NET "force_' + str(port.name)
        out += '" LOC="' + str(port.position) + \
            '" | IOSTANDARD=' + str(port.standard)
        if port.getDrive() is not None:
            out += " | DRIVE=" + str(port.drive)
            out += r'; # ' + str(port.name) + '\n'
        return out

    @classmethod
    def addclockconstraints(cls, connect, frequency):
        """ Generate clock constraints
        """
        out = "NET \"" + connect["instance_dest"] + \
            "_" + connect["port_dest"] + '" TNM_NET = "' + \
            connect["instance_dest"] + "_" + connect["port_dest"] + \
            "\";\n"
        out += "TIMESPEC \"TS_" + connect["instance_dest"] + \
            "_" + connect["port_dest"] + '" = PERIOD "' + \
            connect["instance_dest"] + "_" + connect["port_dest"] + \
            "\" " + "%g" % ((1000 / float(frequency))) + \
            " ns HIGH 50 %;\n"
        return out

    def addpinconstraints(self, connect, port):
        """ Generate constraints for a pin
        """
        constr = port.get_attr_value("constr_hidden")
        if constr is not None and constr == "1":
            return ""

        instancedest =\
            self.project.get_instance(connect["instance_dest"])
        interfacedest = \
            instancedest.get_interface(connect["interface_dest"])
        portdest = interfacedest.get_port(connect["port_dest"])

        get_ports = "[get_ports "
        if portdest.size != 1:
            get_ports += '{'

        get_ports += connect["instance_dest"] + \
            "_" + connect["port_dest"]

        if portdest.size != 1:
            if portdest.is_fully_connected():
                get_ports += "[" + connect["pin_dest"] + "]"
            else:
                get_ports += "_pin" + connect["pin_dest"]
            get_ports += '}'
        get_ports += ']'

        out = 'set_property PACKAGE_PIN ' + str(port.position)
        out += " " + get_ports + "\n"

        # TODO

        # if portdest.getPortOption() != None:
        #    out = out + ' | '+str(portdest.getPortOption())
        # elif port.getPortOption() != None:
        #    out = out + ' | '+str(port.getPortOption())
        out += 'set_property IOSTANDARD '
        if portdest.standard is not None:
            out += str(portdest.standard) + " "
        else:
            out += str(port.standard)
        out += " " + get_ports + "\n"

        # if portdest.getDrive() != None:
        #    out = out + " | DRIVE="+str(portdest.getDrive())
        # elif port.getDrive() != None:
        #    out = out + " | DRIVE="+str(port.getDrive())
        # out = out+r'; # '+str(port.name)+'\n'
        return out

    def project_base_creation(self):
        """ return string
            for project creation
        """
        platform = self.project.platform
        proj_name = self.project.name

        out = "# Set the reference directory for source file relative " + \
            "paths (by default the value is script directory path)\n"
        out += 'set origin_dir "..' + OBJSPATH + '/"'
        out += "\n"
        out += "\n"
        out += "# Create project\n"
        out += "create_project -part " + platform.device + \
            " " + self.project.name + "\n"
        out += "\n"
        out += "# Set the directory path for the new project\n"
        out += "set proj_dir [get_property directory [current_project]]\n"
        out += "\n"
        out += "# Set project properties\n"
        out += "set obj [get_projects " + proj_name + "]\n"
        if platform.board_part is not None:
            out += 'set_property "board_part" "' + \
                platform.board_part + '" $obj\n'
        out += 'set_property "default_lib" "xil_defaultlib" $obj\n'
        out += 'set_property "simulator_language" "Mixed" $obj\n'
        out += 'set_property "target_language" "VHDL" $obj\n'
        out += "\n"
        return out

    def project_base_configuration(self):
        """ return basic project
            configuration
        """
        out = "# Create 'sources_1' fileset (if not found)\n"
        out += "if {[string equal [get_filesets -quiet sources_1] \"\"]} {\n"
        out += "  create_fileset -srcset sources_1\n"
        out += "}\n"
        out += "\n"
        out += "# Set 'sources_1' fileset object\n"
        out += "set obj [get_filesets sources_1]\n"
        out += "set files [list \\\n"
        out += ' "[file normalize "..' + SYNTHESISPATH + "/top_" + \
            self.project.name + VHDLEXT + '"]"\\\n'

        out += "]\n"
        out += "add_files -norecurse -fileset $obj $files\n"
        out += "\n"
        out += "# Set 'sources_1' fileset file properties for remote files\n"
        out += "\n"
        out += "# Set 'sources_1' fileset file properties for local files\n"
        out += "# None\n"
        out += "\n"
        out += "# Set 'sources_1' fileset properties\n"
        out += "set obj [get_filesets sources_1]\n"
        out += 'set_property "top" "top_' + self.project.name + '" $obj\n'
        out += "\n"
        out += "# Create 'constrs_1' fileset (if not found)\n"
        out += "if {[string equal [get_filesets -quiet constrs_1] \"\"]} {\n"
        out += "  create_fileset -constrset constrs_1\n"
        out += "}\n"
        out += "\n"
        return out

    @classmethod
    def add_file_to_tcl(cls, filename):
        out = "set obj [get_filesets sources_1]\n"
        out += 'set file "[file normalize "' + filename + '"]"\n'
        out += "set file_added [add_files -norecurse -fileset $obj $file]\n"
        return out

    def insert_tools_specific_commands(self):
        """ return lines for misc stuff
            specific to a tool
        """
        platform = self.project.platform
        proj_name = self.project.name

        out = "# Create 'sim_1' fileset (if not found)\n"
        out += 'if {[string equal [get_filesets -quiet sim_1] ""]} {\n'
        out += "  create_fileset -simset sim_1\n"
        out += "}\n\n"
        out += "# Set 'sim_1' fileset object\n"
        out += "set obj [get_filesets sim_1]\n"
        out += "# Empty (no sources present)\n\n"
        out += "# Set 'sim_1' fileset properties\n"
        out += "set obj [get_filesets sim_1]\n"
        out += 'set_property "top" "top_' + self.project.name + '" $obj\n'
        out += "\n"
        out += "# Create 'synth_1' run (if not found)\n"
        out += "if {[string equal [get_runs -quiet synth_1] \"\"]} {\n"
        out += "  create_run -name synth_1 -part " + platform.device + \
            ' -flow {Vivado Synthesis ' + self.base_version + '} ' + \
            '-strategy "Vivado Synthesis Defaults" -constrset constrs_1\n'
        out += "} else {\n"
        out += '  set_property strategy "Vivado Synthesis Defaults" ' + \
            "[get_runs synth_1]\n"
        out += '  set_property flow "Vivado Synthesis ' + \
            self.base_version + '" [get_runs synth_1]\n'
        out += "}\n"
        out += "set obj [get_runs synth_1]\n\n"
        out += "# set the current synth run\n"
        out += "current_run -synthesis [get_runs synth_1]\n\n"
        out += "# Create 'impl_1' run (if not found)\n"
        out += "if {[string equal [get_runs -quiet impl_1] \"\"]} {\n"
        out += "  create_run -name impl_1 -part " + platform.device + \
            " -flow {Vivado Implementation " + self.base_version + "} " + \
            '-strategy "Vivado Implementation Defaults" ' + \
            '-constrset constrs_1 -parent_run synth_1\n'
        out += "} else {\n"
        out += '  set_property strategy "Vivado Implementation Defaults" ' + \
            "[get_runs impl_1]\n"
        out += '  set_property flow "Vivado Implementation ' + \
            self.base_version + '" [get_runs impl_1]\n'
        out += "}\n"
        out += "set obj [get_runs impl_1]\n\n"
        out += 'set_property "needs_refresh" "1" $obj\n'
        out += 'set_property "steps.write_bitstream.args.bin_file" "1" $obj\n'

        list_bd_comp = self.need_block_design()
        if len(list_bd_comp):
            out += "load_features ipintegrator\n"
            for component in list_bd_comp:
                bd_name = component.name + "_bd" + TCLEXT
                self.generate_block_design(component)
                out += "source .." + SYNTHESISPATH + "/" + bd_name + "\n"
        out += "\n\n"
        out += "# set the current impl run\n"
        out += "current_run -implementation [get_runs impl_1]\n\n"
        out += 'puts "INFO: Project created: ' + proj_name + '"\n'
        out += "# set the current impl run\n"
        out += "current_run -implementation [get_runs impl_1]\n"

        if len(list_bd_comp):
            for component in list_bd_comp:
                out += "generate_target all [get_files " + \
                    "./" + proj_name + ".srcs/sources_1/bd/" + \
                    component.name + "_bd/" + component.name + "_bd.bd]\n"
        return out

    @classmethod
    def insert_tools_gen_cmds(cls):
        """ return lines for bitstream generation
        """
        out = "launch_runs synth_1\n"
        out += "wait_on_run synth_1\n"

        out += "## do implementation\n"
        out += "launch_runs impl_1\n"
        out += "wait_on_run impl_1\n"

        out += "## make bit file\n"
        out += "launch_runs impl_1 -to_step write_bitstream\n"
        out += "wait_on_run impl_1\n"

        out += "exit\n"
        return out

    @property
    def ext_files(self):
        """ return list of bitstream files extension
        """
        return [XILINX_BITSTREAM_SUFFIX, XILINX_BINARY_SUFFIX]

    def generate_bitstream(self):
        """ generate the bitstream """
        commandname = self.synthesis_toolcommandname
        scriptpath = os.path.join(self.parent.projectpath + SYNTHESISPATH,
                                  self.tcl_scriptname)

        pwd = sy.pwd()
        sy.del_all(self.project.projectpath + OBJSPATH)
        sy.chdir(self.project.projectpath + SYNTHESISPATH)

        commandname += " -mode tcl"
        scriptname = "-source " + scriptpath + " -tclargs build"
        binpath = self.project.projectpath + OBJSPATH + "/" + \
            self.project.name + ".runs/impl_1/"

        for line in sy.launch_as_shell(commandname, scriptname):
            if SETTINGS.color() == 1:
                print(COLOR_SHELL + line + COLOR_END),
            else:
                print("SHELL>" + line),
        for ext_file in self.ext_files:
            try:
                sy.cp_file(binpath + BINARY_PREFIX + self.project.name +
                           ext_file,
                           self.project.projectpath + BINARYPROJECTPATH + "/")
            except IOError:
                raise PodError("Can't copy bitstream")
        sy.chdir(pwd)
