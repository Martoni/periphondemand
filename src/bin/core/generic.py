#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Generic.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  21/05/2008
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
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import re
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.error      import Error

DESTINATION = ["fpga","driver","both"]
PUBLIC = ["true","false"]

class Generic(WrapperXml):
    """ Manage generic instance value
    """

    def __init__(self,parent,**keys):
        """ init Generic,
            __init__(self,parent,node)
            __init__(self,parent,nodestring)
            __init__(self,parent,name)
        """
        self.parent=parent
        if "node" in keys:
            self.__initnode(keys["node"])
        elif "nodestring" in keys:
            self.__initnodestring(keys["nodestring"])
        elif "name" in keys:
            self.__initname(keys["name"])
        else:
            raise Error("Keys unknown in Generic init()",0)

    def __initnode(self,node):
        WrapperXml.__init__(self,node=node)
    def __initnodestring(self,nodestring):
        WrapperXml.__init__(self,nodestring=nodestring)
    def __initname(self,name):
        WrapperXml.__init__(self,nodename="generic")
        self.setName(name)

    def getOp(self):
        return self.getAttributeValue("op")
    def setOp(self,op):
        self.setAttribute("op",op)

    def getTarget(self):
        return self.getAttributeValue("target")
    def setTarget(self,target):
        self.setAttribute("target",target)

    def isPublic(self):
        if self.getAttributeValue("public")=="true":
            return "true"
        else:
            return "false"
    def setPublic(self,public):
        public = public.lower()
        if not public in PUBLIC:
            raise Error("Public value "+str(public)+" wrong")
        self.setAttribute("public",public)

    def getType(self):
        the_type = self.getAttributeValue("type")
        if the_type == None:
            raise Error("Generic "+self.getName()+\
                    " description malformed, type must be defined",0)
        else:
            return the_type
    def setType(self,type):
        self.setAttribute("type",type)

    def getMatch(self):
        try:
            return self.getAttributeValue("match").encode("utf-8")
        except AttributeError:
            return None
    def setMatch(self,match):
        self.setAttribute("match",match)

    def getValue(self):
        """ return the generic value
        """
        component = self.getParent()
        if self.getOp() == None:
            return self.getAttributeValue("value")
        else:
            target = self.getTarget().split(".")
            if self.getOp() == "realsizeof":
                # return the number of connected pin
                return str(int(component.getInterface(target[0]).getPort(target[1]).getMaxPinNum())+1)
            else:
                raise Error("Operator unknown "+self.getOp(),1)
    def setValue(self,value):
        if self.getMatch() == None:
            self.setAttribute("value",value)
        elif re.compile(self.getMatch()).match(value):
            self.setAttribute("value",value)
        else:
            raise Error("Value doesn't match for attribute "+str(value),0)

    def getDestination(self):
        """ return the generic destination (fpga,driver or both)
        """
        return self.getAttributeValue("destination")

    def setDestination(self,destination):
        destination = destination.lower()
        if not destination in DESTINATION:
            raise Error("Destination value "+str(destination)+\
                    " unknown")
        self.setAttribute("destination",destination)

