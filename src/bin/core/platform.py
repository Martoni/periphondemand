#! /usr/bin/python
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
            Component.__init__(self, node=keys["node"])
        elif "file" in keys:
            Component.__init__(self, afile=keys["file"])
        else:
            raise PodError("Keys unknown in Platform constructor", 0)

        if self.getNode("interfaces") is not None:
            for element in self.getNode("interfaces").getNodeList("interface"):
                self._interfaceslist.append(Interface(self, node=element))
        self.librarieslist = []
        if self.getNode("simulation") is not None:
            for library in self.getNode("simulation").getNodeList("simlib"):
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
                component = element.getAttributeValue("name").split("/")
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
    def family(self):
        """ get the family name """
        return self.getNode("fpga").getAttributeValue("family")

    @property
    def device(self):
        """ get device name """
        return self.getNode("fpga").getAttributeValue("device")

    @device.setter
    def device(self, device):
        """ set device name """
        self.getNode("fpga").setAttribute("device", device)

    @property
    def package(self):
        """ get package name """
        return self.getNode("fpga").getAttributeValue("package")

    @property
    def speed(self):
        """ get speed """
        return self.getNode("fpga").getAttributeValue("speed")

    @speed.setter
    def speed(self, speed):
        """ set speed """
        return self.getNode("fpga").setAttribute("speed", speed)

    @property
    def main_clock(self):
        """ get main clock """
        return self.getNode("fpga").getAttributeValue("main_clock")

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
