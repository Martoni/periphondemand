#! /usr/bin/python3
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
    def project(self):
        """ Return the project object linked to this pin """
        return self.parent.parent.parent.parent

    @property
    def connections(self):
        """ return a list of pin connection
            return ("instance_dest":string,
                    "interface_dest":string,
                    "port_dest":string,
                    "pin_dest":string)
        """
        connectionslist = []
        if(self.get_node("connect") is not None):
            for element in self.get_nodes("connect"):
                connectionslist.append(
                    {"instance_dest":
                        str(element.get_attr_value("instance_dest")),
                     "interface_dest":
                        str(element.get_attr_value("interface_dest")),
                     "port_dest":
                        str(element.get_attr_value("port_dest")),
                     "pin_dest":
                        str(element.get_attr_value("pin_dest"))})
        return connectionslist

    def del_connections_forces(self):
        """ Delete all connections in this pin without any check """
        for connection in self.connections:
            self.del_node(
                "connect",
                {"instance_dest": connection["instance_dest"],
                 "interface_dest": connection["interface_dest"],
                 "port_dest": connection["port_dest"],
                 "pin_dest": connection["pin_dest"]})

    def del_connections(self):
        """ Delete all connection from or to this pin """
        for connection in self.connections:
            try:
                instance_dest = self.parent.get_instance(
                    connection["instance_dest"])
                interface_dest =\
                    instance_dest.get_interface(connection["interface_dest"])
                port_dest = interface_dest.get_port(connection["port_dest"])
                pin_dest = port_dest.get_pin(connection["pin_dest"])
            except PodError:
                pass
            self.del_connection_force(pin_dest)

    def del_connection(self, pin_dest):
        """ delete connection to pin_dest """
        if not self.is_connection_exists(pin_dest):
            return False
        return self.del_connection_force(pin_dest)

    def del_connection_force(self, pin_dest):
        """ Delete connection from this pin to pin_dest """
        self.del_node(
            "connect",
            {"instance_dest":
             pin_dest.parent.parent.parent.instancename,
             "interface_dest": pin_dest.parent.parent.name,
             "port_dest": pin_dest.parent.name,
             "pin_dest": str(pin_dest.num)})

        pin_dest.del_node(
            "connect",
            {"instance_dest":
                self.parent.parent.parent.instancename,
             "interface_dest": self.parent.parent.name,
             "port_dest": self.parent.name,
             "pin_dest": str(self.num)})
        return True

    @property
    def connected_pins(self):
        """ return list of pins connected to this pin """
        pinlist = []
        for connect in self.connections:
            pinlist.append(self.project.get_instance(
                connect["instance_dest"]).get_interface(
                    connect["interface_dest"]).get_port(
                        connect["port_dest"]).get_pin(
                            connect["pin_dest"]))
        return pinlist

    def is_connection_exists(self, pin_dest):
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

    def connect_pin(self, pin_dest):
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
                    pin_dest.del_connection(self)
                    self.del_connection(pin_dest)
                except PodError:
                    pass
            if len(self.connections) != 0:
                raise PodError(message + " : Can't connect more than " +
                               "one pin on 'in' pin")

        interface_dest = pin_dest.parent.parent
        instance_dest = interface_dest.parent

        interface_source = self.parent.parent
        instance_source = interface_source.parent

        if not self.is_connection_exists(pin_dest):
            self.add_connection_raw(instance_dest.instancename,
                                    interface_dest.name,
                                    pin_dest.parent.name,
                                    pin_dest.num)
        if not pin_dest.is_connection_exists(self):
            pin_dest.add_connection_raw(instance_source.instancename,
                                        interface_source.name,
                                        self.parent.name,
                                        self.num)

    def add_connection_raw(self, instance_destname, interface_destname,
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
        self.add_node(nodename="connect", attributedict=attributes)

    def autoconnect_pin(self):
        """ connect all platform connection, if connection is not
            for this platform, delete it.
        """
        pindest_list = []
        for connection in self.connections:
            if connection["instance_dest"] == self.project.platform_name:
                instance_dest = self.parent.get_instance(
                    connection["instance_dest"])

                if instance_dest.is_platform() is True:
                    pin_dest = instance_dest.get_interface(
                        connection["interface_dest"]).get_port(
                            connection["port_dest"]).get_pin(
                                connection["pin_dest"])
                    pindest_list.append(pin_dest)
        self.del_connections_forces()
        for pin_dest in pindest_list:
            self.connect_pin(pin_dest)

    def is_connected(self):
        """ Return True if pin is connected to something, else return False """
        if len(self.connected_pins) > 0:
            return True
        else:
            return False

    def is_connected_to_inst(self, instance):
        """ Return True if pin is connected to instance given,
        else return False
        """
        instance_name = instance.instancename
        for connexion in self.connections:
            if connexion["instance_dest"] == instance_name:
                return True
        return False
