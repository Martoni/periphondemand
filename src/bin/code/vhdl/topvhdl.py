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
from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils.poderror import PodError

import datetime

SETTINGS = Settings()
DISPLAY = Display()


class TopVHDL(TopGen):
    """ Generate VHDL Top component
    """

    def __init__(self, project):
        TopGen.__init__(self, project)

    def header(self):
        """ return vhdl header
        """
        header = open(SETTINGS.path + TEMPLATESPATH +
                      "/" + HEADERTPL, "r").read()
        header = header.replace("$tpl:author$", SETTINGS.author)
        header = header.replace("$tpl:date$", str(datetime.date.today()))
        header = header.replace("$tpl:filename$",
                                "Top_" +
                                self.project.name + ".vhd")
        header = header.replace(
            "$tpl:abstract$",
            self.project.description)
        return header

    def entity(self, entityname, portlist):
        """ return VHDL code for Top entity
        """
        out = "entity " + entityname + " is\n"
        out += "\n" + ONETAB + "port\n" + ONETAB + "(\n"
        for port in portlist:
            if port.force_defined():
                portname = "force_" + port.name
                out += ONETAB * 2 + portname + " : out std_logic;\n"
            else:
                portname = port.name
                interfacename = port.parent.name
                instancename = port.parent.parent.instancename

                if port.is_hidden:
                    continue
                out += ONETAB + "-- " + instancename +\
                    "-" + interfacename + "\n"
                if port.is_fully_connected():
                    if (port.direction == "in") or (port.direction == "inout"):
                        same_connections_ports =\
                            port.ports_with_same_connection
                        if same_connections_ports == []:
                            raise PodError(str(port.extended_name) +
                                           " is left unconnected")
                        elif len(same_connections_ports) == 1:
                            out += ONETAB * 2 +\
                                instancename + "_" + portname +\
                                " : " + port.direction
                            if port.connected_msb < 1:
                                out += " std_logic;"
                            else:
                                out += " std_logic_vector(" +\
                                    str(port.connected_msb) +\
                                    " downto 0);"
                            out += "\n"
                        else:
                            same_connections_ports_names = \
                                sorted([aport.extended_name for
                                       aport in same_connections_ports])
                            if port.extended_name ==\
                                    same_connections_ports_names[0]:
                                out += ONETAB * 2 +\
                                    instancename + "_" + portname +\
                                    " : " + port.direction
                                if port.connected_msb < 1:
                                    out += " std_logic;"
                                else:
                                    out += " std_logic_vector(" +\
                                        str(port.connected_msb) +\
                                        " downto 0);"
                                out += "\n"
                    else:
                        # signal declaration
                        out += ONETAB * 2 +\
                            instancename + "_" + portname +\
                            " : " + port.direction
                        if port.connected_msb < 1:
                            out += " std_logic;"
                        else:
                            out += " std_logic_vector(" +\
                                str(port.connected_msb) +\
                                " downto 0);"
                        out += "\n"

                # port not completely connected
                else:
                    for pin in port.pins:
                        if pin.is_connected_to_inst(
                                self.project.platform):
                            out += ONETAB * 2 + \
                                instancename + "_" + portname + "_pin" +\
                                str(pin.num) + " : " +\
                                port.direction + " std_logic;\n"
        # Suppress the #!@ last semicolon
        out = out[:-2]

        out += "\n" + ONETAB + ");\nend entity " + entityname + ";\n\n"
        return out

    @classmethod
    def architectureHead(cls, entityname):
        """ head of architecture
        """
        out = "architecture " + entityname + "_1 of " + entityname + " is\n"
        return out

    @classmethod
    def architectureFoot(cls, entityname):
        """ architecture footer
        """
        out = "\nend architecture " + entityname + "_1;\n"
        return out

    def declareComponents(self):
        """ Declare components
        """
        if self.project.vhdl_version == "vhdl93":
            return ""
        out = ""
        out += ONETAB + "-------------------------\n"
        out += ONETAB + "-- declare components  --\n"
        out += ONETAB + "-------------------------\n"
        out += "\n"
        component = []
        for comp in self.project.instances:
            if comp.is_platform() is False:
                component.append(comp.name)

        # if multiple instance of the same component
        component = set(component)

        for compname in component:
            for component in self.project.instances:
                if component.name == compname:
                    break

            out += "\n" + ONETAB + "component " + compname + "\n"
            if component.fpga_generics != []:
                out += ONETAB * 2 + "generic(\n"
                for generic in component.fpga_generics:
                    out += ONETAB * 3 +\
                        generic.name + " : " +\
                        generic.generictype + " := " +\
                        str(generic.value) +\
                        ";\n"
                # suppress comma
                out = out[:-2] + "\n"
                out += ONETAB * 2 + ");\n"

            out += ONETAB * 2 + "port (\n"
            for interface in component.interfaces:
                out += ONETAB * 3 + "-- " + interface.name + "\n"
                for port in interface.ports:
                    if port.is_hidden:
                        continue
                    out += ONETAB * 3 +\
                        port.name +\
                        "  : " +\
                        port.direction
                    if int(port.size) == 1:
                        out += " std_logic;\n"
                    else:
                        out += " std_logic_vector(" +\
                            str(port.real_size - 1) +\
                            " downto " + port.min_pin_num + ");\n"
            # Suppress the #!@ last semicolon
            out = out[:-2] + "\n"
            out += ONETAB * 2 + ");\n"
            out += ONETAB + "end component;\n"
        return out

    def declareSignals(self, componentslist, incomplete_external_ports_list):
        """ Declare signals ports
        """
        platformname = self.project.platform.instancename
        out = ""
        out += ONETAB + "-------------------------\n"
        out += ONETAB + "-- Signals declaration --\n"
        out += ONETAB + "-------------------------\n"
        for component in componentslist:
            if component.is_platform() is True:
                continue
            out += "\n" + ONETAB + "-- " +\
                component.instancename + "\n"
            for interface in component.interfaces:
                out += ONETAB + "-- " + interface.name + "\n"

                for port in interface.ports:
                    if port.is_hidden:
                        continue
                    if port in incomplete_external_ports_list:
                        continue
                    if len(port.pins) == 0:
                        continue
                    connection_list = port.pins[0].connections
                    if len(connection_list) == 0:
                        continue
                    if connection_list[0]["instance_dest"] == platformname:
                        continue
                    out += ONETAB + "signal " +\
                        component.instancename +\
                        "_" + port.name + ": "
                    if int(port.size) == 1:
                        out += " std_logic;\n"
                    else:
                        out += " std_logic_vector(" +\
                               str(port.real_size - 1) +\
                               " downto " + port.min_pin_num + ");\n"

        out += "\n" + ONETAB + "-- void pins\n"

        for port in incomplete_external_ports_list:
            if port.force_defined():
                continue
            portname = port.name
            instancename = port.parent.parent.instancename
            out += "\n" + ONETAB + "signal " + instancename +\
                "_" + portname + ": std_logic_vector(" +\
                str(port.real_size - 1) + " downto 0);\n"
        return out

    def declareInstance(self):
        """ Declaring instances """
        out = ""
        out += ONETAB + "-------------------------\n"
        out += ONETAB + "-- declare instances\n"
        out += ONETAB + "-------------------------\n"
        for component in self.project.instances:
            if component.is_platform() is False:
                out += "\n" + ONETAB +\
                    component.instancename + " : "
                if self.project.vhdl_version == "vhdl93":
                    out += "entity work."
                out += component.name + "\n"
                if component.fpga_generics != []:
                    out += ONETAB + "generic map (\n"
                    for generic in component.fpga_generics:
                        out += ONETAB * 3 +\
                            generic.name + " => " +\
                            str(generic.value) +\
                            ",\n"
                    # suppress comma
                    out = out[:-2] + "\n"
                    out += ONETAB * 2 + ")\n"

                out += ONETAB + "port map (\n"
                for interface in component.interfaces:

                    out += ONETAB * 3 + "-- " + interface.name + "\n"
                    for port in interface.ports:
                        if port.is_hidden:
                            continue
                        out += ONETAB * 3 + port.name + " => "
                        if len(port.pins) != 0:
                            if (port.direction == "inout") or\
                                    (port.direction == "in"):
                                out +=\
                                    sorted(
                                        [aport.extended_name for aport in
                                         port.ports_with_same_connection]
                                        )[0]
                                out += ",\n"
                            else:
                                out += port.extended_name + ",\n"

                        else:
                            if port.direction == "out":
                                out += "open,\n"
                            else:
                                if int(port.size) == 1:
                                    out += "'" +\
                                        str(port.unconnected_value) +\
                                        "',\n"
                                else:
                                    out += "\"" +\
                                        str(port.unconnected_value) *\
                                        int(port.size) +\
                                        "\",\n"

                # Suppress the #!@ last comma
                out = out[:-2] + "\n"
                out += ONETAB * 3 + ");\n"
        out += "\n"
        return out

    @classmethod
    def connectForces(cls, portlist):
        """ Connecting Forces """
        out = "\n"
        out += ONETAB + "-------------------\n"
        out += ONETAB + "--  Set forces   --\n"
        out += ONETAB + "-------------------\n"
        for port in portlist:
            if port.is_hidden:
                continue
            if port.force_defined():
                if port.force == "gnd":
                    out += ONETAB + "force_" +\
                        port.name + " <= '0';\n"
                else:
                    out += ONETAB + "force_" +\
                        port.name + " <= '1';\n"
        return out + "\n"

    def connect_in_port(self, component, interface, port):
        """ Connect all pins port"""
        platform = self.project.platform
        platformname = platform.instancename
        out = ""
        if len(port.pins) != 0:
            portdest = port.dest_port
            if portdest is not None and\
                    (portdest.size == port.size):
                # If port is completely connected to one
                # and only one other port
                pin = port.pins[0]
                connect = pin.connections[0]
                if connect["instance_dest"] != platformname:
                    out += ONETAB * 2 +\
                        component.instancename +\
                        "_" + port.name +\
                        " <= " +\
                        connect["instance_dest"] +\
                        "_" + connect["port_dest"] + ";\n"
            else:
                # If pins port are connected individualy
                # to several other ports
                for pin in port.pins:
                    # Connect pin individualy
                    if pin.num is not None and\
                            len(pin.connections) != 0:
                        connect = pin.connections[0]
                        if connect["instance_dest"] != platformname:
                            out += ONETAB * 2 +\
                                component.instancename +\
                                "_" + port.name
                            if int(port.size) > 1:
                                out += "(" + pin.num + ")"
                            out += " <= " + connect["instance_dest"] +\
                                "_" + connect["port_dest"]
                            # is destination vector or simple net ?
                            for comp in self.project.instances:
                                if comp.instancename !=\
                                        connect["instance_dest"]:
                                    continue
                                for inter in comp.interfaces:
                                    if inter.name !=\
                                            connect["interface_dest"]:
                                        continue
                                    for port2 in inter.ports:
                                        if port2.name ==\
                                                connect["port_dest"]:
                                            if int(port2.size) > 1:
                                                out += "(" + \
                                                    connect["pin_dest"] + ")"
                            out += ";\n"
        # if port is void, connect '0' or open
        else:
            message = "port " + component.instancename +\
                "." + interface.name + "." +\
                port.name + " is void." +\
                " It will be set to '" +\
                str(port.unconnected_value) + "'"
            DISPLAY.msg(message, 2)
        return out

    def connectInstance(self, incomplete_external_ports_list):
        """ Connect instances
        """
        out = ""
        out += ONETAB + "---------------------------\n"
        out += ONETAB + "-- instances connections --\n"
        out += ONETAB + "---------------------------\n"

        platform = self.project.platform
        platformname = platform.instancename
        # connect incomplete_external_ports_list
        for port in incomplete_external_ports_list:
            if port.is_hidden:
                continue
            if not port.force_defined():
                portname = port.name
                instancename = port.parent.parent.instancename
                out += "\n" + ONETAB +\
                    "-- connect incomplete external port " +\
                    str(portname) + " pins\n"
                for pinnum in range(port.real_size):
                    pin = port.get_pin(pinnum)
                    if pin.is_connected_to_inst(platform):
                        if port.direction == "in":
                            out += ONETAB + instancename + "_" +\
                                portname + "(" + str(pinnum) +\
                                ") <= " + instancename + "_" +\
                                portname + "_pin" +\
                                str(pinnum) + ";\n"
                        else:
                            out += ONETAB + instancename + "_" +\
                                portname + "_pin" +\
                                str(pinnum) + " <= " + instancename +\
                                "_" + portname + "(" +\
                                str(pinnum) + ");\n"

        # connect all "in" ports pin
        for component in self.project.instances:
            if component.is_platform():
                continue
            out += "\n" + ONETAB + "-- connect " +\
                component.instancename + "\n"
            for interface in component.interfaces:
                out += ONETAB * 2 + "-- " + interface.name + "\n"
                for port in interface.ports:
                    if port.direction == "in":
                        out += self.connect_in_port(component, interface, port)
        return out

    @classmethod
    def architectureBegin(cls):
        """ Write architecture begin """
        return "\nbegin\n"
