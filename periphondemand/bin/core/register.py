#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Register.py
# Purpose:  
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/04/2008
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

__doc__ = ""
__version__ = "1.0.0"
__versionTime__ = "30/04/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

from periphondemand.bin.utils.wrapperxml import WrapperXml 
from periphondemand.bin.utils.error      import Error

class Register(WrapperXml):
    """ Manage Register
        attributes:
    """

    def __init__(self,parent,**keys):
        """ Init register,
            __init__(self,parent,node)
            __init__(self,parent,nodestring)
            __init__(self,parent,register_name)
        """
        if "node" in keys:
            WrapperXml.__init__(self,node=keys["node"])
        elif "nodestring" in keys:
            WrapperXml.__init__(self,nodestring=keys["nodestring"])
        elif "register_name" in keys:
            WrapperXml.__init__(self,nodename="register")
            self.setName(keys["register_name"])
        else:
            raise Error("Keys not known in Register",0)

        self.parent = parent

    def getOffset(self):
        return self.getAttribute("offset")
    def setOffset(self,offset):
        #TODO: check if offset is valid
        self.setAttribute("offset",offset)
    def getRows(self):
        return self.getAttribute("rows")
    def setRows(self,rows):
        self.setAttribute("rows",rows)

    def getAbsoluteAddr(self):
        """ return absolute address
        """
        baseaddr = int(self.getParent().getBase(),16)
        offset = int(self.getOffset(),16)
        if int(self.getSize()) == 8:
            return "%02x"%(baseaddr+offset)
        elif int(self.getSize()) == 16:
            return "%04x"%(baseaddr+offset*2)
        elif int(self.getSize()) == 32:
            return "%08x"%(baseaddr+offset*4)
        else:
            return "%x"%absaddr

