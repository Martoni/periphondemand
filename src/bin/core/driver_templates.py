#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Driver_Templates.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  04/08/2008
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
thor__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.error      import Error
from periphondemand.bin.utils.display    import Display
from periphondemand.bin.utils.settings   import Settings

settings = Settings()
display  = Display()

class Driver_Templates(WrapperXml):
    """
    """
    def __init__(self,parent,**keys):
        """ init driver_templates,
            __init__(self,parent,node)
            __init__(self,parent,nodestring)
        """
        self.parent = parent
        if "node" in keys:
            self.__initnode(keys["node"])
        elif "nodestring" in keys:
            self.__initnodestring(keys["nodestring"])
        else:
            raise Error("Keys unknown in Driver_Templates init()",0)

    def __initnode(self,node):
        WrapperXml.__init__(self,node=node)
    def __initnodestring(self,nodestring):
        WrapperXml.__init__(self,nodestring=nodestring)

    def getTemplatesList(self):
        """ return a list of templates file name """
        return [template.getAttributeValue("name") for template in self.getNodeList("file")]

    def getVersionsList(self):
        """ return a list of version supported """
        return [version.getAttributeValue("version") for version in self.getNodeList("support")]

    def getArchitecture(self):
        """ return arcitecture name """
        return self.getAttributeValue("architecture")

