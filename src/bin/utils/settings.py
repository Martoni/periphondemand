#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     settings.py
# Purpose:  Store session settings and project parameters
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/01/22
# Licence:  GPLv3 or newer
# ----------------------------------------------------------------------------
"""Session settings and project parameters"""

import cmd
import re
import os
import sys

from periphondemand.bin.utils.configfile import ConfigFile
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.define import POD_PATH
from periphondemand.bin.define import POD_CONFIG


class Settings(object):
    """Settings class implements a Singleton design pattern to share the same
    state to all instance of this class.
    This class will store the application settings like directory location,
    active component and active project.
    """
    __instance = None
    __do_init = False

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            cls.__instance.__do_init = False
            return cls.__instance

        cls.__instance = object.__new__(cls, *args, **kwargs)
        cls.__instance.__do_init = True
        return cls.__instance

    def __init__(self):
        if self.__do_init:
            pathname, scriptname = os.path.split(sys.argv[0])
            self.history = []
            self.historyroot = []
            self.__script_dir = os.path.abspath(pathname)
            self.path = POD_PATH
            self.headertpl = "/headervhdl.tpl"
            self.script = 0
            self.projectpath = None
            self.color_status = 1
            # init personnal libraries path:
            try:
                self.configfile = ConfigFile(POD_CONFIG)
            except PodError:
                pass
            try:
                self.personal_lib_path_list = self.configfile.getLibraries()
                self.personal_lib_name_list =\
                    [pathlib.split("/")[-1]
                        for pathlib in self.personal_lib_path_list]
            except PodError:
                pass

            try:
                self.personal_platformlib_list =\
                    self.configfile.getPlatformLibPath()
                self.personal_platformlib_name_list =\
                    [pathlib.split("/")[-1]
                        for pathlib in self.personal_platformlib_list]
            except PodError:
                pass

            self.active_project = None
            self.active_library = None
            self.active_component = None

    def getPlatformLibPath(self, platformlib_name):
        for path in self.personal_platformlib_list:
            if path.split("/")[-1] == platformlib_name:
                return path

    def color(self):
        return self.color_status

    def setColor(self, value=1):
        self.color_status = value

    def getDir(self, sub_dir=None):
        if sub_dir:
            return os.path.join(self.__script_dir, sub_dir)
        else:
            return ""

    def isScript(self):
        return self.script

    def setScript(self, value):
        if value:
            self.script = 1
        else:
            self.script = 0

    def get_synthesis_tool_command(self, synthesisName):
        return self.configfile.get_synthesis_tool_command(synthesisName)

    components_dir = property(lambda self: self.getDir("components"))
    board_dir = property(lambda self: self.getDir("boards"))
