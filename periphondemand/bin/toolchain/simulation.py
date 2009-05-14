#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Simulation.py
# Purpose:  
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  16/07/2008
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
__versionTime__ = "16/07/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

from periphondemand.bin.define import *
from periphondemand.bin.utils.settings   import Settings
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils            import wrappersystem as sy
from periphondemand.bin.utils.display    import Display
from periphondemand.bin.utils.error      import Error

settings = Settings()
display  = Display()

class Simulation(WrapperXml):
    """ Manage simulation
    """

    def __init__(self,parent):
        self.parent = parent
        filepath = settings.projectpath+"/"+SIMULATIONPATH+"/simulation"+XMLEXT
        if not sy.fileExist(filepath):
            raise Error("No simulation project found",3)
        WrapperXml.__init__(self,file=filepath)

    def generateProject(self):
        display.msg("TODO")
        pass

    def getLibrary(self):
        return self.getNode("library").getAttribute("name")

    def getLanguage(self):
        return self.getNode("language").getAttribute("name")

    def generateTemplate(self):
        import sys
        sys.path.append(settings.path+TOOLCHAINPATH+SIMULATIONPATH+"/"+self.getName())
        try:
            plugin = __import__(self.getName())
        except ImportError,e:
            sys.path.remove(settings.path+TOOLCHAINPATH+SIMULATIONPATH+"/"+self.getName())
            raise Error(str(e),0)
        sys.path.remove(settings.path+TOOLCHAINPATH+SIMULATIONPATH+"/"+self.getName())
        return plugin.generateTemplate()

    def generateMakefile(self):
        import sys
        sys.path.append(settings.path+TOOLCHAINPATH+SIMULATIONPATH+"/"+self.getName())
        try:
            plugin = __import__(self.getName())
        except ImportError,e:
            sys.path.remove(settings.path+TOOLCHAINPATH+SIMULATIONPATH+"/"+self.getName())
            raise Error(str(e),0)
        sys.path.remove(settings.path+TOOLCHAINPATH+SIMULATIONPATH+"/"+self.getName())
        return plugin.generateMakefile()

    def save(self):
        self.saveXml(settings.projectpath+"/simulation/simulation"+XMLEXT)
