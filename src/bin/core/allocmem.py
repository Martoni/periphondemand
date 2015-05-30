#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     AllocMem.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  10/06/2008
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
# Revision list :
#
# Date       By        Changes
#
# ----------------------------------------------------------------------------
""" Class that manage memory map for bus assignement """

__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils.poderror import PodError

DISPLAY = Display()


class AllocMem(object):
    """ Manage memory mapping, and instances identifiers
    """

    def __init__(self, parent):
        self.parent = parent
        self.listinterfaceslave = []
        self.lastaddress = 0
        self.instancescount = 1

    @property
    def unique_id(self):
        """ Return an unique identificator number for the slave """
        self.instancescount = self.instancescount + 1
        return self.instancescount - 1

    def add_interfaceSlave(self, interface):
        if interface.interface_class != "slave":
            raise PodError(interface.name + " is not a slave", 0)

        # add slave interface to list
        self.listinterfaceslave.append(interface)
        # set base address
        size = interface.mem_size
        if size > 0:
            try:
                base = interface.base_addr
            except PodError:
                base = self.lastaddress / size
                if (self.lastaddress % size) != 0:
                    base = base + 1
                interface.base_addr = base * size
                DISPLAY.msg("setting base address " +
                            hex(base * size) + " for  " +
                            interface.parent.instancename +
                            "." + interface.name)
            else:
                DISPLAY.msg("Base address is " + hex(base) + " for " +
                            interface.parent.instancename +
                            "." + interface.name)
            self.lastaddress = size * (base + 1)
        else:
            DISPLAY.msg("No addressing value in this type of bus")

    def delInterfaceSlave(self, interface):
        self.listinterfaceslave.remove(interface)

    def setAddressSlave(self, interfaceslave, address):
        """ set base address for interfaceslave,
            address in hexa """
        interfaceslave.base_addr = address

    def getMapping(self):
        """ return a list mapping
            list = [[baseaddress, instancename, size, id],
                    [baseaddress,    "void"   , size, "void" ],
                    [baseaddress, instancename, size, id],
                                 ...               ]
        """
        mappinglist = []
        # sorting slave interface
        self.listinterfaceslave.sort(
            lambda x,  y: x.base_addr - y.base_addr)

        baseaddress = 0
        for interface in self.listinterfaceslave:
            if baseaddress < interface.base_addr:
                size = interface.base_addr - baseaddress
                mappinglist.append(["0x%02x" % baseaddress,
                                    "--void--",
                                    str(size),
                                    "void"])
                baseaddress = baseaddress + size
            mappinglist.append([hex(interface.base_addr),
                                interface.parent.instancename +
                                "." + interface.name,
                                interface.mem_size,
                                interface.unique_id])
            baseaddress = baseaddress + interface.mem_size
        return mappinglist

    def __str__(self):
        out = "Address  |     instance.interface         |  size  |   ID   |\n"
        out = out + "------------------------------" +\
                    "-------------------------------\n"
        for register in self.getMapping():
            out = out + "%8s" % register[0] + " | " +\
                        "%30s" % register[1] + " | " +\
                        "%4s  " % register[2] + " | " +\
                        "%4s   " % register[3] + "|\n"
        out = out + "------------------------------" +\
                    "-------------------------------\n"
        return out
