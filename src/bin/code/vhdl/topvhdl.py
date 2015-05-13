#! /usr/bin/python
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
from periphondemand.bin.utils.error import PodError

import datetime

SETTINGS = Settings()
DISPLAY = Display()


class TopVHDL(TopGen):
    """ Generate VHDL Top component
    """

    def __init__(self, project):
        TopGen.__init__(self, project)

    @classmethod
    def header(cls):
        """ return vhdl header
        """
        header = open(SETTINGS.path + TEMPLATESPATH +
                      "/" + HEADERTPL, "r").read()
        header = header.replace("$tpl:author$", SETTINGS.author)
        header = header.replace("$tpl:date$", str(datetime.date.today()))
        header = header.replace("$tpl:filename$",
                                "Top_" +
                                SETTINGS.active_project.getName() + ".vhd")
        header = header.replace(
                    "$tpl:abstract$",
                    SETTINGS.active_project.getDescription())
        return header

    def entity(self, entityname, portlist):
        """ return VHDL code for Top entity
        """
        out = "entity " + entityname + " is\n"
        out = out + "\n" + ONETAB + "port\n" + ONETAB + "(\n"
        for port in portlist:
            if port.forceDefined():
                portname = "force_" + port.getName()
                out = out + ONETAB * 2 + portname + " : out std_logic;\n"
            else:
                portname = port.getName()
                interfacename = port.parent.getName()
                instancename = port.parent.parent.getInstanceName()

                out = out + ONETAB + "-- " + instancename +\
                                  "-" + interfacename + "\n"
                if port.isCompletelyConnected():
                    if (port.getDir() == "in") or (port.getDir() == "inout"):
                        same_connections_ports =\
                            port.getPortsWithSameConnection()
                        if same_connections_ports == []:
                            raise PodError(str(port.getExtendedName()) +
                                        " is left unconnected")
                        elif len(same_connections_ports) == 1:
                            out = out + ONETAB * 2 +\
                                  instancename + "_" + portname +\
                                  " : " + port.getDir()
                            if port.getMSBConnected() < 1:
                                out = out + " std_logic;"
                            else:
                                out = out + " std_logic_vector(" +\
                                          str(port.getMSBConnected()) +\
                                          " downto 0);"
                            out = out + "\n"
                        else:
                            same_connections_ports_names = \
                                sorted([aport.getExtendedName() for
                                            aport in same_connections_ports])
                            if port.getExtendedName() ==\
                                    same_connections_ports_names[0]:
                                out = out + ONETAB * 2 +\
                                        instancename + "_" + portname +\
                                        " : " + port.getDir()
                                if port.getMSBConnected() < 1:
                                    out = out + " std_logic;"
                                else:
                                    out = out + " std_logic_vector(" +\
                                              str(port.getMSBConnected()) +\
                                              " downto 0);"
                                out = out + "\n"
                    else:
                        # signal declaration
                        out = out + ONETAB * 2 +\
                                instancename + "_" + portname +\
                                " : " + port.getDir()
                        if port.getMSBConnected() < 1:
                            out = out + " std_logic;"
                        else:
                            out = out + " std_logic_vector(" +\
                                    str(port.getMSBConnected()) +\
                                    " downto 0);"
                        out = out + "\n"

                # port not completely connected
                else:
                    for pin in port.getPinsList():
                        if pin.isConnectedToInstance(
                                self.project.platform):
                            out = out + ONETAB * 2 + \
                                instancename + "_" + portname + "_pin" +\
                                str(pin.getNum()) + " : " +\
                                port.getDir() + " std_logic;\n"
       # Suppress the #!@ last semicolon
        out = out[:-2]

        out = out + "\n" + ONETAB + ");\nend entity " + entityname + ";\n\n"
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
        out = out + ONETAB + "-------------------------\n"
        out = out + ONETAB + "-- declare components  --\n"
        out = out + ONETAB + "-------------------------\n"
        out = out + "\n"
        component = []
        for comp in self.project.instances:
            if comp.getName() != "platform":
                component.append(comp.getName())

        # if multiple instance of the same component
        component = set(component)

        for compname in component:
            for component in self.project.instances:
                if component.getName() == compname:
                    break

            out = out + "\n" + ONETAB + "component " + compname + "\n"
            if component.getFPGAGenericsList() != []:
                out = out + ONETAB * 2 + "generic(\n"
                for generic in component.getFPGAGenericsList():
                    out = out + ONETAB * 3 +\
                          generic.getName() + " : " +\
                          generic.getType() + " := " +\
                          str(generic.getValue()) +\
                          ";\n"
                # suppress comma
                out = out[:-2] + "\n"
                out = out + ONETAB * 2 + ");\n"

            out = out + ONETAB * 2 + "port (\n"
            for interface in component.getInterfacesList():
                out = out + ONETAB * 3 + "-- " + interface.getName() + "\n"
                for port in interface.ports:
                    out = out + ONETAB * 3 +\
                          port.getName() +\
                          "  : " +\
                          port.getDir()
                    if int(port.getSize()) == 1:
                        out = out + " std_logic;\n"
                    else:
                        out = out + " std_logic_vector(" +\
                              str(int(port.getRealSize()) - 1) +\
                              " downto " + port.getMinPinNum() + ");\n"
            # Suppress the #!@ last semicolon
            out = out[:-2] + "\n"
            out = out + ONETAB * 2 + ");\n"
            out = out + ONETAB + "end component;\n"
        return out

    def declareSignals(self, componentslist, incomplete_external_ports_list):
        """ Declare signals ports
        """
        platformname = self.project.platform.getInstanceName()
        out = ""
        out = out + ONETAB + "-------------------------\n"
        out = out + ONETAB + "-- Signals declaration\n"
        out = out + ONETAB + "-------------------------\n"
        for component in componentslist:
            if component.getName() == "platform":
                continue
            out = out + "\n" + ONETAB + "-- " + component.getInstanceName() + "\n"
            for interface in component.getInterfacesList():
                out = out + ONETAB + "-- " + interface.getName() + "\n"

                for port in interface.ports:
                    if port in incomplete_external_ports_list:
                        continue
                    if len(port.getPinsList()) == 0:
                        continue
                    connection_list = port.getPinsList()[0].getConnections()
                    if len(connection_list) == 0:
                        continue
                    if connection_list[0]["instance_dest"] == platformname:
                        continue
                    out = out + ONETAB + "signal " + component.getInstanceName() +\
                               "_" + port.getName() + ": "
                    if int(port.getSize()) == 1:
                        out = out + " std_logic;\n"
                    else:
                        out = out +\
                               " std_logic_vector(" +\
                               port.getMaxPinNum() +\
                               " downto " + port.getMinPinNum() + ");\n"

        out = out + "\n" + ONETAB + "-- void pins\n"

        for port in incomplete_external_ports_list:
            if port.forceDefined():
                continue
            portname = port.getName()
            instancename = port.parent.parent.getInstanceName()
            out = out + "\n" + ONETAB + "signal " + instancename +\
                        "_" + portname + ": std_logic_vector(" +\
                        str(int(port.getRealSize()) - 1) + " downto 0);\n"

        return out

    def declareInstance(self):
        """ Declaring instances """
        out = ""
        out = out + ONETAB + "-------------------------\n"
        out = out + ONETAB + "-- declare instances\n"
        out = out + ONETAB + "-------------------------\n"
        for component in self.project.instances:
            if component.getName() != "platform":
                out = out + "\n" + ONETAB + component.getInstanceName()\
                        + " : "
                if self.project.vhdl_version == "vhdl93":
                    out = out + "entity work."
                out = out + component.getName() + "\n"
                if component.getFPGAGenericsList() != []:
                    out = out + ONETAB + "generic map (\n"
                    for generic in component.getFPGAGenericsList():
                        out = out + ONETAB * 3 +\
                              generic.getName() + " => " +\
                              str(generic.getValue()) +\
                              ",\n"
                    # suppress comma
                    out = out[:-2] + "\n"
                    out = out + ONETAB * 2 + ")\n"

                out = out + ONETAB + "port map (\n"
                for interface in component.getInterfacesList():

                    out = out + ONETAB * 3 + "-- " + interface.getName() + "\n"
                    for port in interface.ports:
                        out = out + ONETAB * 3 + port.getName() + " => "
                        if len(port.getPinsList()) != 0:
                            if (port.getDir() == "inout") or\
                                    (port.getDir() == "in"):
                                out = out +\
                                    sorted(
                                        [aport.getExtendedName()
                                            for aport in
                                                port.getPortsWithSameConnection()]
                                        )[0]
                                out = out + ",\n"
                            else:
                                out = out + port.getExtendedName() + ",\n"

                        else:
                            if port.getDir() == "out":
                                out = out + "open,\n"
                            else:
                                if int(port.getSize()) == 1:
                                    out = out + "'" +\
                                            str(port.getUnconnectedValue()) +\
                                            "',\n"
                                else:
                                    out = out + "\"" +\
                                            str(port.getUnconnectedValue()) *\
                                            int(port.getSize()) +\
                                            "\",\n"

                # Suppress the #!@ last comma
                out = out[:-2] + "\n"
                out = out + ONETAB * 3 + ");\n"
        out = out + "\n"
        return out
    @classmethod
    def connectForces(cls, portlist):
        """ Connecting Forces """
        out = "\n"
        out = out + ONETAB + "-------------------\n"
        out = out + ONETAB + "--  Set forces   --\n"
        out = out + ONETAB + "-------------------\n"
        for port in portlist:
            if port.forceDefined():
                if port.force == "gnd":
                    out = out + ONETAB + "force_" + port.getName() + " <= '0';\n"
                else:
                    out = out + ONETAB + "force_" + port.getName() + " <= '1';\n"
        return out + "\n"

    def connectInstance(self, incomplete_external_ports_list):
        """ Connect instances
        """
        out = ""
        out = out + ONETAB + "---------------------------\n"
        out = out + ONETAB + "-- instances connections --\n"
        out = out + ONETAB + "---------------------------\n"

        platform = self.project.platform
        platformname = platform.getInstanceName()
        # connect incomplete_external_ports_list
        for port in incomplete_external_ports_list:
            if not port.forceDefined():
                portname = port.getName()
                instancename = port.parent.parent.getInstanceName()
                out = out + "\n" + ONETAB +\
                        "-- connect incomplete external port " +\
                        str(portname) + " pins\n"
                for pinnum in range(int(port.getRealSize())):
                    pin = port.getPin(pinnum)
                    if pin.isConnectedToInstance(platform):
                        if port.getDir() == "in":
                            out = out + ONETAB + instancename + "_" +\
                                  portname + "(" + str(pinnum) +\
                                  ") <= " + instancename + "_" +\
                                  portname + "_pin" +\
                                  str(pinnum) + ";\n"
                        else:
                            out = out + ONETAB + instancename + "_" +\
                                    portname + "_pin" +\
                                    str(pinnum) + " <= " + instancename +\
                                    "_" + portname + "(" +\
                                    str(pinnum) + ");\n"

        # connect all "in" ports pin
        for component in self.project.instances:
            if component.getInstanceName() == platformname:
                continue
            out = out + "\n" + ONETAB + "-- connect " +\
                    component.getInstanceName() + "\n"
            for interface in component.getInterfacesList():
                out = out + ONETAB * 2 + "-- " + interface.getName() + "\n"
                for port in interface.ports:
                    if port.getDir() == "in":
                        # Connect all pins port
                        if len(port.getPinsList()) != 0:
                            portdest = port.getDestinationPort()
                            if portdest is not None and\
                                   (portdest.getSize() == port.getSize()):
                                # If port is completely connected to one
                                # and only one other port
                                pin = port.getPinsList()[0]
                                connect = pin.getConnections()[0]
                                if connect["instance_dest"] != platformname:
                                    out = out + ONETAB * 2 +\
                                          component.getInstanceName() +\
                                          "_" + port.getName() +\
                                          " <= " +\
                                          connect["instance_dest"] +\
                                          "_" + connect["port_dest"] + ";\n"
                            else:
                                # If pins port are connected individualy
                                # to several other ports
                                for pin in port.getPinsList():
                                    # Connect pin individualy
                                    if pin.getNum() is not None and\
                                            len(pin.getConnections()) != 0:
                                        connect = pin.getConnections()[0]
                                        if connect["instance_dest"] != platformname:
                                            out = out + ONETAB * 2 +\
                                                  component.getInstanceName() +\
                                                  "_" + port.getName()
                                            if int(port.getSize()) > 1:
                                                out = out + "(" + pin.getNum() + ")"
                                            out = out + " <= " + connect["instance_dest"] +\
                                                    "_" + connect["port_dest"]
                                            # is destination vector or simple net ?
                                            for comp in self.project.instances:
                                                if comp.getInstanceName() != connect["instance_dest"]:
                                                    continue
                                                for inter in comp.getInterfacesList():
                                                    if inter.getName() != connect["interface_dest"]:
                                                        continue
                                                    for port2 in inter.ports:
                                                        if port2.getName() == connect["port_dest"]:
                                                            if int(port2.getSize()) > 1:
                                                                out = out + "(" + \
                                                                        connect["pin_dest"] + ")"
                                            out = out + ";\n"
                        # if port is void, connect '0' or open
                        else:
                            message = "port " + component.getInstanceName() +\
                                      "." + interface.getName() + "." +\
                                      port.getName() + " is void." +\
                                      " It will be set to '" +\
                                      str(port.getUnconnectedValue()) + "'"
                            DISPLAY.msg(message, 2)

        return out

    @classmethod
    def architectureBegin(cls):
        """ Write architecture begin """
        return "\nbegin\n"
