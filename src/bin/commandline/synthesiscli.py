#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     SynthesisCli.py
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

from periphondemand.bin.define                     import *

from periphondemand.bin.utils.settings             import Settings
from periphondemand.bin.utils.basecli              import BaseCli
from periphondemand.bin.utils.error                import Error
from periphondemand.bin.utils.display              import Display
from periphondemand.bin.utils import wrappersystem as sy

from periphondemand.bin.toolchain.synthesis        import Synthesis

settings = Settings()
display  = Display()

class SynthesisCli(BaseCli):
    """
    """

    def __init__(self,parent):
        BaseCli.__init__(self,parent)

    def complete_selecttoolchain(self,text,line,begidx,endidx):
        toolchainlist = []
        try:
            toolchainlist = self.completeargs(text,line,"[synthesistoolchain]")
        except Exception,e:
            print e
        return toolchainlist

    def do_selecttoolchain(self,line):
        """\
Usage : selecttoolchain [synthesistoolchain]
select toolchain used for simulation
        """
        try:
            self.checkargs(line,"[synthesistoolchain]")
        except Error,e:
            print e
            return

        if line.strip() == "":
            if len(settings.active_project.getSynthesisToolChainList())==1:
                settings.active_project.setSynthesisToolChain(
                    settings.active_project.getSynthesisToolChainList()[0])
            else:
                if settings.active_project.getSynthesisToolChain() == None:
                    print "Choose a toolchain\n"
                    for toolchain in \
                            settings.active_project.getSynthesisToolChainList():
                        print toolchain
                    return
        else:
            try:
                settings.active_project.setSynthesisToolChain(line)
            except Error,e:
                print e
                return

    def complete_generateproject(self,text,line,begidx,endidx):
        toollist = []
        try:
            toollist = self.completeargs(text,line,"[synthesistoolchain]")
        except Exception,e:
            print e
        return toollist

    def do_generateproject(self,line):
        """\
Usage : generateproject [synthesistoolchain]
generate the project for synthesis tool
        """
        try:
            self.checkargs(line,"[synthesistoolchain]")
        except Error,e:
            print e
            return
        # select toolchain
        if line.strip() != "":
            try:
                self.do_selecttoolchain(line)
            except Error,e:
                print e
                return
        elif settings.active_project.synthesis== None:
            print Error("Toolchain must be selected before")
            return

        # generate project
        try:
            settings.active_project.synthesis.generateProject()
            print display
            pinoutfile = settings.active_project.synthesis.generatePinout(None)
            print display
            tclname = settings.active_project.synthesis.generateTCL(None)
        except Error,e:
            print e
            return
        print display

    def do_generatetcl(self,line):
        """\
Usage : generatetcl [filename]
Made a tcl script for synthesis,tools supported are:
ise
        """

        if settings.active_project.synthesis == None:
            print Error("Select toolchain before")
            return
        if line.strip() != "":
            filename = settings.path + TOOLCHAINPATH+\
                    SYNTHESISPATH+"/"+line.strip()
        else:
            filename = None
        try:
            settings.active_project.synthesis.generateTCL(filename)
        except Error,e:
            print e
            return
        print display

    def do_generatepinout(self,line):
        """\
Usage : generatepinout [filename]
generate ucf file, tool supported are :
ise
        """
        if settings.active_project.synthesis == None:
            print Error("Select toolchain before")
            return
        if line.strip() != "":
            filename = settings.path + TOOLCHAINPATH+SYNTHESISPATH+"/"+line.strip()
        else:
            filename = None
        try:
            settings.active_project.synthesis.generatePinout(filename)
        except Error,e:
            print e
            return
        print display

    def do_generatebitstream(self,line):
        """\
Usage : generatebitstream
generate the bitstream for fpga configuration
        """
        if settings.active_project.synthesis == None:
            print Error("Select toolchain before")
            return
        try:
            settings.active_project.synthesis.generateBitStream()
        except Error,e:
            print e
            return
        print display

