#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Hdl_file.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/05/2008
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
""" Managing list of hdl files """

import os

from periphondemand.bin.define import HDLEXT

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError

SETTINGS = Settings()


class HdlFile(WrapperXml):
    """ Manage source files
    """

    def __init__(self, parent, **keys):
        """ Init HdlFile,
            __init__(self, parent, node)
            __init__(self, filename, istop, scope)
        """
        self.parent = parent
        self.parser = None
        if "node" in keys:
            WrapperXml.__init__(self,
                                node=keys["node"])

        elif "filename" in keys:
            WrapperXml.__init__(self, nodename="hdl_file")
            if keys["istop"] == 1:
                self.settop()
            self.scope = keys["scope"]
            self.filename = keys["filename"]
        else:
            raise PodError("Keys unknown in HdlFile", 0)

    @property
    def filename(self):
        """ get filename """
        return self.get_attr_value("filename")

    @filename.setter
    def filename(self, filename):
        """ set filename """
        if filename.split(".")[-1] not in HDLEXT:
            raise PodError("File " + str(filename) + " is not an HDL file")
        self.set_attr("filename", filename)

    @property
    def filepath(self):
        """ return an open file pointer of HDL file """
        librarypath = SETTINGS.active_library.library_path()
        componentname = self.parent.name
        filepath = os.path.join(librarypath, componentname,
                                "hdl", self.filename)
        return filepath

    def istop(self):
        """ is it top HDL file ? """
        if self.get_attr_value("istop") == "1":
            return True
        else:
            return False

    def settop(self, istop=True):
        """ Set HDL as top component """
        if istop:
            self.set_attr("istop", "1")
        else:
            self.set_attr("istop", "0")

    @property
    def scope(self):
        """ getting scope """
        return self.get_attr_value("scope")

    @scope.setter
    def scope(self, scope):
        """ setting scope """
        lscope = ["both", "fpga", "driver"]
        if scope.lower() in lscope:
            self.set_attr("scope", scope)
        else:
            raise PodError("Unknown scope " + str(scope))
