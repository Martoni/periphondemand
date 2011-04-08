#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Error.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/04/2008
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
#__versionTime__ = "30/04/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

INFO    = 2
WARNING = 1
ERROR   = 0

class Error(Exception):
    """ Manage specific error

    attributes:
        message -- the message
        level   -- the exception level
    """

    def __init__(self,message,level=0):
        self._message = message
        self.level   = level
        Exception.__init__(self,message)

    def __repr__(self):
        return self.message

    def _get_message(self):
        return self._message
    def _set_message(self, message):
        self._message = message
    message = property(_get_message, _set_message)


    def __str__(self):
        if self.level == 0:
            standardmsg = "[ERROR] : " + self.message
            try:
                if settings.color()==1:
                    return COLOR_ERROR+"[ERROR]"+COLOR_END+"  : "+\
                            COLOR_ERROR_MESSAGE+self.message+\
                            COLOR_END
                else:
                    return standardmsg
            except NameError:
                return standardmsg
        elif self.level == 1:
            standardmsg = "[WARNING] : " + self.message
            try:
                if settings.color()==1:
                    return COLOR_WARNING+"[WARNING]"+COLOR_END\
                            +": "+COLOR_WARNING_MESSAGE + self.message+\
                            COLOR_END
                else:
                    return standardmsg
            except NameError:
                return standardmsg
        else:
            standardmsg = "[INFO] : " + self.message
            try:
                if settings.color()==1:
                    return COLOR_INFO+"[INFO]"+COLOR_END+"   : "+\
                            COLOR_INFO_MESSAGE+self.message+COLOR_END
                else:
                    return standardmsg
            except NameError:
                return standardmsg

    def setLevel(self,level):
        self.level = int(str(level))
    def getLevel(self):
        return self.level

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.define import *

settings = Settings()

