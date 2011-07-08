#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Cli.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  22/05/2008
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

__version__ = "1.0.0"
__versionTime__ = "22/05/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import cmd,os
#import readline

from periphondemand.bin.define   import *
from periphondemand.bin.utils.basecli  import BaseCli
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.basecli  import Statekeeper
from periphondemand.bin.utils.error    import Error
from periphondemand.bin.utils.display  import Display
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.core.project   import Project

from periphondemand.bin.commandline.projectcli import ProjectCli
from periphondemand.bin.commandline.librarycli import LibraryCli

settings = Settings()
display  = Display()

class Cli(BaseCli):
    """
    ---------------------------------
     Command line interpreter for POD
    ---------------------------------
    """
    # Specific command for project
    def __init__(self,parent=None):
        BaseCli.__init__(self,parent)
        settings.active_project = Project("void",void=1)

    def do_project(self,arg):
       """\
Usage : project
Project management commands
       """
       cli = ProjectCli(self)
       if not settings.active_project.isVoid():
           cli.setPrompt("project:"+settings.active_project.getName())
       else:
           cli.setPrompt("project")
       arg = str(arg)
       if len(arg) > 0:
           line = cli.precmd(arg)
           cli.onecmd(line)
           cli.postcmd(True, line)
       else:
           cli.cmdloop()
           self.stdout.write("\n")

    def complete_source(self,text,line,begidx,endidx):
        """ complete load command with files under directory """
        path = line.split(" ")[1]
        if path.find("/") == -1: # sub
            path = ""
        elif text.split() == "": # sub/sub/
            path = "/".join(path)+"/"
        else: # sub/sub
            path = "/".join(path.split("/")[0:-1]) + "/"
        listdir  = sy.listDirectory(path)
        listfile = sy.listFileType(path, PODSCRIPTEXT[1:])
        listfile.extend(listdir)
        return self.completelist(line,text,listfile)

    def do_source(self, fname=None):
        """\
Usage : source <filename>
use <filename> as standard input execute commands stored in.
Runs command(s) from a file.
        """
        keepstate = Statekeeper(self,
            ('stdin','use_rawinput','prompt','base_prompt','continuation_prompt'))
        try:
            self.stdin = open(fname, 'r')
        except IOError, e:
            try:
                self.stdin = open('%s.%s' % (fname, self.default_extension), 'r')
            except IOError:
                print 'Problem opening file %s: \n%s' % (fname, e)
                keepstate.restore()
                return
        self.use_rawinput = False
        self.prompt = self.continuation_prompt = ''
        settings.setScript(1)
        self.cmdloop()
        settings.setScript(0)
        self.stdin.close()
        keepstate.restore()
        self.lastcmd = ''
        return

    def do_version(self,line):
        """\
Usage : version
Print the version of POD
        """
        print "Peripherals On Demand version "+settings.version

if __name__ == "__main__":
    cli = Cli()
    settings = Settings()
    settings.path = "/home/fabien/POD/trunk/pod/"
    settings.projectpath = sy.pwd()
    cli.cmdloop()

