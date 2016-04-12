#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Intercon.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  13/05/2008
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
""" Manage intercon """

from periphondemand.bin.utils.display import Display

from periphondemand.bin.core.component import Component
from periphondemand.bin.core.port import Port
from periphondemand.bin.core.interface import Interface

DISPLAY = Display()


class Intercon(Component):
    """ Generate Intercon component """

    def __init__(self, parent, masterinterface):
        """ Init fonction
        """
        masterinstancename = masterinterface.parent.instancename
        masterinterfacename = masterinterface.name

        Component.__init__(self, parent)
        self.interfaceslist = []
        self.add_node(nodename="component")

        masterinstance = self.parent.get_instance(masterinstancename)
        masterinterface = masterinstance.get_interface(masterinterfacename)

        # Write xml description
        self.generate_xml(masterinterface)
        # Write Code for component

        masterinterface.bus.generate_intercon(self)

        DISPLAY.msg("Intercon with name : " + self.instancename + " Done")

    def generate_xml(self, masterinterface):
        """ Generate intercon code
        """
        masterinstance = masterinterface.parent

        # set name and description
        self.name = str(masterinstance.instancename) +\
            "_" + str(masterinterface.name)
        self.instancename = masterinstance.instancename +\
            "_" + masterinterface.name +\
            "_intercon"
        self.description = "Connect slaves to " + masterinterface.name +\
            " from " + masterinstance.instancename

        # Save to make directories
        self.save()

        # Create interface for each component connected on intercon
        # for slaves and master:
        slaveslist = masterinterface.slaves
        interfaceslist = [slave.get_interface() for slave in slaveslist]
        interfaceslist.append(masterinterface)

        # For each slave and master interface, create interface in intercon
        for interface in interfaceslist:
            instance = interface.parent

            # bus (wishbone,...)
            bus = Interface(self,
                            name=instance.instancename +
                            "_" + interface.name)
            bus.interface_class = "intercon"
            # Adding bus interface on intercon
            self.add_interface(bus)

            # Creating port with invert direction value
            for port in interface.ports:
                newport = Port(bus,
                               name=instance.instancename +
                               "_" + port.name)
                newport.direction = self.inv_direction(port.direction)
                newport.size = port.size
                # adding port on bus interface
                bus.add_port(newport)
                # connect port new port on instance interface
                port.connect_all_pins(newport)

        bus.interface_class = "intercon"
        self.num = "0"
