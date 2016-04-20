#! /usr/bin/python3
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
""" Manage port """

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.core.pin import Pin


class Port(WrapperXml):
    """ Manage port
        attributes:
            pinlist -- list of pin
    """

    def __init__(self, parent, **keys):
        """ Init port,
            __init__(self, parent, name)
            __init__(self, parent, wxml)
        """

        self.parent = parent

        if "name" in keys:
            WrapperXml.__init__(self, nodename="port")
            self.set_attr("name", keys["name"])
        elif "node" in keys:
            WrapperXml.__init__(self, node=keys["node"])
        else:
            raise PodError("Keys not known in Port ", 0)

        self.pinlist = []
        for element in self.get_nodes("pin"):
            pin = Pin(self, node=element)
            self.pinlist.append(pin)

    @property
    def extended_name(self):
        """ Get name in this format:
            instancename_portname
        """
        instancename = self.parent.parent.instancename
        return instancename + "_" + self.name

    @property
    def pins(self):
        """ return the pins port list """
        return self.pinlist

    def get_pin(self, num):
        """ return pin node """
        if int(num) >= self.size:
            raise PodError("Pin number " + str(num) + " not in port size")
        for pin in self.pins:
            if pin.num == str(num):
                return pin
        pin = Pin(self, num=str(num))
        self.pinlist.append(pin)
        self.add_node(node=pin)
        return pin

    @property
    def porttype(self):
        """ get type of port """
        return self.get_attr_value("type")

    @porttype.setter
    def porttype(self, the_type):
        """ set type of port """
        self.set_attr("type", the_type)

    @property
    def direction(self):
        """ get port direction """
        return self.get_attr_value("dir")

    @direction.setter
    def direction(self, direction):
        """ set port direction """
        if not direction.lower() in ["out", "in", "inout"]:
            raise PodError("Direction wrong : " + str(direction))
        self.set_attr("dir", direction)

    @property
    def is_hidden(self):
        """ get port direction """
        if self.get_attr_value("hidden") == "true":
            return True
        else:
            return False

    @property
    def unconnected_value(self):
        """ Get unconnected value """
        try:
            ucvalue = self.get_attr_value("unconnected_value")
            if ucvalue is None:
                return "0"
            else:
                return ucvalue
        except PodError:
            return "0"

    @unconnected_value.setter
    def unconnected_value(self, value):
        """ Set unconnected value """
        if self.direction != "in":
            raise PodError("Unconnected Value can be set only on 'in' port")
        if str(value).isdigit():
            if int(value) in [0, 1]:
                self.set_attr("unconnected_value", str(value))
            else:
                raise PodError("Wrong value : " + str(value))
        else:
            raise PodError("Wrong value : " + str(value), 0)

    @property
    def port_option(self):
        """ get port option """
        return self.get_attr_value("port_option")

    @port_option.setter
    def port_option(self, port_option):
        """ set port option """
        self.set_attr("port_option", port_option)

    @property
    def standard(self):
        """ Set standard value """
        return self.get_attr_value("standard")

    @standard.setter
    def standard(self, standard):
        """ Get standard value """
        self.set_attr("standard", standard)

    @property
    def drive(self):
        """ get drive """
        return self.get_attr_value("drive")

    @drive.setter
    def drive(self, drive):
        """ Set drive """
        self.set_attr("drive", drive)

    @property
    def force(self):
        """ Get a force platform io value """
        return self.get_attr_value("force")

    @force.setter
    def force(self, force):
        """ Setting force platform io for this port """
        listofpins = self.pins
        if len(listofpins) > 1:
            raise PodError("Force multiple pin port is not implemented")
        if len(listofpins) == 1:
            raise PodError("This pin is already connected")

        forcevalues = ["gnd", "vcc", "undef"]
        if force in forcevalues:
            self.set_attr("force", force)
        else:
            raise PodError("force value must be in " + str(forcevalues))

    @property
    def position(self):
        """ Get position """
        return self.get_attr_value("position")

    @position.setter
    def position(self, position):
        """ Set position """
        self.set_attr("position", position)

    @property
    def frequency(self):
        """ Get a frequency for this port (if it's clock port) """
        freq = self.get_attr_value("freq")
        if freq is None:
            raise PodError("No frequency attribute for " + self.name)
        return freq

    def force_defined(self):
        """ Return True if a force platform io is defined """
        try:
            force = self.force
        except PodError:
            return False
        forcevalues = ["gnd", "vcc"]
        if force in forcevalues:
            return True
        return False

    def isvariable(self):
        """ Is size of this port is variable ? """
        try:
            if self.get_attr_value("variable_size") == "1":
                return True
            else:
                return False
        except AttributeError:
            return False

    def check_variable_port(self):
        """ check if variable port is correctly connected.
            Connections on variable port must begin at pin 0
            and must be followed.
            ex: 0, 1, 2, 3, …
        """
        if self.isvariable():
            listofpin = self.pins
            if listofpin == []:
                return True
            tab = []
            for pin in listofpin:
                if pin.num is not None:
                    tab.append(int(pin.num))
            tab.sort()
            if (len(tab) - 1) != tab[-1]:
                return False
            return True
        else:
            return True

    @property
    def real_size(self):
        """ if port is variable, return the size set by generic"""
        if self.isvariable():
            return int(self.max_pin_num) + 1
        else:
            return int(self.size)

    @property
    def max_pin_num(self):
        """ return the max num pin value """
        num = "0"
        listofpin = self.pins
        if listofpin == []:
            return str(int(self.size) - 1)
        for pin in listofpin:
            if pin.num is None:
                return str(int(self.size) - 1)
            if int(pin.num) > int(num):
                num = pin.num
        return num

    @property
    def min_pin_num(self):
        """ return the min pin value """
        num = self.size
        listofpin = self.pins
        if listofpin == []:
            return "0"
        for pin in self.pins:
            if pin.num is None:
                return "0"
            if int(pin.num) < int(num):
                num = pin.num
        return num

    def check_connection(self, portdest):
        """ Check the compatibility between the two pin with following rules:
        src dest|  out in  inout lock clock
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

        if checktab[listdir.index(self.direction)][
                listdir.index(portdest.direction)] == 0:
            raise PodError("incompatible pin : " +
                           self.direction + " => " + portdest.direction, 0)

    def connect_port(self, port_dest):
        """ Connect all pins of a port on all pin on same size port dest
        """
        size = self.size
        if size != port_dest.size:
            raise PodError("The two ports have differents size")
        if self.pins != []:
            raise PodError("Port connection " +
                           self.name + " is not void")
        if port_dest.pins != []:
            raise PodError("Port connection " +
                           port_dest.name + " is not void")

        self.connect_all_pins(port_dest)

    def connect_all_pins(self, port_dest):
        """ Connect all port pin to a destination instance
        """
        for pin_num in range(int(self.size)):
            pin_source = self.get_pin(pin_num)
            pin_dest = port_dest.get_pin(pin_num)
            pin_source.connect_pin(pin_dest)

    def autoconnect_pins(self):
        """ If there are platform defaut connection
            in this port, autoconnect it
        """
        for pin in self.pins:
            pin.autoconnect_pin()

    @property
    def dest_port(self):
        """ get destination port connected to this port
            if only one port connected
        """
        port_list = self.dest_ports
        if len(port_list) == 1:
            return port_list[0]
        else:
            return None

    @property
    def dest_ports(self):
        """ Get a list of destination ports
        """
        dest_port_list = []
        for pin in self.pins:
            port_connections =\
                [pin.parent for pin in pin.connected_pins]
            for port_connect in port_connections:
                if port_connect not in dest_port_list:
                    dest_port_list.append(port_connect)

        return dest_port_list

    @property
    def ports_with_same_connection(self):
        """ Return a list of ports that are connected on sames pin.
            only works with port on externals I/O (platform). If only this
            one port is connected to one pin, self port is returned.
        """
        pin_dest_list = self.get_pin(0).connected_pins
        if (len(pin_dest_list) == 0):
            return []
        first_pin = pin_dest_list[0]
        return [pin.parent for pin in first_pin.connected_pins]

    @property
    def connected_msb(self):
        """Return the MSB num that is connected to an another pin
        """
        num = -1
        for pin in self.pins:
            if pin.is_connected():
                if int(pin.num) > num:
                    num = int(pin.num)
        return num

    def isVoid(self):
        """ Return False if at less one pin is connected
            on another pin
        """
        for pin in self.pins:
            if pin.is_connected():
                return False
        return True

    def is_fully_connected(self):
        """ return True if all pin has connection"""
        if len(self.pins) != int(self.size):
            return False
        for pin in self.pins:
            if not pin.is_connected():
                return False
        return True
