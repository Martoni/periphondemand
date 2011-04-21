#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     configfile.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  11/02/2009
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
__versionTime__ = "11/02/2009"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import os
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.error import Error

class ConfigFile(WrapperXml):
    """ this class manage configuration file
    """

    def __init__(self,filename):
        self.filename = os.path.expanduser(filename)
        if os.path.exists(self.filename):
            WrapperXml.__init__(self,file=self.filename)
        else:
            print filename + " doesn't exist, be created"
            WrapperXml.__init__(self,nodename="podconfig")
            self.addNode(nodename="libraries")
            self.savefile()
        # fill library path list:
        try:
            self.personal_lib_list =\
                [node.getAttribute("path")
                        for node in self.getSubNodeList("libraries","lib")]
        except:
            self.personal_lib_list = []
        try:
            self.personal_platformlib_list =\
                [node.getAttribute("path")
                        for node in self.getSubNodeList("platforms","platform")]
        except:
            self.personal_platformlib_list = []

    def delLibrary(self,path):
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
         # check if lib doesn't exists in config file
        libpathlist = [node.getAttribute("path") for node in
                self.getSubNodeList(nodename="libraries", subnodename="lib")]
        if not (path in libpathlist):
            raise Error("Library "+path+" doesn't exist in config",0)
        self.delSubNode(nodename="libraries",
                        subnodename="lib",
                        attribute="path",
                        value=path)
        self.savefile()

    def addLibrary(self,path):
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        # check if lib doesn't exists in config file
        libpathlist = [node.getAttribute("path") for node in
                self.getSubNodeList(nodename="libraries", subnodename="lib")]
        if path in libpathlist:
            raise Error("This library is already in POD",0)
        # check if directory exist then add it
        if os.path.exists(path):
            self.addSubNode(nodename="libraries",
                            subnodename="lib",
                            attributename="path",
                            value=path)
            self.personal_lib_list.append(path)
            self.savefile()
        else:
            raise Error("path "+path+" doesn't exist")

    def getLibraries(self):
        """ return a list of library path """
        return self.personal_lib_list
    def getPlatformLibPath(self):
        return self.personal_platformlib_list

    def savefile(self):
        self.file = open(self.filename,"w")
        self.file.write(str(self))
        self.file.close()

