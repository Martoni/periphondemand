#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Display.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  18/07/2008
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
#
# ----------------------------------------------------------------------------
""" Managing printing messages """

from periphondemand.bin.define import COLOR_ERROR
from periphondemand.bin.define import COLOR_END
from periphondemand.bin.define import COLOR_ERROR_MESSAGE
from periphondemand.bin.define import COLOR_WARNING_MESSAGE
from periphondemand.bin.define import COLOR_WARNING
from periphondemand.bin.define import COLOR_INFO_MESSAGE
from periphondemand.bin.define import COLOR_INFO

from periphondemand.bin.utils.settings import Settings

SETTINGS = Settings()


class Display(object):
    """ Class used to display messages,
        level:
        0 : error
        1 : warning
        2 : info
    """
    instance = None

    class __Display(object):
        """ Singleton object of display class """
        def __init__(self):
            self.msglist = []
            self.val = None

        def __str__(self):
            out = ""
            for msg in self.msglist:
                if msg[1] == 0:
                    try:
                        if SETTINGS.color() == 1:
                            out = out + COLOR_ERROR + "[ERROR]" +\
                                COLOR_END + "  : " +\
                                COLOR_ERROR_MESSAGE + msg[0].strip() +\
                                COLOR_END + "\n"
                        else:
                            out = out + "[ERROR]  : " + msg[0].strip() + "\n"
                    except NameError:
                        out = out + "[ERROR]  : " + msg[0].strip() + "\n"
                elif msg[1] == 1:
                    try:
                        if SETTINGS.color() == 1:
                            out = out + COLOR_WARNING + "[WARNING]" +\
                                COLOR_END + ": " +\
                                COLOR_WARNING_MESSAGE + msg[0].strip() +\
                                COLOR_END + "\n"
                        else:
                            out = out + "[WARNING]: " + msg[0].strip() + "\n"
                    except NameError:
                        out = out + "[WARNING]: " + msg[0].strip() + "\n"
                elif msg[1] == 2:
                    try:
                        if SETTINGS.color() == 1:
                            out = out + COLOR_INFO + "[INFO]" +\
                                COLOR_END + " : " +\
                                COLOR_INFO_MESSAGE + msg[0].strip() +\
                                COLOR_END + "\n"
                        else:
                            out = out + "[INFO] : " + msg[0].strip() + "\n"
                    except NameError:
                        out = out + "[INFO] : " + msg[0].strip() + "\n"
                else:
                    out = out + msg[0].strip() + "\n"

            self.msglist = []
            return out

        def msg(self, msg, level=3):
            """ message printer """
            self.msglist.append((msg, level))

    def __new__(cls):  # _new_ is always class method
        if not Display.instance:
            Display.instance = Display.__Display()
        return Display.instance

    def __getattr__(self, attr):
        return getattr(self.instance, attr)
