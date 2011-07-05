#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Display.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  18/07/2008
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
__versionTime__ = "18/07/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

from periphondemand.bin.define import *
from periphondemand.bin.utils.settings import Settings

settings = Settings()

class Display(object):
    """ Class used to display messages,
        level:
        0 : error
        1 : warning
        2 : info
    """
    instance = None

    class __Display:
        def __init__(self):
            self.msglist = []
            self.val = None
        def __str__(self):
            out = ""
            for msg in self.msglist:
                if   msg[1] == 0:
                     try:
                         if settings.color()==1:
                             out = out + COLOR_ERROR+"[ERROR]"+COLOR_END+"  : "+\
                                     COLOR_ERROR_MESSAGE+msg[0].strip()+\
                                     COLOR_END+"\n"
                         else:
                             out = out+"[ERROR]  : "+msg[0].strip()+"\n"
                     except NameError:
                         out = out+"[ERROR]  : "+msg[0].strip()+"\n"
                elif msg[1] == 1:
                     try:
                         if settings.color()==1:
                             out = out + COLOR_WARNING+"[WARNING]"+COLOR_END+": "+\
                                     COLOR_WARNING_MESSAGE+msg[0].strip()+\
                                     COLOR_END+"\n"
                         else:
                             out = out+"[WARNING]: "+msg[0].strip()+"\n"
                     except NameError:
                         out = out+"[WARNING]: "+msg[0].strip()+"\n"
                elif msg[1] == 2:
                     out = out+msg[0].strip()+"\n"

            self.msglist = []
            return out

        def msg(self,msg,level=2):
            self.msglist.append((msg,level))

    def __new__(c): # _new_ is always class method
        if not Display.instance:
               Display.instance = Display.__Display()
        return Display.instance

    def __getattr__(self, attr):
       return getattr(self.instance, attr)

