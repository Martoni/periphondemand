#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     ise.py
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
""" Manage ISE toolchain """

from periphondemand.bin.utils.synthesiswrapper import SynthesisWrapper

from periphondemand.bin.define import UCFEXT
from periphondemand.bin.define import XILINX_BITSTREAM_SUFFIX
from periphondemand.bin.define import XILINX_BINARY_SUFFIX


class Ise(SynthesisWrapper):
    """ Manage specific ise synthesis toolchain part
    """
    def __init__(self, project, parent):
        SynthesisWrapper.__init__(self, project, parent)

    @classmethod
    def constraints_file_extension(cls):
        return ("ucf")

    def project_base_creation(self):
        """ return basic project
            configuration
        """
        # create project
        return "project new " + self.project.name + "\n"

    def project_base_configuration(self):
        """ return basic project
            configuration
        """
        platform = self.project.platform
        out = "project set family " + platform.family + "\n"
        out += "project set device " + platform.device + "\n"
        out += "project set package " + platform.package + "\n"
        out += "project set speed " + platform.speed + "\n"
        out += "project set {Preferred Language} VHDL\n"
        out += 'project set "Create Binary Configuration File" TRUE\n'
        return out

    @classmethod
    def add_file_to_tcl(cls, filename):
        """ return line according to the
            synthesis tool
        """
        return "xfile add " + filename + "\n"

    def add_constraints_file(self, filename):
        """ return line for constraints file insertion
        """
        out = self.add_file_to_tcl(".." + filename + UCFEXT)
        out += "set constraints_file .." + filename + \
            UCFEXT + " \n"
        return out

    @classmethod
    def addforcepinout(cls, port):
        """ return line for pin forced
        """
        out = 'NET "force_' + str(port.name)
        out += '" LOC="' + str(port.position)\
                  + '" | IOSTANDARD=' + str(port.standard)
        if port.drive is not None:
            out += " | DRIVE=" + str(port.drive)
        out += r'; # ' + str(port.name) + '\n'
        return out

    def addpinconstraints(self, connect, port):
        """ return pin constraint definition
        """
        out = 'NET "' +\
            connect["instance_dest"] + "_" + connect["port_dest"]
        instancedest =\
            self.project.get_instance(connect["instance_dest"])
        interfacedest = \
            instancedest.get_interface(connect["interface_dest"])
        portdest = interfacedest.get_port(connect["port_dest"])

        if portdest.size != 1:
            if portdest.is_fully_connected() :
                out += "<" + connect["pin_dest"] + ">"
            else:
                out += "_pin" + connect["pin_dest"]
        out += '" LOC="' + str(port.position) + '"'
        if portdest.port_option is not None:
            out += ' | ' + str(portdest.port_option)
        elif port.port_option is not None:
            out += ' | ' + str(port.port_option)
        if portdest.standard is not None:
            out += " | IOSTANDARD=" +\
                str(portdest.standard)
        else:
            out += " | IOSTANDARD=" + str(port.standard)
        if portdest.drive is not None:
            out += " | DRIVE=" + str(portdest.drive)
        elif port.drive is not None:
            out += " | DRIVE=" + str(port.drive)
        out += r'; # ' + str(port.name) + '\n'
        return out

    @classmethod
    def addclockconstraints(cls, connect, frequency):
        """ return clock constraints line definition
        """
        out = "NET \"" + connect["instance_dest"] +\
            "_" + connect["port_dest"] + "\" TNM_NET = \"" +\
            connect["instance_dest"] + "_" + connect["port_dest"] +\
            "\";\n"
        out += "TIMESPEC \"TS_" +\
            connect["instance_dest"] +\
            "_" + connect["port_dest"] +\
            "\" = PERIOD \"" +\
            connect["instance_dest"] +\
            "_" + connect["port_dest"] +\
            "\" " +\
            "%g" % ((1000 / float(frequency))) +\
            " ns HIGH 50 %;\n"
        return out

    @classmethod
    def insert_tools_specific_commands(cls):
        """ return lines for misc stuff
            specific to a tool
        """
        out = 'project set "Load Physical Constraints File" "Default" ' + \
            '-process "Analyze Power Distribution (XPower Analyzer)"\n'
        out += 'project set "Load Physical Constraints File" "Default" ' + \
            '-process "Generate Text Power Report"\n'
        out += 'project set "Target UCF File Name" "" ' + \
            '-process "Back-annotate Pin Locations"\n'
        out += 'project set "Ignore User Timing Constraints" "false" ' + \
            '-process "Map"\n'
        return out

    @classmethod
    def insert_tools_gen_cmds(cls):
        """ return lines for bitstream generation
        """
        # Run synthesis
        out = 'process run "Synthesize"\n'
        out += 'process run "Translate"\n'
        out += 'process run "Map"\n'
        out += 'process run "Place & Route"\n'
        out += 'process run "Generate Programming File"\n'

        # Run post synthesis model generation
        out += 'process run "Generate Post-Synthesis Simulation Model"\n'
        #    out += 'cp netgen/synthesis/top_' +
        #                    SETTINGS.active_project.name + \
        #        '_synthesis.vhd ../simulation/\n')
        # Run post place and route model generation
        out += 'process run ' + \
            '"Generate Post-Place & Route Simulation Model"\n'
        out += 'process run "Implement Design" -force rerun_all\n'
        out += 'project close\n'
        return out

    @property
    def ext_files(self):
        """ return list of bitstream files extension
        """
        return [XILINX_BITSTREAM_SUFFIX, XILINX_BINARY_SUFFIX]
