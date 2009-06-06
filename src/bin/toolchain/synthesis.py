#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Synthesis.py
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
__versionTime__ = "30/05/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import sys
from periphondemand.bin.utils.settings   import Settings
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils            import wrappersystem as sy
from periphondemand.bin.utils.error      import Error
from periphondemand.bin.utils.display    import Display

from periphondemand.bin.define import *

settings = Settings()
display  = Display()

class Synthesis(WrapperXml):
    """ Manage synthesis
    """

    def __init__(self,parent):
        self.parent = parent
        filepath = settings.projectpath+"/"+SYNTHESISPATH+"/synthesis"+XMLEXT
        if not sy.fileExist(filepath):
            raise Error("No synthesis project found",3)
        WrapperXml.__init__(self,file=filepath)
        # adding path for toolchain plugin
        sys.path.append(settings.path+TOOLCHAINPATH+\
                SYNTHESISPATH+"/"+self.getName())


    def save(self):
        self.saveXml(settings.projectpath+"/synthesis/synthesis"+XMLEXT)

    def getSynthesisToolName(self):
        """ return synthesis tool name """
        return self.getAttribute(key="name",subnodename="tool")
    def getSynthesisToolCommand(self):
        """ Test if command exist and return it """
        command_name = self.getAttribute(key="command",subnodename="tool")
        if not sy.commandExist(command_name):
            raise Error("Synthesis tool tcl shell command named "+command_name+\
                    "doesn't exist in PATH");
        return command_name

    def generateProject(self):
        """ copy all hdl file in synthesis project directory
        """
        for component in self.parent.getInstancesList():
            if component.getNum() == "0":
                # Make directory
                compdir = settings.projectpath+SYNTHESISPATH+"/"+\
                          component.getName()
                if sy.dirExist(compdir):
                    display.msg("Directory "+compdir+" exist, will be deleted")
                    sy.delDirectory(compdir)
                sy.makeDirectory(compdir)
                display.msg("Make directory for "+component.getName())
                # copy hdl files
                for hdlfile in component.getHdl_filesList():
                    try:
                        sy.copyFile(settings.projectpath+\
                                COMPONENTSPATH+\
                                "/"+\
                                component.getInstanceName()+\
                                "/hdl/"+\
                                hdlfile.getFileName(),
                                compdir+"/")
                    except IOError,e:
                        print display
                        raise Error(str(e),0)

    def generateTCL(self,filename=None):
        """ generate tcl script to drive synthesis tool """
        try:
            plugin = __import__(self.getName())
        except ImportError,e:
            sys.path.remove(settings.path+TOOLCHAINPATH+\
                    SYNTHESISPATH+"/"+self.getName())
            raise Error(str(e),0)
        sys.path.append(settings.path+TOOLCHAINPATH+\
                    SYNTHESISPATH+"/"+self.getName())
        filename = plugin.generateTCL(self)
        self.setTCLScriptName(filename)
        return None

    def setTCLScriptName(self,filename):
        if self.getNode("script")==None:
            self.addNode(nodename="script",
                         attributename="filename",
                         value=str(filename))
        else:
            self.setAttribute(key="filename",
                              value=filename,
                              subname="script")

    def getTCLScriptName(self):
        try:
            return self.getAttribute(key="filename",subnodename="script")
        except Error,e:
            raise Error("TCL script must be generated before")

    def generatePinout(self,filename):
        """ Generate pinout constraints file """
        try:
            plugin = __import__(self.getName())
        except ImportError,e:
            sy.delFile(settings.path+TOOLCHAINPATH+\
                    SYNTHESISPATH+"/"+self.getName())
            raise Error(str(e),0)
        sy.delFile(settings.path+TOOLCHAINPATH+\
                SYNTHESISPATH+"/"+self.getName())

        plugin.generatepinout(self,filename)
        return None

    def generateBitStream(self):
        """ Generate the bitstream for fpga configuration """
        try:
            plugin = __import__(self.getName())
        except ImportError,e:
            raise Error(str(e),0)
        tclscript_name = self.getTCLScriptName()
        scriptpath = settings.projectpath+SYNTHESISPATH+"/"+tclscript_name
        plugin.generateBitStream(self,self.getSynthesisToolCommand(),
                                 scriptpath)

