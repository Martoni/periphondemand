#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     ghdl.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  24/07/2008
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
__versionTime__ = "24/07/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

from periphondemand.bin.define import *

from periphondemand.bin.code.topgen    import TopGen

from periphondemand.bin.utils          import wrappersystem as sy
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.display  import Display
from periphondemand.bin.utils.error    import Error

import time
import datetime

TAB = "    "
MAKEFILETEMPLATE="ghdlsimulationmakefile"
settings = Settings()
display  = Display()

def header():
    """ return vhdl header
    """
    header = open(settings.path + TEMPLATESPATH+ "/"+HEADERTPL,"r").read()
    header = header.replace("$tpl:author$",settings.author)
    header = header.replace("$tpl:date$",str(datetime.date.today()))
    header = header.replace("$tpl:filename$","Top_"+settings.active_project.getName()+"_tb.vhd")
    header = header.replace("$tpl:abstract$",settings.active_project.getDescription())
    return header

def include():
    include = ""
    platform = settings.active_project.getPlatform()
    for library in platform.getLibrariesList():
        for line in library.getDescription().split("\n"):
            include = include+"-- "+line+"\n"
        include = include + "use " +\
                  settings.active_project.simulation_toolchain.getLibrary() +\
                  "." + library.getFileName().replace(VHDLEXT,".all") + ";\n"
    return include

def entity():
    """ return entity code
    """
    entity = "\nentity "+"top_"+\
            settings.active_project.getName()+"_tb is\n"
    entity = entity + "end entity top_"+settings.active_project.getName()+"_tb;\n\n"
    return entity

def architecturehead():
    """ return architecture head VHDL code
    """
    arch = "architecture RTL of "+"top_"+settings.active_project.getName()+\
            "_tb is\n\n"
    return arch

def constant(clockhalfperiode):
    """ return constant declaration
    """
    constant = TAB+"CONSTANT HALF_PERIODE : time := "+str(clockhalfperiode)+" ns;  -- Half clock period\n"
    for instance in settings.active_project.instances:
        for interface in instance.getInterfacesList():
            for register in interface.getRegisterList():
                constant = constant + TAB +\
                        "CONSTANT "+\
                        instance.getInstanceName().upper()+\
                        "_"+\
                        register.getName().upper()+\
                        " : std_logic_vector := x\""+\
                        register.getAbsoluteAddr()+"\";"+\
                        "\n"
    return constant

def signals(portlist):
    """ return signal declaration
    """
    out = ""
    for port in portlist:
        portname = port.getName()
        interfacename = port.getParent().getName()
        instancename = port.getParent().getParent().getInstanceName()

        out = out + TAB +"signal  "+\
                instancename+"_"+portname +\
                " : "
        if port.getMSBConnected() <1:
            out = out + " std_logic;"
        else:
            out = out + " std_logic_vector("+str(port.getMSBConnected())\
                    +" downto 0);"
        out = out + "\n"
    return out

def declareTop(portlist):
    """ declare top component
    """

    out = "\n"+TAB+"component top_"+settings.active_project.getName()
    out = out + "\n" + TAB + "port ("

    for port in portlist:
        portname = port.getName()
        interfacename = port.getParent().getName()
        instancename = port.getParent().getParent().getInstanceName()

        out = out + TAB*2 +\
                instancename+"_"+portname+\
                " : " + port.getDir()
        if port.getMSBConnected()  < 1:
            out = out + " std_logic;"
        else:
            out = out + " std_logic_vector("+str(port.getMSBConnected())+" downto 0);"
        out = out + "\n"
    # Suppress the #!@ last semicolon
    out = out[:-2]
    out = out + "\n"+TAB + ");\n"
    out = out + TAB + "end component top_"+settings.active_project.getName()+";\n"
    return out

def beginarch():
    return "\nbegin\n\n"

def connectTop(portlist):
    out = TAB+"top : top_"+settings.active_project.getName()+"\n"
    out = out + TAB+"port map(\n"

    for port in portlist:
        portname = port.getName()
        interfacename = port.getParent().getName()
        instancename = port.getParent().getParent().getInstanceName()

        # sig declaration
        out = out + TAB*2 +\
                instancename+"_"+portname +\
                " => " +\
                instancename+"_"+portname +\
                ",\n"
    # Suppress the #!@ last comma
    out = out[:-2]
    out = out + "\n"+TAB + ");\n"
    return out

def clock(clockname):
   """ write clock process
   """
   clock = TAB+"clockp : process\n"+TAB+"begin\n"
   clock = clock+TAB*2+clockname+" <= '1';\n"
   clock = clock+TAB*2+"wait for HALF_PERIODE;\n"
   clock = clock+TAB*2+clockname+" <= '0';\n"
   clock = clock+TAB*2+"wait for HALF_PERIODE;\n"
   clock = clock+TAB+"end process clockp;\n"
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
    filename = settings.projectpath+SIMULATIONPATH+"/top_"+ settings.active_project.getName()+"_tb"+VHDLEXT
    clockportlist = settings.active_project.getListClockPorts()
    if len(clockportlist) == 0:
        raise Error("No external clock signal found",0)
    if len(clockportlist) != 1:
        display.msg("More than one external clock in design",1)
    clockport = clockportlist[0]
    clockname = clockport.getParent().getParent().getInstanceName()+"_"+clockport.getName()

    ###################
    # header
    out = header()
    out = out + include()
    out = out + entity()
    out = out + architecturehead()
    freq = clockport.getDestinationPort().getFreq()
    clockhalfperiode= (1000/float(freq))/2
    out = out + constant(clockhalfperiode)
    portlist =  settings.active_project.getPlatform().getConnectPortsList()
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
        display.msg("[WARNING] File exist, file renamed in "+filename+"old",0)
        sy.renameFile(filename,filename+"old")
    try:
        file = open(filename,"w")
    except IOError, e:
        raise e
    file.write(out)
    file.close()
    return filename

def generateMakefile():
    """ generate makefile for ghdl
    """
    # include file list:
    srclist =[]
    platform = settings.active_project.getPlatform()
    projectname = "top_"+settings.active_project.getName()
    srclist.append(".."+SYNTHESISPATH+"/top_"+settings.active_project.getName()+VHDLEXT)
    for component in settings.active_project.instances:
        if component.getNum() == "0":
            compdir = ".."+SYNTHESISPATH+"/"+component.getName()+"/"
            for hdlfile in component.getHdl_filesList():
                srclist.append(compdir+hdlfile.getFileName().split("/")[-1])

    librarylist = []
    for library in platform.getLibrariesList():
        srclist.append(library.getFileName())
        librarylist.append(library.getFileName())

    makefile = open(settings.path + TEMPLATESPATH+ "/"+MAKEFILETEMPLATE,"r").read()
    makefile = makefile.replace(r'$tpl:projectname$',projectname)
    makefile = makefile.replace(r'$tpl:files$'," ".join(srclist))
    makefile = makefile.replace(r'$tpl:library$'," ".join(librarylist))

    makefilename = settings.projectpath+SIMULATIONPATH+"/Makefile"
    file = open(makefilename,"w")
    file.write(makefile)
    file.close()
    return makefilename

