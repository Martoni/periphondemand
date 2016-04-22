#! /usr/bin/python3
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

from periphondemand.bin.define import LIBRARYPATH

from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils import wrappersystem as sy

SETTINGS = Settings()


class Library(object):
    """ Libraries management class
    """

    def __init__(self, project):
        self._libname = None
        self._project = project

    @property
    def libraries(self):
        """ Return a list of libraries availables """
        componentlist = sy.list_dir(SETTINGS.path + LIBRARYPATH)
        componentlist.extend(self.personnal_libraries())
        componentlist.extend(self.get_component_lib_name())
        return componentlist

    @classmethod
    def official_libraries(cls):
        """ Get list of official libraries"""
        return sy.list_dir(SETTINGS.path + LIBRARYPATH)

    def library_path(self, libraryname=None):
        """ Get the library path """
        if libraryname is None:
            libraryname = self.lib_name
        official_component_type = self.official_libraries()
        if libraryname in official_component_type:
            return SETTINGS.path + LIBRARYPATH + "/" + libraryname
        elif libraryname in self.personnal_libraries():
            return self.get_pers_lib_path(libraryname)
        elif libraryname in self.get_component_lib_name():
            return self.get_component_lib_path(libraryname)
        else:
            raise PodError("Library not found : " + str(libraryname), 0)

    def list_components(self, libraryname=None):
        """ Return a list with all library components
        """
        if libraryname is None:
            libraryname = self.lib_name
        official_component_type = self.official_libraries()
        componentlist = []
        if libraryname in official_component_type:
            componentlist =\
                sy.list_dir(SETTINGS.path +
                            LIBRARYPATH + "/" +
                            libraryname)
        elif libraryname in self.personnal_libraries():
            componentlist =\
                sy.list_dir(self.get_pers_lib_path(libraryname))
        elif libraryname in self.get_component_lib_name():
            componentlist =\
                sy.list_dir(self.get_component_lib_path(libraryname))
        return componentlist

    def add_library(self, path):
        """ Adding library path """
        self.check_lib(path)
        SETTINGS.configfile.add_library(path)
        SETTINGS.personal_lib_path_list.append(path)
        SETTINGS.personal_lib_name_list.append(path.split("/")[-1])

    def del_library(self, libraryname):
        """ delete library path from config file
        """
        if libraryname in self.official_libraries():
            raise PodError("Can't delete an official library")
        libpath = self.get_pers_lib_path(libraryname)
        SETTINGS.configfile.del_library(libpath)

    def check_lib(self, path):
        """ check if lib and component are not duplicated """
        libname = path.split("/")[-1]
        # check if lib name exist
        if libname in self.libraries:
            raise PodError("Library " + libname + " already exist", 0)
        # check if components under library are new
        componentlist = sy.list_dir(path)
        for component in componentlist:
            for libraryname in self.libraries:
                if component in self.list_components(libraryname):
                    raise PodError("Library " + libname +
                                   " contain a component that exist in '" +
                                   libraryname + "' : " + component, 0)

    @classmethod
    def get_component_lib_path(cls, name=None):
        """ Get the path of library"""
        path_list = []
        try:
            for node in\
                    SETTINGS.active_project.get_subnodes("componentslibs",
                                                         "componentslib"):
                path_list.append(node.get_attr_value(key="path"))
            for libpath in path_list:
                if libpath.split("/")[-1] == name:
                    return libpath
            return []
        except AttributeError:
            return []

    def get_component_lib_name(self):
        """ Get the name of library"""
        name_list = []
        for path in self.get_component_lib_path():
            name_list.append(path.split("/")[-1])
        return name_list

    @classmethod
    def personnal_libraries(cls):
        """ Get the list names of Personnal library"""
        return SETTINGS.personal_lib_name_list

    @classmethod
    def get_pers_lib_path(cls, name):
        """ Get the path library"""
        for libpath in SETTINGS.personal_lib_path_list:
            if libpath.split("/")[-1] == name:
                return libpath
        return ""

    def load(self, libname):
        """ Load a library with name given in parameter"""
        if libname not in self.libraries:
            raise PodError("No " + libname + " in pod libraries")
        self._libname = libname

    @property
    def lib_name(self):
        """ Get the library name """
        return self._libname
