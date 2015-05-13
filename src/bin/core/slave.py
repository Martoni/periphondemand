#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Slave.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  06/06/2008
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
""" Managing slave interfaces """

__doc__ = ""
__version__ = "1.0.0"
__versionTime__ = "06/06/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.error import PodError


class Slave(WrapperXml):
    """ Manage Slaves connection
    """

    def __init__(self, parent, **keys):
        """ init Slave,
            __init__(self,parent,node)
            __init__(self,parent,instancename,interfacename)
        """
        self.parent = parent
        if "node" in keys:
            WrapperXml.__init__(self, node=keys["node"])
        elif "instancename" in keys:
            WrapperXml.__init__(self, nodename="slave")
            self.setInstanceName(keys["instancename"])
            self.setInterfaceName(keys["interfacename"])
        else:
            raise PodError("Keys unknowns in Slave init()", 0)

    def getInstanceName(self):
        return self.getAttributeValue("instancename")

    def setInstanceName(self, instancename):
        self.setAttribute("instancename", instancename)

    def getInterfaceName(self):
        return self.getAttributeValue("interfacename")

    def setInterfaceName(self, interfacename):
        self.setAttribute("interfacename", interfacename)

    def get_instance(self):
        return self.parent.parent.parent.get_instance(
                self.getInstanceName())

    def getInterface(self):
        return self.get_instance().getInterface(self.getInterfaceName())
