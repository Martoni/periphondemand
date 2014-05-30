#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Pin.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  05/05/2008
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
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------
""" Class that manage pins """

__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.error import Error

settings = Settings()


class Pin(WrapperXml):
    """ Manage Pin
        attributes:

    """

    def __init__(self, parent, **keys):
        """ init Pin,
            __init__(self,parent,node)
            __init__(self,parent,num)
        """
        if "node" in keys:
            self.__initnode(keys["node"])
        elif "num" in keys:
            self.__initnum(keys["num"])
        else:
            raise Error("Keys unknown in Pin", 0)
        self.parent = parent

    def __initnode(self, node):
        WrapperXml.__init__(self, node=node)

    def __initnum(self, num):
        WrapperXml.__init__(self, nodename="pin")
        self.setNum(num)

    def getConnections(self):
        """ return a list of pin connection
            return ("instance_dest":string,
                    "interface_dest":string,
                    "port_dest":string,
                    "pin_dest":string)
        """
        connectionslist = []
        if(self.getNode("connect") is not None):
            for element in self.getNodeList("connect"):
                connectionslist.append(
                        {"instance_dest":
                            str(element.getAttributeValue("instance_dest")),
                         "interface_dest":
                            str(element.getAttributeValue("interface_dest")),
                         "port_dest":
                            str(element.getAttributeValue("port_dest")),
                         "pin_dest":
                            str(element.getAttributeValue("pin_dest"))})
        return connectionslist

    def delAllConnectionsForce(self):
        """ Delete all connections in this pin without any check
        """
        for connection in self.getConnections():
            self.delNode("connect",
                {"instance_dest": connection["instance_dest"],
                 "interface_dest": connection["interface_dest"],
                 "port_dest": connection["port_dest"],
                 "pin_dest": connection["pin_dest"]})

    def delAllConnections(self):
        """ Delete all connection from or to this pin
        """
        for connection in self.getConnections():
            try:
                instance_dest = settings.active_project.getInstance(
                                                  connection["instance_dest"])
                interface_dest =\
                       instance_dest.getInterface(connection["interface_dest"])
                port_dest = interface_dest.getPort(connection["port_dest"])
                pin_des = port_dest.getPin(connection["pin_dest"])
            except Error:
                pass
            self.delConnectionForce(pin_dest)

    def delConnection(self, pin_dest):
        if not self.connectionExists(pin_dest):
            return 1
        return self.delConnectionForce(pin_dest)

    def delConnectionForce(self, pin_dest):
        """ Delete connection from this pin to pin_dest
        """
        try:
            self.delNode("connect",
                {"instance_dest":
                pin_dest.getParent().getParent().getParent().getInstanceName(),
                "interface_dest": pin_dest.getParent().getParent().getName(),
                "port_dest": pin_dest.getParent().getName(),
                "pin_dest": str(pin_dest.getNum())})
        except Exception:
            pass
        try:
            pin_dest.delNode("connect",
                {"instance_dest":
                    self.getParent().getParent().getParent().getInstanceName(),
                 "interface_dest": self.getParent().getParent().getName(),
                 "port_dest": self.getParent().getName(),
                 "pin_dest": str(self.getNum())})
        except Exception:
            pass
        return 1

    def getConnectedPinList(self):
        """ return list of pins connected to this pin
        """
        project = self.getParent().getParent().getParent().getParent()
        pinlist = []
        for connect in self.getConnections():
            pinlist.append(project.getInstance(
                connect["instance_dest"]).getInterface(
                    connect["interface_dest"]).getPort(
                        connect["port_dest"]).getPin(
                            connect["pin_dest"]))
        return pinlist

    def connectionExists(self, pin_dest):
        """ check if this connection exists
        """
        for connect in self.getConnections():
            if connect ==\
            {
          "instance_dest":
            pin_dest.getParent().getParent().getParent().getInstanceName(),
          "interface_dest": pin_dest.getParent().getParent().getName(),
          "port_dest": pin_dest.getParent().getName(),
          "pin_dest": str(pin_dest.getNum())}:
                return True
        return False

    def isEmpty(self):
        if len(self.getConnections()) == 0:
            return True
        else:
            return False

    def setNum(self, num):
        self.setAttribute("num", str(num))

    def getNum(self):
        return self.getAttributeValue("num")

    def isAll(self):  # To Be Remove ?
        if self.getAttributeValue("all") == "true":
            return True
        else:
            return False

    def setAll(self):
        self.setAttribute("all", "true")

    def connectPin(self, pin_dest):
        """ Make connection between two pin
        """
        if self.getParent().forceDefined():
            raise Error("Port " + str(self.getParent().getName()) +
                        " is forced, can't be connected")
        if pin_dest.getParent().forceDefined():
            raise Error("Port " + str(pin_dest.getParent().getName()) +
                        " is forced, can't be connected")

        if self.getParent().getDir() == "in":
            if len(self.getConnections()) != 0:
                try:
                    pin_dest.delConnection(self)
                    self.delConnection(pin_dest)
                except:
                    pass
                raise Error("Can't connect more than one pin on 'in' pin", 0)

        interface_dest = pin_dest.getParent().getParent()
        instance_dest = interface_dest.getParent()

        interface_source = self.getParent().getParent()
        instance_source = interface_source.getParent()

        if not self.connectionExists(pin_dest):
            self.__addConnection(instance_dest.getInstanceName(),
                                 interface_dest.getName(),
                                 pin_dest.getParent().getName(),
                                 pin_dest.getNum())
        if not pin_dest.connectionExists(self):
            pin_dest.__addConnection(instance_source.getInstanceName(),
                                     interface_source.getName(),
                                     self.getParent().getName(),
                                     self.getNum())

    def __addConnection(self, instance_destname, interface_destname,
                              port_destname, pin_destnum=None):
        """ add pin connection and check direction compatibility
        """
        if pin_destnum is not None:
            attributes = {"instance_dest": str(instance_destname),
                          "interface_dest": str(interface_destname),
                          "port_dest": str(port_destname),
                          "pin_dest": str(pin_destnum)}
        else:
            attributes = {"instance_dest": str(instance_destname),
                          "interface_dest": str(interface_destname),
                          "port_dest": str(port_destname)}
        self.addNode(nodename="connect", attributedict=attributes)

    def autoconnectPin(self):
        """ connect all platform connection, if connection is not
            for this platform, delete it.
        """
        project = self.getParent().getParent().getParent().getParent()
        pindest_list = []
        for connection in self.getConnections():
            if connection["instance_dest"] == project.getPlatformName():
                pin_dest = project.getInstance(
                        connection["instance_dest"]).getInterface(
                                connection["interface_dest"]).getPort(
                                        connection["port_dest"]).getPin(
                                                connection["pin_dest"])
                pindest_list.append(pin_dest)
        self.delAllConnectionsForce()

        for pin_dest in pindest_list:
            self.connectPin(pin_dest)

    def isConnected(self):
        """ Return True if pin is connected to something, else return False """
        if len(self.getConnectedPinList()) > 0:
            return True
        else:
            return False

    def isConnectedToInstance(self, instance):
        """ Return True if pin is connected to instance given, else return False
        """
        instance_name = instance.getInstanceName()
        for connexion in self.getConnections():
            if connexion["instance_dest"] == instance_name:
                return True
        return False
