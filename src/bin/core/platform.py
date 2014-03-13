#! /usr/bin/python
# -*- coding: utf-8
#-----------------------------------------------------------------------------
# Name:     Platform.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  28/04/2008
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
# Revision list :
# Date       By        Changes
#
#-----------------------------------------------------------------------------

__doc__ = ""
__version__ = "1.0.0"
__versionTime__ = "28/04/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.error import Error
from periphondemand.bin.utils import wrappersystem as sy

from periphondemand.bin.core.component import Component
from periphondemand.bin.core.interface import Interface
from periphondemand.bin.core.simulationlib import SimulationLib

settings = Settings()


class Platform(Component):
    """ This class manage platform dependances
        attributes:
            tree            -- the XML root
            interfacelist   -- list objects containing platforms constraints
    """

    def __init__(self, parent, **keys):
        """ Init Component,
            __init__(self,parent,node)
            __init__(self,parent,file)
        """
        Component.__init__(self, parent)
        if "node" in keys:
            self.__initnode(keys["node"])
        elif "file" in keys:
            self.__initfile(keys["file"])
        else:
            raise Error("Keys unknown in Platform constructor", 0)

        if self.getNode("interfaces") is not None:
            for element in self.getNode("interfaces").getNodeList("interface"):
                self.interfaceslist.append(Interface(self, node=element))
        self.librarieslist = []
        if self.getNode("simulation") is not None:
            for library in self.getNode("simulation").getNodeList("simlib"):
                self.librarieslist.append(SimulationLib(self, node=library))

    def __initnode(self, node):
        WrapperXml.__init__(self, node=node)

    def __initfile(self, file):
        WrapperXml.__init__(self, file=file)

    def getForcesList(self):
        forcelist = []
        interfaces_list = self.getInterfacesList()
        if len(interfaces_list) != 1:
            raise Error("I found " + str(len(interfaces_list)) +
                        " FPGAs (" + str(interfaces_list) +
                        ") and multiple FPGA project is not implemented yet.")
        for port in interfaces_list[0].getPortsList():
            if port.forceDefined():
                forcelist.append(port)
        return forcelist

    def getComponentsList(self):
        """ Return platform dependent components list
        """
        componentslist = []
        try:
            for element in self.getSubNodeList("components", "component"):
                component = element.getAttributeValue("name").split("/")
                componentslist.append({"type": component[0],
                                       "name": component[1]})
        except AttributeError:
            pass
        return componentslist

    def delComponent(self):
        """ suppress platform instance
        """
        self.tree = None

    def saveInstance(self):
        """ platform component is in project file
        then, no save
        """
        pass

    def loadInstance(self, name):
        """ Load platform
        """
        pass

    def getInstanceName(self):
        return Component.getName(self)

    def getName(self):
        return "platform"

    def getConnectPortsList(self):
        """ Return the list of port to be connected out of Platform
            [portlist]
        """
        portlist = []
        # loop for each connection in platform interface
        for interface in self.getInterfacesList():
            for port in interface.getPortsList():
                # add forced port in list
                if port.forceDefined():
                    portlist.append(port)
                else:
                    for port in port.getDestinationPortList():
                        if port not in portlist:
                            portlist.append(port)
        return portlist

    def getIncompleteExternalPortsList(self):
        """ Return the list of incomplete in or
            inout port connected on platform
        """
        incomplete_port_list = []
        for port in self.getConnectPortsList():
            if port.getDir() != "out":
                if not port.isCompletelyConnected():
                    incomplete_port_list.append(port)
        return incomplete_port_list

    def getLibrariesList(self):
        try:
            return self.librarieslist
        except AttributeError, error:
            return []

    def getFamily(self):
        return self.getNode("fpga").getAttributeValue("family")

    def getDevice(self):
        return self.getNode("fpga").getAttributeValue("device")

    def setDevice(self, device):
        self.getNode("fpga").setAttribute("device", device)

    def getPackage(self):
        return self.getNode("fpga").getAttributeValue("package")

    def getSpeed(self):
        return self.getNode("fpga").getAttributeValue("speed")

    def setSpeed(self, speed):
        return self.getNode("fpga").setAttribute("speed", speed)

    def getMainClock(self):
        return self.getNode("fpga").getAttributeValue("main_clock")

    def isPlatform(self):
        return True

    def getPlatformPortsList(self):
        """ Get all port in platform """
        portslist = []
        for interface in self.getInterfacesList():
            for port in interface.getPortsList():
                portslist.append(port)
        return portslist
