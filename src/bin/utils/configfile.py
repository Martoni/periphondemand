#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     configfile.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  11/02/2009
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
""" Manage ~/.podrc like config file """


import os
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.poderror import PodError


class ConfigFile(WrapperXml):
    """ this class manage configuration file
    """

    def __init__(self, filename):
        self.filename = os.path.expanduser(filename)
        self.configfile = None
        if os.path.exists(self.filename):
            WrapperXml.__init__(self, file=self.filename)
        else:
            print filename + " doesn't exist, be created"
            WrapperXml.__init__(self, nodename="podconfig")
            self.addNode(nodename="libraries")
            self.savefile()
        # fill library path list:
        try:
            self.personal_lib_list = \
                [node.getAttributeValue("path")
                        for node in self.getSubNodeList("libraries", "lib")]
        except:
            self.personal_lib_list = []
        try:
            self.personal_platformlib_list = \
                [node.getAttributeValue("path")
                        for node in self.getSubNodeList("platforms",
                                                        "platform")]
        except:
            self.personal_platformlib_list = []

    def delLibrary(self, path):
        """ Delete library path in config file"""
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
         # check if lib doesn't exists in config file
        libpathlist = [node.getAttributeValue("path") for node in
                self.getSubNodeList(nodename="libraries", subnodename="lib")]
        if not (path in libpathlist):
            raise PodError("Library " + path + " doesn't exist in config", 0)
        self.delSubNode(nodename="libraries",
                        subnodename="lib",
                        attribute="path",
                        value=path)
        self.savefile()

    def addLibrary(self, path):
        """ Adding a library path in config file """
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        # check if lib doesn't exists in config file
        libpathlist = [node.getAttributeValue("path") for node in
                self.getSubNodeList(nodename="libraries", subnodename="lib")]
        if path in libpathlist:
            raise PodError("This library is already in POD", 0)
        # check if directory exist then add it
        if os.path.exists(path):
            self.addSubNode(nodename="libraries",
                            subnodename="lib",
                            attributename="path",
                            value=path)
            self.personal_lib_list.append(path)
            self.savefile()
        else:
            raise PodError("path " + path + " doesn't exist")

    def getLibraries(self):
        """ return a list of library path """
        return self.personal_lib_list

    def getPlatformLibPath(self):
        """ Return a list of platformlib path """
        return self.personal_platformlib_list

    def getSynthesisToolCommand(self, synthesisName):
        """ Return the path to synthesis command """
        from periphondemand.bin.utils import wrappersystem as sy
        for i in self.getNode("tools").getNodeList("tool"):
            if (i.getAttributeValue(key="name") == synthesisName):
                command_name = i.getAttributeValue(key="command")
                command_path = i.getAttributeValue(key="default_path")
                command_name = command_path + "/" + command_name
                break
        if not sy.commandExist(command_name):
            raise PodError("Synthesis tool tcl shell command named " +
                        command_name +
                        " doesn't exist in .podrc")
        return command_name

    def savefile(self):
        """ Write configuration file """
        self.configfile = open(self.filename, "w")
        self.configfile.write(str(self))
        self.configfile.close()

