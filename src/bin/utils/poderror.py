#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     PodError.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/04/2008
# ----------------------------------------------------------------------------
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
# ----------------------------------------------------------------------------
""" PodError class """

from periphondemand.bin.define import COLOR_INFO
from periphondemand.bin.define import COLOR_INFO_MESSAGE
from periphondemand.bin.define import COLOR_END
from periphondemand.bin.define import COLOR_WARNING
from periphondemand.bin.define import COLOR_WARNING_MESSAGE
from periphondemand.bin.define import COLOR_ERROR
from periphondemand.bin.define import COLOR_ERROR_MESSAGE

INFO = 2
WARNING = 1
ERROR = 0


class PodError(Exception):
    """ Manage specific error

    attributes:
        message -- the message
        level   -- the exception level
    """

    def __init__(self, message, level=0):
        self._message = message
        self.level = level
        Exception.__init__(self, message)

    def __repr__(self):
        return self.message

    @property
    def message(self):
        """ get message """
        return self._message

    @message.setter
    def message(self, message):
        """ Set message """
        self._message = message

    def __str__(self):
        if self.level == 0:
            standardmsg = "[ERROR] : " + self.message
            try:
                if SETTINGS.color() == 1:
                    return COLOR_ERROR + "[ERROR]" + COLOR_END + "  : " +\
                        COLOR_ERROR_MESSAGE + self.message +\
                        COLOR_END
            except NameError:
                pass
        elif self.level == 1:
            standardmsg = "[WARNING] : " + self.message
            try:
                if SETTINGS.color() == 1:
                    return COLOR_WARNING + "[WARNING]" + COLOR_END +\
                        ": " + COLOR_WARNING_MESSAGE + self.message +\
                        COLOR_END
            except NameError:
                pass
        else:
            standardmsg = "[INFO] : " + self.message
            try:
                if SETTINGS.color() == 1:
                    return COLOR_INFO + "[INFO]" + COLOR_END + "   : " +\
                        COLOR_INFO_MESSAGE + self.message + COLOR_END
            except NameError:
                pass
        return standardmsg

from periphondemand.bin.utils.settings import Settings
SETTINGS = Settings()
