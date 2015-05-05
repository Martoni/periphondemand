#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     SynthesisCli.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/05/2008
# ----------------------------------------------------------------------------
#  Copyright (2008)  Armadeus Systems
# ----------------------------------------------------------------------------
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
""" Command line for synthesis environment """


from periphondemand.bin.define import TOOLCHAINPATH 
from periphondemand.bin.define import SYNTHESISPATH 

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.basecli import BaseCli
from periphondemand.bin.utils.error import Error
from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils import wrappersystem as sy

from periphondemand.bin.toolchain.synthesis import Synthesis

SETTINGS = Settings()
DISPLAY = Display()


class SynthesisCli(BaseCli):
    """
    """

    def __init__(self, parent):
        BaseCli.__init__(self, parent)

    def complete_selecttoolchain(self, text, line, begidx, endidx):
        toolchainlist = []
        try:
            toolchainlist = self.completeargs(text, line,
                                              "[synthesistoolchain]")
        except Exception, error:
            print(str(error))
        return toolchainlist

    def do_selecttoolchain(self, line):
        """\
Usage : selecttoolchain [synthesistoolchain]
select toolchain used for simulation
        """
        try:
            self.checkargs(line, "[synthesistoolchain]")
        except Error, error:
            print(str(error))
            return

        if line.strip() == "":
            if len(SETTINGS.active_project.get_synthesis_toolchains()) == 1:
                SETTINGS.active_project.synthesis_toolchain =\
                    SETTINGS.active_project.get_synthesis_toolchains()[0]
            else:
                if SETTINGS.active_project.synthesis_toolchain is None:
                    print("Choose a toolchain\n")
                    for toolchain in \
                           SETTINGS.active_project.get_synthesis_toolchains():
                        print(str(toolchain))
                    return
        else:
            try:
                SETTINGS.active_project.synthesis_toolchain = line
            except Error, error:
                print(str(error))
                return

    def complete_generateproject(self, text, line, begidx, endidx):
        toollist = []
        try:
            toollist = self.completeargs(text, line,
                                         "[synthesistoolchain]")
        except Exception, error:
            print(str(error))
        return toollist

    def do_generateproject(self, line):
        """\
Usage : generateproject [synthesistoolchain]
generate the project for synthesis tool
        """
        try:
            self.checkargs(line, "[synthesistoolchain]")
        except Error, error:
            print(str(error))
            return
        # select toolchain
        if line.strip() != "":
            try:
                self.do_selecttoolchain(line)
            except Error, error:
                print(str(error))
                return
        elif SETTINGS.active_project.synthesis is None:
            print(str(Error("Toolchain must be selected before")))
            return

        # generate project
        try:
            SETTINGS.active_project.synthesis.generateProject()
            print(str(DISPLAY))
            pinoutfile = SETTINGS.active_project.synthesis.generatePinout(None)
            print(str(DISPLAY))
            tclname = SETTINGS.active_project.synthesis.generateTCL(None)
        except Error, error:
            print(str(error))
            return
        print(str(DISPLAY))

    def do_generatetcl(self, line):
        """\
Usage : generatetcl [filename]
Made a tcl script for synthesis,tools supported are:
ise
        """

        if SETTINGS.active_project.synthesis is None:
            print Error("Select toolchain before")
            return
        if line.strip() != "":
            filename = SETTINGS.path + TOOLCHAINPATH +\
                       SYNTHESISPATH + "/" + line.strip()
        else:
            filename = None
        try:
            SETTINGS.active_project.synthesis.generateTCL(filename)
        except Error, error:
            print(str(error))
            return
        print DISPLAY

    def do_generatepinout(self, line):
        """\
Usage : generatepinout [filename]
generate ucf file, tool supported are :
ise
        """
        if SETTINGS.active_project.synthesis is None:
            print(str(Error("Select toolchain before")))
            return
        if line.strip() != "":
            filename = SETTINGS.path + TOOLCHAINPATH +\
                       SYNTHESISPATH + "/" + line.strip()
        else:
            filename = None
        try:
            SETTINGS.active_project.synthesis.generatePinout(filename)
        except Error, error:
            print(str(error))
            return
        print(str(DISPLAY))

    def do_generatebitstream(self, line):
        """\
Usage : generatebitstream
generate the bitstream for fpga configuration
        """
        if SETTINGS.active_project.synthesis is None:
            print Error("Select toolchain before")
            return
        try:
            SETTINGS.active_project.synthesis.generateBitStream()
        except Error, error:
            print(str(error))
            return
        print DISPLAY

    def complete_setiostandard(self, text, line, begidx, endidx):
        IOlist = []
        try:
            IOlist = self.completeargs(text, line, "<IO_name>")
        except Exception, e:
            print e
        return IOlist

    def do_setiostandard(self, line):
        """\
Usage : setiostandard <IO_name> <standard_value>
set IO standard value
        """
        try:
            self.checkargs(line, "<IO_name> <standard_value>")
        except Exception, error:
            print(str(DISPLAY))
            print(str(error))
            return
        arg = line.split(' ')
        io_name = arg[0]
        standard_value = arg[1]
        try:
            SETTINGS.active_project.get_io(io_name).setStandard(standard_value)
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return

    def complete_getiostandard(self, text, line, begidx, endidx):
        IOlist = []
        try:
            IOlist = self.completeargs(text, line, "<IO_name>")
        except Exception, error:
            print(str(error))
        return IOlist

    def do_getiostandard(self, line):
        """\
Usage : getiostandard <IO_name>
get IO standard value
        """
        try:
            self.checkargs(line, "<IO_name>")
        except Exception, error:
            print(str(DISPLAY))
            print(str(error))
            return
        arg = line.split(' ')
        io_name = arg[0]
        try:
            print SETTINGS.active_project.get_io(io_name).getStandard()
        except Error, e:
            print DISPLAY
            print e
            return
        print DISPLAY

    def complete_setportoption(self, text, line, begidx, endidx):
        IOlist = []
        try:
            IOlist = self.completeargs(text, line, "<IO_name>")
        except Exception, error:
            print(str(error))
        return IOlist

    def do_setportoption(self, line):
        """\
Usage : setportoption <IO_name> <port_option_value>
set IO standard value
        """
        try:
            self.checkargs(line, "<IO_name> <port_option_value>")
        except Exception, error:
            print(str(DISPLAY))
            print(str(error))
            return
        arg = line.split(' ')
        io_name = arg[0]
        port_option_value = arg[1]
        try:
            SETTINGS.active_project.get_io(
                    io_name).setPortOption(port_option_value)
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return

    def complete_getportoption(self, text, line, begidx, endidx):
        IOlist = []
        try:
            IOlist = self.completeargs(text, line, "<IO_name>")
        except Exception, error:
            print(str(error))
        return IOlist

    def do_getportoption(self, line):
        """\
Usage : getportoption <IO_name>
get IO Port option value
        """
        try:
            self.checkargs(line, "<IO_name>")
        except Exception, e:
            print DISPLAY
            print e
            return
        arg = line.split(' ')
        io_name = arg[0]
        try:
            print SETTINGS.active_project.get_io(io_name).getPortOption()
        except Error, e:
            print DISPLAY
            print e
            return
        print DISPLAY

    def complete_setiodrive(self, text, line, begidx, endidx):
        IOlist = []
        try:
            IOlist = self.completeargs(text, line, "<IO_name>")
        except Exception, error:
            print(str(error))
        return IOlist

    def do_setiodrive(self, line):
        """\
Usage : setiodrive <IO_name> <drive_value>
set IO drive value
        """
        try:
            self.checkargs(line, "<IO_name> <drive_value>")
        except Exception, error:
            print(str(DISPLAY))
            print(str(errror))
            return
        arg = line.split(' ')
        io_name = arg[0]
        drive_value = arg[1]
        try:
            SETTINGS.active_project.get_io(io_name).setDrive(drive_value)
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return

    def complete_getiodrive(self, text, line, begidx, endidx):
        IOlist = []
        try:
            IOlist = self.completeargs(text, line, "<IO_name>")
        except Exception, error:
            print(str(error))
        return IOlist

    def do_getiodrive(self, line):
        """\
Usage : getiodrive <IO_name>
get IO drive value
        """
        try:
            self.checkargs(line, "<IO_name>")
        except Exception, error:
            print(str(DISPLAY))
            print(str(error))
            return
        arg = line.split(' ')
        io_name = arg[0]
        try:
            print SETTINGS.active_project.get_io(io_name).getDrive()
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print(str(DISPLAY))

    def complete_setfpga(self, text, line, begidx, endidx):
        attributes = []
        try:
            attributes = self.completeargs(text, line, "<fpga_attributes>")
        except Exception, error:
            print(str(error))
        return attributes

    def do_setfpga(self, line):
        """\
Usage : setfpga <fpga_attributes> <attribute_value>
Set fpga attributes
        """
        try:
            self.checkargs(line, "<fpga_attributes> <attribute_value>")
        except Exception, error:
            print(str(DISPLAY))
            print(str(error))
            return
        arg = line.split(' ')
        att_name = arg[0]
        att_value = arg[1]
        try:
            platform = SETTINGS.active_project.platform
            platform.setAttribute(att_name, att_value, "fpga")
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print(str(DISPLAY))

    def complete_getfpga(self, text, line, begidx, endidx):
        attributes = []
        try:
            attributes = self.completeargs(text, line, "<fpga_attributes>")
        except Exception, error:
            print(str(error))
        return attributes

    def do_getfpga(self, line):
        """\
Usage : getfpga <fpga_attributes>
get fpga attributes values
        """
        try:
            self.checkargs(line, "<fpga_attributes>")
        except Exception, error:
            print(str(DISPLAY))
            print(str(error))
            return
        arg = line.split(' ')
        att_name = arg[0]
        try:
            platform = SETTINGS.active_project.platform
            print(str(platform.getAttributeValue(att_name, "fpga")))
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print(str(DISPLAY))
