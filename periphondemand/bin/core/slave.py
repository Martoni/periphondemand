#! /usr/bin/python3
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

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.settings import Settings

SETTINGS = Settings()


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
            self.instancename = keys["instancename"]
            self.interfacename = keys["interfacename"]
        else:
            raise PodError("Keys unknowns in Slave init()", 0)

    @property
    def instancename(self):
        """ Get instance name """
        return self.get_attr_value("instancename")

    @instancename.setter
    def instancename(self, instancename):
        """ Set instance name """
        self.set_attr("instancename", instancename)

    @property
    def interfacename(self):
        """ get interface name """
        return self.get_attr_value("interfacename")

    @interfacename.setter
    def interfacename(self, interfacename):
        """ set interface name """
        self.set_attr("interfacename", interfacename)

    def get_interface(self):
        """ get the parent interface of this slave interface """
        return self.get_instance().get_interface(self.interfacename)
