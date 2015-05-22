#! /usr/bin/python
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

from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.display import Display

from periphondemand.bin.core.component import Component
from periphondemand.bin.core.port import Port
from periphondemand.bin.core.interface import Interface
from periphondemand.bin.core.hdl_file import Hdl_file

DISPLAY = Display()


class Intercon(Component):
    """ Generate Intercon component """

    def __init__(self, masterinterface):
        """ Init fonction
        """
        masterinstancename = masterinterface.parent.getInstanceName()
        masterinterfacename = masterinterface.getName()

        Component.__init__(self)
        self.interfaceslist = []
        self.addNode(nodename="component")

        masterinstance = self.parent.get_instance(masterinstancename)
        masterinterface = masterinstance.getInterface(masterinterfacename)

        # Write xml description
        self.generateXML(masterinterface)
        # Write Code for component

        masterinterface.getBus().generate_intercon(self)

        DISPLAY.msg("Intercon with name : " + self.getInstanceName() + " Done")

    def generateXML(self, masterinterface):
        """ Generate intercon code
        """
        masterinstance = masterinterface.parent

        # set name and description
        self.setName(str(masterinstance.getInstanceName()) +
                     "_" + str(masterinterface.getName()))
        self.setInstanceName(str(masterinstance.getInstanceName()) +
                             "_" + str(masterinterface.getName()) +
                             "_intercon")
        self.setDescription("Connect slaves to " +
                            masterinterface.getName() +
                            " from " +
                            masterinstance.getInstanceName())

        # Save to make directories
        self.saveInstance()

        # Create interface for each component connected on intercon
        # for slaves and master:
        slaveslist = masterinterface.getSlavesList()
        interfaceslist = [slave.getInterface() for slave in slaveslist]
        interfaceslist.append(masterinterface)

        # For each slave and master interface, create interface in intercon
        for interface in interfaceslist:
            instance = interface.parent

            # bus (wishbone,...)
            bus = Interface(self,
                            name=instance.getInstanceName() +
                            "_" + interface.getName())
            bus.setClass("intercon")
            # Adding bus interface on intercon
            self.addInterface(bus)

            # Creating port with invert direction value
            for port in interface.ports:
                newport = Port(bus,
                               name=instance.getInstanceName() +
                               "_" + port.getName())
                newport.direction = self.invertDir(port.direction)
                newport.size = port.size
                # adding port on bus interface
                bus.addPort(newport)
                # connect port new port on instance interface
                port.connect_all_pins(newport)

        bus.setClass("intercon")
        self.setNum("0")
