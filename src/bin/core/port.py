#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Port.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/04/2008
# ----------------------------------------------------------------------------
#  Copyright (2008)  Armadeus Systems
#
# This program is free software; you an redistribute it and/or modify
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
# Revision list :
#
# Date       By        Changes
#
# ----------------------------------------------------------------------------

__doc__ = ""
__version__ = "1.0.0"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.poderror import PodError

from periphondemand.bin.core.pin import Pin


class Port(WrapperXml):
    """ Manage port
        attributes:
            pinlist -- list of pin
    """

    def __init__(self, parent, **keys):
        """ Init port,
            __init__(self,parent,name)
            __init__(self,parent,wxml)
        """
        if "name" in keys:
            self.__initname(keys["name"])
        elif "node" in keys:
            self.__initnode(keys["node"])
        else:
            raise PodError("Keys not known in Port ", 0)

        self.parent = parent
        self.pinlist = []
        for element in self.getNodeList("pin"):
            pin = Pin(self, node=element)
            self.pinlist.append(pin)

    def __initname(self, name):
        WrapperXml.__init__(self, nodename="port")
        self.setAttribute("name", name)

    def __initnode(self, node):
        WrapperXml.__init__(self, node=node)

    def getExtendedName(self):
        """ Get name in this format:
            instancename_portname
        """
        instancename = self.parent.parent.getInstanceName()
        interfacename = self.parent.getName()
        return instancename + "_" + self.getName()

    def getPinsList(self):
        return self.pinlist

    def addPin(self, pin):
        """ Connect an object Pin in Port
            attributes:
                pin -- object Pin()
        """
        if pin.isAll() and len(self.pinlist) == 1:
            if self.pinlist[0].isAll():
                return self.pinlist[0]
        else:
            for pintmp in self.pinlist:
                if pintmp.getNum() == pin.getNum():
                    return pintmp
        self.pinlist.append(pin)
        self.addNode(node=pin)
        return pin

    def delPin(self, pin_num):
        """ delete a pin
        """
        pin = self.getPin(pin_num)
        if pin.getConnections() != []:
            raise PodError("Pin " +
                        str(self.parent.parent.getInstanceName()) +
                        "." +
                        str(self.parent.getName()) +
                        "." +
                        str(self.getName()) +
                        "." +
                        str(pin_num) +
                        " can't be deleted, connections exists")
        self.pinlist.remove(pin)
        self.delNode(pin)

    def getSize(self):
        """ return port size
        """
        size = WrapperXml.getSize(self)
        if size.isdigit():
            return size
        else:
            return self.parent.parent.getGeneric(str(size)).getValue()

    def getPin(self, num):
        """ return pin node
        """
        if int(num) >= self.getSize():
            raise PodError("Pin number " + str(num) + " not in port size")
        for pin in self.getPinsList():
            if pin.getNum() == str(num):
                return pin
        pin = Pin(self, num=str(num))
        self.pinlist.append(pin)
        self.addNode(node=pin)
        return pin

    def getType(self):
        return self.getAttributeValue("type")

    def setType(self, the_type):
        #TODO: check if type is known
        self.setAttribute("type", the_type)

    def getDir(self):
        return self.getAttributeValue("dir")

    def getUnconnectedValue(self):
        try:
            ucvalue = self.getAttributeValue("unconnected_value")
            if ucvalue is None:
                return "0"
            else:
                return ucvalue
        except PodError:
            return "0"

    def set_unconnected_value(self, value):
        if self.getDir() != "in":
            raise PodError("Unconnected Value can be set only on 'in' port", 0)
        if str(value).isdigit():
            if int(value) in [0, 1]:
                self.setAttribute("unconnected_value", str(value))
            else:
                raise PodError("Wrong value : " + str(value), 0)
        else:
            raise PodError("Wrong value : " + str(value), 0)

    def setDir(self, direction):
        if not direction.lower() in ["out", "in", "inout"]:
            raise PodError("Direction wrong : " + str(direction))
        self.setAttribute("dir", direction)

    def getPortOption(self):
        return self.getAttributeValue("port_option")

    def setPortOption(self, port_option):
        self.setAttribute("port_option", port_option)

    def getStandard(self):
        return self.getAttributeValue("standard")

    def setStandard(self, standard):
        self.setAttribute("standard", standard)

    def setDrive(self, drive):
        self.setAttribute("drive", drive)

    def getDrive(self):
        return self.getAttributeValue("drive")

    @property
    def force(self):
        return self.getAttributeValue("force")

    @force.setter
    def force(self, force):
        """ Setting force for this port """
        listofpins = self.getPinsList()
        if len(listofpins) > 1:
            raise PodError("Force multiple pin port is not implemented")
        if len(listofpins) == 1:
            raise PodError("This pin is already connected")

        forcevalues = ["gnd", "vcc", "undef"]
        if force in forcevalues:
            self.setAttribute("force", force)
        else:
            raise PodError("force value must be in " + str(forcevalues))

    def forceDefined(self):
        try:
            force = self.force
        except PodError:
            return False
        forcevalues = ["gnd", "vcc"]
        if force in forcevalues:
            return True
        return False

    def getPosition(self):
        return self.getAttributeValue("position")

    def setPosition(self, position):
        self.setAttribute("position", position)

    def getFreq(self):
        freq = self.getAttributeValue("freq")
        if freq is None:
            raise PodError("No frequency attribute for " + self.getName())
        return freq

    def isvariable(self):
        try:
            if self.getAttributeValue("variable_size") == "1":
                return 1
            else:
                return 0
        except AttributeError:
            return 0

    def checkVariablePort(self):
        """ check if variable port is correctly connected.
            Connections on variable port must begin at pin 0
            and must be followed.
            ex: 0, 1, 2, 3, …
        """
        if self.isvariable():
            listofpin = self.getPinsList()
            if listofpin == []:
                return True
            tab = []
            for pin in listofpin:
                if pin.getNum() is not None:
                    tab.append(int(pin.getNum()))
            tab.sort()
            if (len(tab) - 1) != tab[-1]:
                return False
            return True
        else:
            return True

    def getRealSize(self):
        """ if port is variable, return the size set by generic"""
        if self.isvariable():
            return str(int(self.getMaxPinNum()) + 1)
        else:
            return str(self.getSize())

    def getMaxPinNum(self):
        """ return the max num pin value
        """
        num = "0"
        listofpin = self.getPinsList()
        if listofpin == []:
            return str(int(self.getSize()) - 1)
        for pin in listofpin:
            if pin.getNum() is None:
                return str(int(self.getSize()) - 1)
            if int(pin.getNum()) > int(num):
                num = pin.getNum()
        return num

    def getMinPinNum(self):
        """ return the min pin value
        """
        num = self.getSize()
        listofpin = self.getPinsList()
        if listofpin == []:
            return "0"
        for pin in self.getPinsList():
            if pin.getNum() is None:
                return "0"
            if int(pin.getNum()) < int(num):
                num = pin.getNum()
        return num

    def checkConnection(self, portdest):
        """ Check the compatibility between the two pin with following rules:
        src\dest|  out in  inout lock clock
        ------------------------------------
        out     |   x   v    v     x    x
        in      |   v   v    v     x    v
        inout   |   v   v    v     x    x
        lock    |   v   v    v     x    x
        clock   |   x   v    x     x    x
        """
        listdir = ["out", "in", "inout", "lock", "clock"]
        checktab = ((0, 1, 1, 0, 0),
                    (1, 1, 1, 0, 1),
                    (1, 1, 1, 0, 0),
                    (1, 1, 1, 0, 0),
                    (0, 1, 0, 0, 0))

        if checktab[
                listdir.index(self.getDir())][
                        listdir.index(portdest.getDir())] == 0:
            raise PodError("incompatible pin : " +
                        self.getDir() + " => " + portdest.getDir(), 0)

    def connect_port(self, port_dest):
        """ Connect all pins of a port on all pin on same size port dest
        """
        size = self.getSize()
        if size != port_dest.getSize():
            raise PodError("The two ports have differents size")
        if self.getPinsList() != []:
            raise PodError("Port connection " +
                        self.getName() + " is not void")
        if port_dest.getPinsList() != []:
            raise PodError("Port connection " +
                        port_dest.getName() + " is not void")

        self.connectAllPin(port_dest)

    def connectAllPin(self, port_dest):
        """ Connect all port pin to a destination instance
        """
        for pin_num in range(int(self.getSize())):
            pin_source = self.getPin(pin_num)
            pin_dest = port_dest.getPin(pin_num)
            pin_source.connectPin(pin_dest)

    def autoconnectPin(self):
        """ If there are platform defaut connection
            in this port, autoconnect it
        """
        for pin in self.getPinsList():
            pin.autoconnectPin()

    def getDestinationPort(self):
        """ get destination port connected to this port
            if only one port connected
        """
        port_list = self.getDestinationPortList()
        if len(port_list) == 1:
            return port_list[0]
        else:
            return None

    def getDestinationPortList(self):
        """ Get a list of destination ports
        """
        port_dest = None
        dest_port_list = []
        for pin in self.getPinsList():
            port_connections = \
                    [pin.parent for pin in pin.getConnectedPinList()]
            for port_connect in port_connections:
                if port_connect not in dest_port_list:
                    dest_port_list.append(port_connect)

        return dest_port_list

    def getPortsWithSameConnection(self):
        """ Return a list of ports that are connected on sames pin.
            only works with port on externals I/O (platform). If only this
            one port is connected to one pin, self port is returned.
        """
        pin_dest_list = self.getPin(0).getConnectedPinList()
        if (len(pin_dest_list) == 0):
            return []
        first_pin = pin_dest_list[0]
        return [pin.parent for pin in first_pin.getConnectedPinList()]

    def getMSBConnected(self):
        """Return the MSB that is connected to an another pin
        """
        num = -1
        for pin in self.getPinsList():
            if pin.isConnected():
                if int(pin.getNum()) > num:
                    num = int(pin.getNum())
        return num

    def isVoid(self):
        """ Return False if at less one pin is connected
            on another pin
        """
        for pin in self.getPinsList():
            if pin.isConnected():
                return False
        return True

    def isCompletelyConnected(self):
        """ return True if all pin has connection"""
        if len(self.getPinsList()) != int(self.getSize()):
            return False
        for pin in self.getPinsList():
            if not pin.isConnected():
                return False
        return True
