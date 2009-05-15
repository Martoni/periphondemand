#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     entityparser.py
# Purpose:  
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  06/05/2009
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
__versionTime__ = "06/05/2009"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import re


from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.code.vhdl.vhdlentityparser import VHDLEntityParser
from periphondemand.bin.utils.error import Error

class EntityParser:
    """ Abstract class used to parse HDL files
    """
    def __init__(self):
        pass

    def factory(self,filepath):
        self.filepath = filepath
        langage = self.getHDLLangage(filepath) 
        if self.getHDLLangage(filepath) == "VHDL":
            return VHDLEntityParser(filepath)
        else:
            raise Error("Unknown langage")

    def getHDLLangage(self,filepath):
        """ return HDL description langage of the file """
        if re.match(r'.*\.vhd$',filepath) or re.match(r'.*\.vhdl$',filepath):
            return "VHDL"
        else:
            return None

    def parseGeneric(self):
        """ Return list of generic found in current entity
            list of:
                {name:string,type:string,defautvalue:string,description:string}
        """
        raise Error("ParseGeneric not implemented")

    def parsePort(self):
        """ Return list of port found in current entity
            list of:
                {name:string,direction:string,type:string,size:string,description:string}
        """
        raise Error("ParsePort not implemented")

if __name__ == "__main__":
    print "entityparser class test\n"
    print entityparser.__doc__

