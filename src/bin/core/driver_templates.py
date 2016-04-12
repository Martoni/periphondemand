#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Driver_Templates.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  04/08/2008
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
""" Class that manage driver templates """

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.poderror import PodError


class DriverTemplates(WrapperXml):
    """ Manage drivers templates
    """
    def __init__(self, parent, **keys):
        """ init driver_templates,
            __init__(self,parent,node)
            __init__(self,parent,nodestring)
        """
        self.parent = parent
        if "node" in keys:
            WrapperXml.__init__(self, node=keys["node"])
        elif "nodestring" in keys:
            WrapperXml.__init__(self, nodestring=keys["nodestring"])
        else:
            raise PodError("Keys unknown in DriverTemplates init()", 0)

    @property
    def template_names(self):
        """ return a list of templates file name """
        return [template.get_attr_value("name") for
                template in self.get_nodes("file")]

    @property
    def versions(self):
        """ return a list of version supported """
        return [version.get_attr_value("version") for
                version in self.get_nodes("support")]

    @property
    def architecture_name(self):
        """ return arcitecture name """
        return self.get_attr_value("architecture")
