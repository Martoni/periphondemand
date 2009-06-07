#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     librarycli.py
# Purpose:  
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  27/04/2009
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
__versionTime__ = "27/04/2009"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import os
import periphondemand.bin.define

from   periphondemand.bin.utils import wrappersystem as sy
from   periphondemand.bin.utils.display  import Display

from   periphondemand.bin.utils.settings import Settings
from   periphondemand.bin.utils.basecli  import BaseCli
from   periphondemand.bin.utils.error    import Error

from   periphondemand.bin.commandline.componentcli import ComponentCli

from   periphondemand.bin.core.library   import Library
from   periphondemand.bin.core.component import Component

settings = Settings()
display  = Display()

class LibraryCli(BaseCli):
    """
    """
    def __init__(self,parent=None):
        BaseCli.__init__(self,parent)
        if settings.active_library == None:
            settings.active_library = Library()

    def complete_component(self,text,line,begidx,endidx):
        """
        """
        libname = settings.active_library.getLibName()
        if libname == None:
            return
        else:
            return  self.completeargs(text,line,"<libcomponentname>")

    def do_component(self,arg):
        """\
Usage : component <libcomponentname>
Create, edit and manage components in library
        """
        try:
            libname = settings.active_library.getLibName()
            if libname == None:
                raise Error("Library must be loaded before")
        except Error,e:
            print e
            return

        cli = ComponentCli(self)
        cli.setPrompt("component")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")

    def do_listlibrary(self,line):
        """\
Usage : listlibrary
List libraries available in POD
        """
        if line.strip() == "":
            return self.columnize(
                    settings.active_library.listLibraries())

    def complete_addlibrary(self,text,line,begidx,endidx):
        """ complete addlibrary command with files under directory """
        path = line.split(" ")[1]
        if path.find("/") == -1: # sub
            path = ""
        elif text.split() == "": # sub/sub/
            path = "/".join(path)+"/"
        else: # sub/sub
            path = "/".join(path.split("/")[0:-1]) + "/"
        listdir = sy.listDirectory(path)
        return self.completelist(line,text,listdir)

    def do_addlibrary(self,line):
        """\
Usage : addlibrary <librarydirectoryname>
Adding a personnal library in POD
        """
        try:
            self.checkargs(line,"<path>")
        except Error,e:
            print e
            return
        line = os.path.expanduser(line)
        if not os.path.exists(line):
            print Error("Directory doesn't exists")
            return
        try:
            settings.active_library.addLibrary(line)
        except Error,e:
            print e
            return
        except IOError,e:
            print e
            return
        print display

    def complete_dellibrary(self,text,line,begidx,endidx):
        """
        """
        completelist = []
        try:
            completelist = self.completeargs(text,line,"<libraryname>")
        except Exception,e:
            print e
        return completelist

    def do_dellibrary(self,line):
        """\
Usage : dellibrary <libraryname>
Delete a personnal library path from configfile
        """
        try:
            self.checkargs(line,"<libraryname>")
        except Error,e:
            print e
            return
        try:
            settings.active_library.delLibrary(line)
        except Error,e:
            print e
            return
        except IOError,e:
            print e
            return
        print display

    def complete_load(self,text,line,begidx,endidx):
        """ complete load command with libraries available """
        completelist = []
        try:
            completelist = self.completeargs(text,line,"<libraryname>")
        except Exception,e:
            print e
        return completelist

    def do_load(self,line):
        """\
Usage : projectload <projectfilename>.xml
Load a project
        """
        try:
            self.checkargs(line,"<libraryname>")
        except Error,e:
            print e
            return
        try:
            settings.active_library.load(line)
        except Error,e:
            print e
            return
        self.setPrompt("library:"+settings.active_library.getLibName())
        print display

    def do_listcomponents(self,line):
        """\
Usage : listcomponent
List component under active library
        """
        libname = settings.active_library.getLibName()
        if libname == None:
            print Error("Load a library before")
            return
        try:
            return self.columnize(
                    settings.active_library.listComponents(libname))
        except Error,e:
            print e
            return

if __name__ == "__main__":
    print "librarycli class test\n"
    print librarycli.__doc__

