#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     ghdl.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  24/07/2008
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
""" Generate simulation code for GHDL """

from periphondemand.bin.define import VHDLEXT
from periphondemand.bin.define import ONETAB
from periphondemand.bin.define import SIMULATIONPATH
from periphondemand.bin.define import SYNTHESISPATH
from periphondemand.bin.define import TEMPLATESPATH
from periphondemand.bin.define import HEADERTPL

from periphondemand.bin.code.topgen import TopGen

from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils.poderror import PodError

import time
import datetime

MAKEFILETEMPLATE = "ghdlsimulationmakefile"
SETTINGS = Settings()
DISPLAY = Display()


def header():
    """ return vhdl header
    """
    header = open(SETTINGS.path + TEMPLATESPATH + "/" + HEADERTPL, "r").read()
    header = header.replace("$tpl:author$", SETTINGS.author)
    header = header.replace("$tpl:date$", str(datetime.date.today()))
    header = header.replace("$tpl:filename$", "Top_" +
                            SETTINGS.active_project.getName() + "_tb.vhd")
    header = header.replace("$tpl:abstract$",
                            SETTINGS.active_project.getDescription())
    return header


def include():
    include = ""
    platform = SETTINGS.active_project.platform
    for library in platform.getLibrariesList():
        for line in library.getDescription().split("\n"):
            include = include + "-- " + line + "\n"
        include = include + "use " +\
            SETTINGS.active_project.simulation_toolchain.getLibrary() +\
            "." + library.getFileName().replace(VHDLEXT, ".all") + ";\n"
    return include


def entity():
    """ return entity code
    """
    entity = "\nentity " + "top_" +\
        SETTINGS.active_project.getName() + "_tb is\n"
    entity = entity + "end entity top_" +\
        SETTINGS.active_project.getName() + "_tb;\n\n"
    return entity


def architecturehead():
    """ return architecture head VHDL code
    """
    arch = "architecture RTL of " + "top_" +\
        SETTINGS.active_project.getName() + "_tb is\n\n"
    return arch


def constant(clockhalfperiod):
    """ return constant declaration
    """
    constant = ONETAB + "CONSTANT HALF_PERIODE : time := " +\
        str(clockhalfperiod) + " ns;  -- Half clock period\n"
    for instance in SETTINGS.active_project.instances:
        for interface in instance.getInterfacesList():
            for register in interface.getRegisterList():
                constant = constant + ONETAB + "CONSTANT " +\
                    instance.getInstanceName().upper() + "_" +\
                    register.getName().upper() +\
                    " : std_logic_vector := x\"" + register.getAbsoluteAddr() +\
                    "\";\n"
    return constant


def signals(portlist):
    """ return signal declaration
    """
    out = ""
    for port in portlist:
        portname = port.getName()
        interfacename = port.parent.getName()
        instancename = port.parent.parent.getInstanceName()
        out = out + ONETAB + "signal  " +\
            instancename + "_" + portname + " : "
        if port.getMSBConnected() < 1:
            out = out + " std_logic;"
        else:
            out = out + " std_logic_vector(" + str(port.getMSBConnected()) +\
                " downto 0);"
        out = out + "\n"
    return out


def declareTop(portlist):
    """ declare top component
    """

    out = "\n" + ONETAB + "component top_" + SETTINGS.active_project.getName()
    out = out + "\n" + ONETAB + "port ("

    for port in portlist:
        portname = port.getName()
        interfacename = port.parent.getName()
        instancename = port.parent.parent.getInstanceName()
        out = out + ONETAB * 2 +\
            instancename + "_" + portname + \
            " : " + port.getDir()
        if port.getMSBConnected() < 1:
            out = out + " std_logic;"
        else:
            out = out + " std_logic_vector(" +\
                str(port.getMSBConnected()) + " downto 0);"
        out = out + "\n"
    # Suppress the #!@ last semicolon
    out = out[:-2]
    out = out + "\n" + ONETAB + ");\n"
    out = out + ONETAB + "end component top_" +\
        SETTINGS.active_project.getName() + ";\n"
    return out


def beginarch():
    return "\nbegin\n\n"


def connectTop(portlist):
    out = ONETAB + "top : top_" + SETTINGS.active_project.getName() + "\n"
    out = out + ONETAB + "port map(\n"

    for port in portlist:
        portname = port.getName()
        interfacename = port.parent.getName()
        instancename = port.parent.parent.getInstanceName()

        # sig declaration
        out = out + ONETAB * 2 + instancename + "_" + portname +\
            " => " + instancename + "_" + portname + ", \n"
    # Suppress the #!@ last comma
    out = out[:-2]
    out = out + "\n" + ONETAB + ");\n"
    return out


def clock(clockname):
    """ write clock process
    """
    clock = ONETAB + "clockp : process\n" + ONETAB + "begin\n"
    clock = clock + ONETAB * 2 + clockname + " <= '1';\n"
    clock = clock + ONETAB * 2 + "wait for HALF_PERIODE;\n"
    clock = clock + ONETAB * 2 + clockname + " <= '0';\n"
    clock = clock + ONETAB * 2 + "wait for HALF_PERIODE;\n"
    clock = clock + ONETAB + "end process clockp;\n"
    return clock


def stimulis():
    """ write a template stimulis processus
    """
    return """
    stimulis : process
    begin
    -- write stimulis here
    wait for 10 us;
    assert false report "End of test" severity error;
    end process stimulis;
    """


def endarch():
        return "end architecture RTL;\n"


def generateTemplate():
    """ generate Template Testbench
    """
    filename = SETTINGS.projectpath + SIMULATIONPATH +\
        "/top_" + SETTINGS.active_project.getName() +\
        "_tb" + VHDLEXT
    clockportlist = SETTINGS.active_project.clock_ports
    if len(clockportlist) == 0:
        raise PodError("No external clock signal found", 0)
    if len(clockportlist) != 1:
        DISPLAY.msg("More than one external clock in design", 1)
    clockport = clockportlist[0]
    clockname = clockport.parent.parent.getInstanceName() +\
        "_" + clockport.getName()

    ###################
    # header
    out = header()
    out = out + include()
    out = out + entity()
    out = out + architecturehead()
    freq = clockport.getDestinationPort().getFreq()
    clockhalfperiod = (1000 / float(freq)) / 2
    out = out + constant(clockhalfperiod)
    portlist = SETTINGS.active_project.platform.getConnectPortsList()
    out = out + signals(portlist)
    out = out + declareTop(portlist)
    out = out + beginarch()
    out = out + connectTop(portlist)

    out = out + stimulis()

    out = out + "\n"
    out = out + clock(clockname)
    out = out + "\n"
    out = out + endarch()
    #######################
    # save file
    if sy.fileExist(filename):
        DISPLAY.msg("[WARNING] File exist, file renamed in " +
                    filename + "old", 0)
        sy.renameFile(filename, filename + "old")
    try:
        afile = open(filename, "w")
    except IOError, error:
        raise error
    afile.write(out)
    afile.close()
    return filename


def generateMakefile():
    """ generate makefile for ghdl
    """
    # include file list:
    srclist = []
    platform = SETTINGS.active_project.platform
    projectname = "top_" + SETTINGS.active_project.getName()
    srclist.append(".." + SYNTHESISPATH + "/top_" +
                   SETTINGS.active_project.getName() + VHDLEXT)
    for component in SETTINGS.active_project.instances:
        if component.getNum() == "0":
            compdir = ".." + SYNTHESISPATH + "/" + component.getName() + "/"
            for hdlfile in component.getHdl_filesList():
                srclist.append(compdir + hdlfile.getFileName().split("/")[-1])

    librarylist = []
    for library in platform.getLibrariesList():
        srclist.append(library.getFileName())
        librarylist.append(library.getFileName())

    makefile = open(SETTINGS.path + TEMPLATESPATH +
                    "/" + MAKEFILETEMPLATE, "r").read()
    makefile = makefile.replace(r'$tpl:projectname$', projectname)
    makefile = makefile.replace(r'$tpl:files$', " ".join(srclist))
    makefile = makefile.replace(r'$tpl:library$', " ".join(librarylist))

    makefilename = SETTINGS.projectpath + SIMULATIONPATH + "/Makefile"
    afile = open(makefilename, "w")
    afile.write(makefile)
    afile.close()
    return makefilename
