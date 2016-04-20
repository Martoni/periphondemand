#! /usr/bin/python3
# -*- coding: utf-8
# ----------------------------------------------------------------------------
# Name:     Platform.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  28/04/2008
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
""" Platform management """

from periphondemand.bin.utils.poderror import PodError

from periphondemand.bin.core.component import Component
from periphondemand.bin.core.interface import Interface
from periphondemand.bin.core.simulationlib import SimulationLib


class Platform(Component):
    """ This class manage platform dependances
        attributes:
            tree            -- the XML root
            interfacelist   -- list objects containing platforms constraints
    """

    def __init__(self, parent, **keys):
        """ Init Component,
            __init__(self, parent, node)
            __init__(self, parent, file)
        """
        if "node" in keys:
            Component.__init__(self, parent, node=keys["node"])
        elif "file" in keys:
            Component.__init__(self, parent, afile=keys["file"])
        else:
            raise PodError("Keys unknown in Platform constructor", 0)

        if self.get_node("interfaces") is not None:
            for element in self.get_node("interfaces").get_nodes("interface"):
                self._interfaceslist.append(Interface(self, node=element))
        self.librarieslist = []
        if self.get_node("simulation") is not None:
            for library in self.get_node("simulation").get_nodes("simlib"):
                self.librarieslist.append(SimulationLib(self, node=library))

        self.instancename = self.name
        self.parent = parent

    @property
    def forces(self):
        """ get the list of forces """
        forcelist = []
        interfaces_list = self.interfaces
        if len(interfaces_list) != 1:
            raise PodError("I found " + str(len(interfaces_list)) +
                           " FPGAs (" + str(interfaces_list) +
                           ") and multiple FPGA project " +
                           " is not implemented yet.")
        for port in interfaces_list[0].ports:
            if port.force_defined():
                forcelist.append(port)
        return forcelist

    @property
    def components(self):
        """ Return platform dependent components list """
        componentslist = []
        try:
            for element in self.get_subnodes("components", "component"):
                component = element.get_attr_value("name").split("/")
                componentslist.append({"type": component[0],
                                       "name": component[1]})
        except AttributeError:
            pass
        return componentslist

    def save(self):
        """ platform component is in project file
        then, no save
        """
        pass

    def load(self, name):
        """ Load platform
        """
        pass

    @property
    def connect_ports(self):
        """ Return the list of port to be connected out of Platform
            [portlist]
        """
        portlist = []
        # loop for each connection in platform interface
        for interface in self.interfaces:
            for port in interface.ports:
                # add forced port in list
                if port.force_defined():
                    portlist.append(port)
                else:
                    for port in port.dest_ports:
                        if port not in portlist:
                            portlist.append(port)
        return portlist

    @property
    def incomplete_ext_ports(self):
        """ Return the list of incomplete in or
            inout port connected on platform
        """
        incomplete_port_list = []
        for port in self.connect_ports:
            if port.direction != "out":
                if not port.is_fully_connected():
                    incomplete_port_list.append(port)
        return incomplete_port_list

    @property
    def libraries(self):
        """ Get the library list """
        try:
            return self.librarieslist
        except AttributeError:
            return []

    @property
    def board_part(self):
        """ get the board part name """
        return self.get_node("fpga").get_attr_value("board_part")

    @property
    def family(self):
        """ get the family name """
        return self.get_node("fpga").get_attr_value("family")

    @property
    def device(self):
        """ get device name """
        return self.get_node("fpga").get_attr_value("device")

    @device.setter
    def device(self, device):
        """ set device name """
        self.get_node("fpga").set_attr("device", device)

    @property
    def package(self):
        """ get package name """
        return self.get_node("fpga").get_attr_value("package")

    @property
    def pin_count(self):
        """ get package pin_count """
        return self.get_node("fpga").get_attr_value("pin_count")

    @property
    def speed(self):
        """ get speed """
        return self.get_node("fpga").get_attr_value("speed")

    @speed.setter
    def speed(self, speed):
        """ set speed """
        return self.get_node("fpga").set_attr("speed", speed)

    @property
    def main_clock(self):
        """ get main clock """
        return self.get_node("fpga").get_attr_value("main_clock")

    @property
    def clocks(self):
        """ get list of clocks and frequency """
        output_clk_list = []
        list_clocks = self.get_subnodes("clocks", "clock")
        for clock in list_clocks:
            for interface in self.interfaces:
                try:
                    port = interface.get_port(clock.name)
                    if port.get_pin(0).connections != []:
                        pin_conn = port.get_pin(0).connections[0]
                        pin_name = pin_conn["instance_dest"] + "_" + \
                            pin_conn["port_dest"]
                        output_clk_list.append(
                            {"name": pin_name,
                             "frequency":
                             str(clock.get_attr_value("frequency"))})
                except PodError:
                    continue
        return output_clk_list

    @classmethod
    def is_platform(cls):
        """ is it a platform instance ? """
        return True

    @property
    def platform_ports(self):
        """ Get all port in platform """
        portslist = []
        for interface in self.interfaces:
            for port in interface.ports:
                portslist.append(port)
        return portslist

    @property
    def output_format(self):
        """ get speed """
        return self.get_node("fpga").get_attr_value("out_bin")
