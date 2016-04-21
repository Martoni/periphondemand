#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     TopVHDL.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  15/05/2008
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
""" Generating code for top component """

from periphondemand.bin.define import ONETAB
from periphondemand.bin.define import TEMPLATESPATH
from periphondemand.bin.define import HEADERTPL

from periphondemand.bin.code.topgen import TopGen
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError

SETTINGS = Settings()


class TopVHDL(TopGen):
    """ Generate VHDL Top component
    """

    def __init__(self, project):
        TopGen.__init__(self, project)

    @classmethod
    def header_template_name(cls):
        return SETTINGS.path + TEMPLATESPATH + "/" + HEADERTPL

    @classmethod
    def file_extension(cls):
        return ".vhd"

    @classmethod
    def insert_comment(cls, comment):
        """ return VHDL one line comment """
        return "-- " + comment + "\n"

    @classmethod
    def insert_comment_block(cls, indent, comment):
        """ return VHDL multi line comment """
        comm_size = len(comment) + 6
        out = indent + "-" * comm_size + "\n"
        out += indent + "-- " + comment + " --\n"
        out += indent + "-" * comm_size + "\n\n"
        return out

    @classmethod
    def connect_ports(cls, srcname, destname):
        """ return port connection between to signals """
        out = srcname + " <= "
        if destname == 0:
            out += "'0'"
        elif destname == 1:
            out += "'1'"
        else:
            out += destname
        out += ";\n"
        return out

    def connect_inc_signals(self, srcname, destname, direction, pinnum):
        """ return incomplete connected signal """
        if direction == "in":
            srcname += "(" + str(pinnum) + ")"
            destname += "_pin" + str(pinnum)
        else:
            srcname += "_pin" + str(pinnum)
            destname += "(" + str(pinnum) + ")"
        return self.connect_ports(srcname, destname)

    def instance_inc_sig(self, component, connect, pin):
        """ return pin connection when
            ports pins are connected individually
            to several oter ports
        """
        port = pin.parent
        out = component.instancename + "_" + port.name
        dest_inst_name = connect["instance_dest"]
        dest_inter_name = connect["interface_dest"]
        p_dest = connect["port_dest"]
        try:
            comp = self.project.get_instance(dest_inst_name)
            inter = comp.get_interface(dest_inter_name)
            port2 = inter.get_port(p_dest)

            if int(port.size) > 1:
                out += "(" + pin.num + ")"
            out += " <= " + connect["instance_dest"] + "_" + \
                connect["port_dest"]
            if int(port2.size) > 1:
                out += "(" + connect["pin_dest"] + ")"
            out += ";\n"
        except PodError:
            pass
        return out

    @classmethod
    def add_scalar_sig(cls, signame, direction):
        """ return entity scalar signal definition """
        out = signame + ": "
        if direction != "":
            out += direction + " "
        out += "std_logic;\n"
        return out

    @classmethod
    def add_vector_sig(cls, signame, direction, msb, lsb):
        """ return entity scalar signal definition """
        out = signame + ": "
        if direction != "":
            out += direction + " "
        out += "std_logic_vector(" + msb + " downto " + lsb + ");\n"
        return out

    def arch_add_line(self, instancename, port, direction):
        """ return port definition """
        if int(port.size) == 1:
            out = self.add_scalar_sig(instancename, direction)
        else:
            out = self.add_vector_sig(instancename, direction,
                                      str(port.real_size - 1),
                                      str(port.min_pin_num))
        return out

    def declare_signal(self, instancename, port):
        """ return signal declaration """
        instancename = "signal " + instancename
        return self.arch_add_line(instancename, port, "")

    @classmethod
    def begin_component(cls, compname):
        return "component " + compname + "\n"

    @classmethod
    def end_component(cls):
        return "end component;\n"

    @classmethod
    def begin_attributes(cls):
        return "generic(\n"

    @classmethod
    def end_attributes(cls):
        return ");\n"

    @classmethod
    def instance_add_port(cls, portname, sig_name):
        """ return port connection """
        return portname + " => " + \
            sig_name + ",\n"

    def instance_add_unc_port(self, port):
        """ return port unconnected """
        if port.direction == "out":
            destname = "open"
        else:
            if int(port.size) == 1:
                destname = "'" + str(port.unconnected_value) + \
                    "'"
            else:
                destname = '"' +\
                    str(port.unconnected_value) * \
                    int(port.size) + \
                    '"'
        return self.instance_add_port(port.name, destname)

    @classmethod
    def insert_attribute(cls, attribute):
        return attribute.name + " : " + \
            attribute.generictype + " := " + \
            str(attribute.value) + ";\n"

    @classmethod
    def instance_begin_port(cls):
        return "port (\n"

    @classmethod
    def instance_end_port(cls):
        return ");\n"

    def entity(self, entityname, portlist):
        """ return code for Top entity
        """
        out = "entity " + entityname + " is\n"
        out += "\n" + ONETAB + "port\n" + ONETAB + "(\n"
        out += self.entity_port_part(portlist)

        out += "\n" + ONETAB + ");\nend entity " + entityname + ";\n\n"
        return out

    def declare_instance(self):
        """ Declaring instances """
        out = self.insert_comment_block(ONETAB, "declare instances")
        for component in self.project.instances:
            if component.is_platform() is False:
                out += "\n" + ONETAB + component.instancename + " : "
                if self.project.vhdl_version == "vhdl93":
                    out += "entity work."
                out += component.name + "\n"
                if component.fpga_generics != []:
                    out += ONETAB + "generic map (\n"
                    for generic in component.fpga_generics:
                        out += ONETAB * 3 + generic.name + " => " + \
                            str(generic.value) + ",\n"
                    # suppress comma
                    out = out[:-2] + "\n"
                    out += ONETAB * 2 + ")\n"

                out += ONETAB + "port map (\n"
                out += self.instance_port_part(ONETAB * 3, component)
                out += ONETAB * 3 + ");\n"
        out += "\n"
        return out

    def architecture(self, entityname, portlist, incompleteportslist):
        """ construct architecture part of the file """
        out = "architecture " + entityname + "_1 of " + entityname + " is\n"
        # declare components
        out = out + self.declare_components()
        # declare signals
        out = out + self.declare_signals(self.project.instances,
                                         incompleteportslist)
        # begin
        out += "\nbegin\n"
        # Connect forces
        out = out + self.connect_forces(portlist)
        # declare Instance
        out = out + self.declare_instance()
        # instance connection
        out = out + self.connect_instance(incompleteportslist)
        # architecture foot
        out += "\nend architecture " + entityname + "_1;\n"
        return out
