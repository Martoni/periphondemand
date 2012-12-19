#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     DriverCli.py
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
from periphondemand.bin.utils.basecli  import BaseCli
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.error    import Error
from periphondemand.bin.utils.display  import Display
from periphondemand.bin.utils          import wrappersystem as sy

display  = Display()
settings = Settings()

class DriverCli(BaseCli):
    """
    """

    def __init__(self,parent):
        BaseCli.__init__(self,parent)
        self.driver = settings.active_project.driver
        self.project = settings.active_project

    def testIfToolChainSelected(self):
        if self.driver==None:
            raise Error("No toolchain selected (use selecttoolchain command)")

    def complete_generateproject(self,text,line,begidx,endidx):
        toollist = []
        try:
            toollist = self.completeargs(text,line,"[drivertoolchain]")
        except Exception,e:
            print e
        return toollist

    def do_generateproject(self,line):
        """\
Usage : generateproject
generate a project drivers directory with templates
        """
        try:
            self.testIfToolChainSelected()
            self.driver.generateProject()
            self.driver.fillAllTemplates()
        except Error,e:
            print display
            print e
            return
        print display

    def do_filltemplates(self,line):
        """\
Usage : filltemplates
fill drivers templates
        """
        try:
            self.testIfToolChainSelected()
            self.driver.fillAllTemplates()
        except Error,e:
            print display
            print e
            return
        print display

    def do_copydrivers(self,line):
        """\
Usage : copydrivers
copy drivers file in software developpement tree. Developpement tree
directory must be selected with setprojecttree
        """
        try:
            self.testIfToolChainSelected()
            self.driver.copyBSPDrivers()
        except Error,e:
            print display
            print e
            return
        print display

    def complete_selectprojecttree(self,text,line,begidx,endidx):
        """complete selectprojecttree command directories """
        path = line.split(" ")[1]
        if path.find("/") == -1: # sub
            path = ""
        elif text.split() == "": # sub/sub/
            path = "/".join(path)+"/"
        else: # sub/sub
            path = "/".join(path.split("/")[0:-1]) + "/"
        listdir = sy.listDirectory(path)
        return self.completelist(line,text,listdir)

    def do_selectprojecttree(self,line):
        """\
Usage : setprojecttree [directory]
select software developpement tree, to copy driver
        """
        try:
            self.testIfToolChainSelected()
            self.driver.setBSPDirectory(line)
        except Error,e:
            print display
            print e
            return
        print display

    def complete_selecttoolchain(self,text,line,begidx,endidx):
        toolchainlist = []
        try:
            toolchainlist = self.completeargs(text,line,"[drivertoolchain]")
        except Exception,e:
            print e
        return toolchainlist

    def do_selecttoolchain(self,line):
        """\
Usage : selecttoolchain [drivertoolchain]
select operating system to generate drivers
        """
        try:
            self.checkargs(line,"[drivertoolchain]")
        except Error,e:
            print display
            print e
            return
        if line.strip() == "":
            if len(settings.active_project.getDriverToolChainList())==1:
                settings.active_project.setDriverToolChain(
                    settings.active_project.getDriverToolChainList()[0])
            else:
                if settings.active_project.getDriverToolChain() == None:
                    print "Choose a toolchain\n"
                    for toolchain in \
                            settings.active_project.getDriverToolChainList():
                        print toolchain
                    return
        else:
            try:
                settings.active_project.setDriverToolChain(line)
            except Error,e:
                print e
                return
        self.driver = settings.active_project.driver


