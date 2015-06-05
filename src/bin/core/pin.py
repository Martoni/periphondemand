#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Pin.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  05/05/2008
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
""" Class that manage pins """

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError

SETTINGS = Settings()


class Pin(WrapperXml):
    """ Manage Pin
        attributes:

    """

    def __init__(self, parent, **keys):
        """ init Pin,
            __init__(self,parent,node)
            __init__(self,parent,num)
        """

        self.parent = parent

        if "node" in keys:
            WrapperXml.__init__(self, node=keys["node"])
        elif "num" in keys:
            WrapperXml.__init__(self, nodename="pin")
            self.num = keys["num"]
        else:
            raise PodError("Keys unknown in Pin", 0)

    @property
    def connections(self):
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

    def del_connections_forces(self):
        """ Delete all connections in this pin without any check
        """
        for connection in self.connections:
            self.delNode(
                "connect",
                {"instance_dest": connection["instance_dest"],
                 "interface_dest": connection["interface_dest"],
                 "port_dest": connection["port_dest"],
                 "pin_dest": connection["pin_dest"]})

    def delAllConnections(self):
        """ Delete all connection from or to this pin
        """
        for connection in self.connections:
            try:
                instance_dest = SETTINGS.active_project.get_instance(
                    connection["instance_dest"])
                interface_dest =\
                    instance_dest.get_interface(connection["interface_dest"])
                port_dest = interface_dest.get_port(connection["port_dest"])
                pin_dest = port_dest.get_pin(connection["pin_dest"])
            except PodError:
                pass
            self.delConnectionForce(pin_dest)

    def delConnection(self, pin_dest):
        if not self.connectionExists(pin_dest):
            return False
        return self.delConnectionForce(pin_dest)

    def delConnectionForce(self, pin_dest):
        """ Delete connection from this pin to pin_dest
        """
        self.delNode(
            "connect",
            {"instance_dest":
             pin_dest.parent.parent.parent.instancename,
             "interface_dest": pin_dest.parent.parent.name,
             "port_dest": pin_dest.parent.name,
             "pin_dest": str(pin_dest.num)})

        pin_dest.delNode(
            "connect",
            {"instance_dest":
                self.parent.parent.parent.instancename,
             "interface_dest": self.parent.parent.name,
             "port_dest": self.parent.name,
             "pin_dest": str(self.num)})
        return True

    def getConnectedPinList(self):
        """ return list of pins connected to this pin
        """
        project = self.parent.parent.parent.parent
        pinlist = []
        for connect in self.connections:
            pinlist.append(project.get_instance(
                connect["instance_dest"]).get_interface(
                    connect["interface_dest"]).get_port(
                        connect["port_dest"]).get_pin(
                            connect["pin_dest"]))
        return pinlist

    def connectionExists(self, pin_dest):
        """ check if this connection exists
        """
        for connect in self.connections:
            if connect == {"instance_dest":
                           pin_dest.parent.parent.parent.instancename,
                           "interface_dest": pin_dest.parent.parent.name,
                           "port_dest": pin_dest.parent.name,
                           "pin_dest": str(pin_dest.num)}:
                return True
        return False

    def isEmpty(self):
        if len(self.connections) == 0:
            return True
        else:
            return False

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
        message = "trying to connect " +\
                  self.parent.parent.parent.name + "." +\
                  self.parent.parent.name + "." +\
                  self.parent.name + "." +\
                  self.num + " -> " +\
                  pin_dest.parent.parent.parent.name + "." +\
                  pin_dest.parent.parent.name + "." +\
                  pin_dest.parent.name + "." +\
                  pin_dest.num

        if self.parent.force_defined():
            raise PodError(message + " : Port " + str(self.parent.name) +
                           " is forced, can't be connected")
        if pin_dest.parent.force_defined():
            raise PodError(message +
                           " : Port " + str(pin_dest.parent.name) +
                           " is forced, can't be connected")

        if self.parent.direction == "in":
            if len(self.connections) != 0:
                try:
                    pin_dest.delConnection(self)
                    self.delConnection(pin_dest)
                except:
                    pass
            if len(self.connections) != 0:
                raise PodError(message + " : Can't connect more than " +
                               "one pin on 'in' pin")

        interface_dest = pin_dest.parent.parent
        instance_dest = interface_dest.parent

        interface_source = self.parent.parent
        instance_source = interface_source.parent

        if not self.connectionExists(pin_dest):
            self.__addConnection(instance_dest.instancename,
                                 interface_dest.name,
                                 pin_dest.parent.name,
                                 pin_dest.num)
        if not pin_dest.connectionExists(self):
            pin_dest.__addConnection(instance_source.instancename,
                                     interface_source.name,
                                     self.parent.name,
                                     self.num)

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

    def autoconnect_pin(self):
        """ connect all platform connection, if connection is not
            for this platform, delete it.
        """
        project = SETTINGS.active_project
        pindest_list = []
        if project.platform_name is not None:
            for connection in self.connections:
                if connection["instance_dest"] == project.platform_name:
                    pin_dest = project.get_instance(
                        connection["instance_dest"]).get_interface(
                            connection["interface_dest"]).get_port(
                                connection["port_dest"]).get_pin(
                                    connection["pin_dest"])
                    pindest_list.append(pin_dest)
        self.del_connections_forces()
        for pin_dest in pindest_list:
            self.connectPin(pin_dest)

    def isConnected(self):
        """ Return True if pin is connected to something, else return False """
        if len(self.getConnectedPinList()) > 0:
            return True
        else:
            return False

    def isConnectedToInstance(self, instance):
        """ Return True if pin is connected to instance given,
        else return False
        """
        instance_name = instance.instancename
        for connexion in self.connections:
            if connexion["instance_dest"] == instance_name:
                return True
        return False
