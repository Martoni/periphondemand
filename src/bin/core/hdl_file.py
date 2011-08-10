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

from   periphondemand.bin.define import *

from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings   import Settings
from periphondemand.bin.utils.error      import Error

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
        if filename.split(".")[-1] not in HDLEXT:
            raise Error("File "+str(filename)+" is not an HDL file")
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
        SCOPE = ["both","fpga","driver"]
        if scope.lower() in SCOPE:
            self.setAttribute("scope",scope)
        else:
            raise Error("Unknown scope "+str(scope))

