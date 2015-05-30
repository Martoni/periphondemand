#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     library.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  28/04/2009
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
""" Manage library """

import os
from periphondemand.bin.define import LIBRARYPATH

from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils import wrappersystem as sy

SETTINGS = Settings()


class Library(object):
    """ Libraries management class
    """

    def __init__(self):
        self.libname = None
        pass

    def listLibraries(self):
        """ Return a list of libraries availables
        """
        componentlist = sy.listDirectory(SETTINGS.path + LIBRARYPATH)
        componentlist.extend(self.getPersonalLibName())
        componentlist.extend(self.getComponentsLibName())
        return componentlist

    def getOfficialLibraries(self):
        """ Get list of official libraries"""
        return sy.listDirectory(SETTINGS.path + LIBRARYPATH)

    def getLibraryPath(self, libraryname=None):
        """ Get the library path """
        if libraryname is None:
            libraryname = self.getLibName()
        official_component_type = self.getOfficialLibraries()
        if libraryname in official_component_type:
            return SETTINGS.path + LIBRARYPATH + "/" + libraryname
        elif libraryname in self.getPersonalLibName():
            return SETTINGS.active_library.getPersonalLibPath(libraryname)
        elif libraryname in self.getComponentsLibName():
            return SETTINGS.active_library.getComponentsLibPath(libraryname)
        else:
            raise PodError("Library not found : " + str(libraryname), 0)

    def listComponents(self, libraryname=None):
        """ Return a list with all library components
        """
        if libraryname is None:
            libraryname = self.getLibName()
        official_component_type = self.getOfficialLibraries()
        componentlist = []
        if libraryname in official_component_type:
            componentlist =\
                sy.listDirectory(SETTINGS.path +
                                 LIBRARYPATH + "/" +
                                 libraryname)
        elif libraryname in self.getPersonalLibName():
            componentlist =\
                sy.listDirectory(self.getPersonalLibPath(libraryname))
        elif libraryname in self.getComponentsLibName():
            componentlist =\
                sy.listDirectory(self.getComponentsLibPath(libraryname))
        return componentlist

    def addLibrary(self, path):
        self.checkLib(path)
        SETTINGS.configfile.addLibrary(path)
        SETTINGS.personal_lib_path_list.append(path)
        SETTINGS.personal_lib_name_list.append(path.split("/")[-1])

    def delLibrary(self, libraryname):
        """ delete library path from config file
        """
        if libraryname in self.getOfficialLibraries():
            raise PodError("Can't delete an official library")
        libpath = self.getPersonalLibPath(libraryname)
        SETTINGS.configfile.delLibrary(libpath)

    def checkLib(self, path):
        """ check if lib and component are not duplicated """
        libname = path.split("/")[-1]
        # check if lib name exist
        if libname in self.listLibraries():
            raise PodError("Library " + libname + " already exist", 0)
        # check if components under library are new
        componentlist = sy.listDirectory(path)
        for component in componentlist:
            for libraryname in self.listLibraries():
                if component in self.listComponents(libraryname):
                    raise PodError("Library " + libname +
                                   " contain a component that exist in '" +
                                   libraryname + "' : " + component, 0)

    def getComponentsLibPath(self, name=None):
        """ Get the path of library"""
        path_list = []
        try:
            for node in\
                    SETTINGS.active_project.getSubNodeList("componentslibs",
                                                           "componentslib"):
                path_list.append(node.getAttributeValue(key="path"))
            if name is None:
                return path_list
            else:
                for libpath in path_list:
                    if libpath.split("/")[-1] == name:
                        return libpath
                return []
        except AttributeError:
            return []

    def getComponentsLibName(self):
        """ Get the name of library"""
        name_list = []
        for path in self.getComponentsLibPath():
            name_list.append(path.split("/")[-1])
        return name_list

    def getPersonalLibName(self):
        """ Get the list names of Personnal library"""
        return SETTINGS.personal_lib_name_list

    def getPersonalLibPath(self, name):
        """ Get the path library"""
        for libpath in SETTINGS.personal_lib_path_list:
            if libpath.split("/")[-1] == name:
                return libpath
        return ""

    def load(self, libname):
        """ Load a library with name given in parameter"""
        if libname not in self.listLibraries():
            raise PodError("No " + libname + " in pod libraries")
        self.libname = libname

    def getLibName(self):
        """ Get the library name """
        return self.libname
