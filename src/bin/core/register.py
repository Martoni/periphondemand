#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Register.py
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
# Revision list :
#
# Date       By        Changes
#
# ----------------------------------------------------------------------------
""" Manage registers """

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.poderror import PodError


class Register(WrapperXml):
    """ Manage Register
        attributes:
    """

    def __init__(self, parent, **keys):
        """ Init register,
            __init__(self,parent,node)
            __init__(self,parent,nodestring)
            __init__(self,parent,register_name)
        """
        if "node" in keys:
            WrapperXml.__init__(self, node=keys["node"])
        elif "nodestring" in keys:
            WrapperXml.__init__(self, nodestring=keys["nodestring"])
        elif "register_name" in keys:
            WrapperXml.__init__(self, nodename="register")
            self.name = keys["register_name"]
        else:
            raise PodError("Keys not known in Register", 0)

        self.parent = parent

    @property
    def offset(self):
        """ Get the offset value """
        return self.get_attr_value("offset")

    @offset.setter
    def offset(self, offset):
        """ Set the offset value """
        self.set_attr("offset", offset)

    @property
    def absolute_addr(self):
        """ return absolute address """
        baseaddr = self.parent.base_addr
        offset = int(self.offset, 16)
        if int(self.size) == 8:
            return "%02x" % (baseaddr + offset)
        elif int(self.size) == 16:
            return "%04x" % (baseaddr + offset * 2)
        elif int(self.size) == 32:
            return "%08x" % (baseaddr + offset * 4)
        else:
            raise PodError("Register size not supported for reg " +
                           str(self.name) +
                           " in component " +
                           str(self.parent.parent.name))
