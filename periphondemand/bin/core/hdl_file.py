#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Hdl_file.py
# Purpose:  
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/05/2008
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

import os

from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings   import Settings
from periphondemand.bin.utils.error      import Error

from periphondemand.bin.code.entityparser          import EntityParser

from periphondemand.bin.core.port    import Port
from periphondemand.bin.core.generic import Generic

settings = Settings()

class Hdl_file(WrapperXml):
    """ Manage source files
    """

    def __init__(self,parent,**keys):
        """ Init Hdl_file,
            __init__(self,parent,node)
            __init__(self,filename,istop,scope)
        """
        self.parent = parent
        self.parser = None
        if "node" in keys:
            WrapperXml.__init__(self,node=keys["node"])
        elif "filename" in keys:
            self.__initfilename(filename=keys["filename"],
                                istop=keys["istop"],scope=keys["scope"])
        else:
            raise Error("Keys unknown in Hdl_file",0)

    def __initfilename(self,filename,istop,scope):
        WrapperXml.__init__(self,nodename="hdl_file")
        if istop == 1:
            self.setTop()
        self.setScope(scope)
        self.setFileName(filename)

    def getFileName(self):
        return self.getAttribute("filename")

    def setFileName(self,filename):
        self.setAttribute("filename",filename)

    def getFilePath(self):
        """ return an open file pointer of HDL file """
        librarypath = settings.active_library.getLibraryPath()
        componentname = self.getParent().getName()
        filepath = os.path.join(librarypath, componentname,
                                "hdl", self.getFileName())
        return filepath

    def isTop(self):
        if self.getAttribute("istop") == "1":
            return 1
        else:
            return 0
    def setTop(self):
        self.setAttribute("istop","1")
    def unsetTop(self):
        self.setAttribute("istop","0")

    def getScope(self):
        return self.getAttribute("scope")
    def setScope(self,scope):
        self.setAttribute("scope",scope)

    def getGeneric(self,genericname):
        """ Get generic declared in HDL file"""
        for generic in self.getGenericsList():
            if generic.getName() == genericname:
                return generic
        raise Error("No generic named "+str(genericname))

    def getGenericsList(self):
        """ Parse HDL file and return a list of generic """
        if not self.isTop():
            raise Error("Only top HDL file can be parsed")
        if self.parser == None:
            Et = EntityParser()
            self.parser = Et.factory(self.getFilePath())
        parsed_generic_list = self.parser.parseGeneric()
        generic_list = []
        for parsed_generic in parsed_generic_list:
            generic = Generic(self,name=parsed_generic["name"])
            generic.setType(parsed_generic["type"])
            generic.setValue(parsed_generic["defautvalue"])
            generic.setDescription(parsed_generic["description"])
            generic_list.append(generic)
        return generic_list
    
    def getEntityName(self):
        if self.parser == None:
            Et = EntityParser()
            self.parser = Et.factory(self.getFilePath())
        return self.parser.getEntityName()

    def getPort(self,portname):
        """ get port declared in HDL file """
        portlist = self.getPortsList()
        for port in portlist:
            if port.getName() == portname:
                return port
        raise Error("No port named "+portname+\
                " in file "+self.getFileName())

    def getPortsList(self):
        """ Parse HDL file and return a list of ports"""
        if not self.isTop():
            raise Error("Only top HDL file can be parsed")
        if self.parser == None:
            Et = EntityParser()
            self.parser = Et.factory(self.getFilePath())
        parsedportlist = self.parser.parsePort()
        portlist = []
        for parsedport in parsedportlist:
            port = Port(self,name=parsedport["name"])
            port.setDir(parsedport["direction"])
            port.setSize(str(parsedport["size"]))
            port.setDescription(parsedport["description"])
            portlist.append(port)
        return portlist
         

