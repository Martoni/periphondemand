#! /usr/bin/python3
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
""" Class that manage memory map for bus assignement """

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

    def __str__(self):
        out = "Address  |     instance.interface         |  size  |   ID   |\n"
        out = out + "------------------------------" +\
                    "-------------------------------\n"
        for register in self.mapping:
            out = out + "%8s" % register[0] + " | " +\
                        "%30s" % register[1] + " | " +\
                        "%4s  " % register[2] + " | " +\
                        "%4s   " % register[3] + "|\n"
        out = out + "------------------------------" +\
                    "-------------------------------\n"
        return out

    @property
    def unique_id(self):
        """ Return an unique identificator number for the slave """
        self.instancescount = self.instancescount + 1
        return self.instancescount - 1

    def add_slave_interface(self, interface):
        """ adding slave interface """
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
                base = int(self.lastaddress / size)
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

    def del_slave_interface(self, interface):
        """ delete slave interface from list """
        self.listinterfaceslave.remove(interface)

    @classmethod
    def set_slave_addr(cls, interfaceslave, address):
        """ set base address for interfaceslave,
            address in hexa """
        interfaceslave.base_addr = address

    @property
    def mapping(self):
        """ return a list mapping
            list = [[baseaddress, instancename, size, id],
                    [baseaddress,    "void"   , size, "void" ],
                    [baseaddress, instancename, size, id],
                                 ...               ]
        """
        mappinglist = []
        # sorting slave interface
        self.listinterfaceslave.sort(key=lambda x: x.base_addr)

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
