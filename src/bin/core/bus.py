#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Bus.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/04/2008
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
""" Manage busses """

from periphondemand.bin.define import BUSPATH

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.error import Error

SETTINGS = Settings()


class Bus(WrapperXml):
    """ Class for bus type
        attributes:
            settings --
    """

    def __init__(self, parent, name):
        self.parent = parent
        WrapperXml.__init__(self, file=(SETTINGS.path + BUSPATH + "/" +
                                  name + "/" + name + ".xml"))

    def getDataSize(self):
        """ Get size of data"""
        size = self.getAttributeValue("datasize")
        if size is None:
            raise Error("No datasize attribute in bus " + self.getName(), 0)
        else:
            return size

    def getSignalName(self, classname, typename):
        """ return the signal name for a given type
        """
        for classnode in self.getNodeList("class"):
            if classnode.getAttributeValue("type") == classname:
                for signal in classnode.getNodeList("type"):
                    if signal.getAttributeValue("type") == typename:
                        return signal.getAttributeValue("name")
        return None

    def generate_intercon(self, intercon):
        """ generate intercon
        """
        masterinterface = self.getParent()
        import sys
        # load module path
        sys.path.append(SETTINGS.path + BUSPATH + "/" + self.getName())
        plugin = __import__(self.getName())
        sys.path.remove(SETTINGS.path + BUSPATH + "/" + self.getName())

        plugin.generate_intercon(masterinterface, intercon)
