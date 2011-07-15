#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     candr.py
# Purpose:
# Authors:   Fabien Marteau <fabien.marteau@armadeus.com>
#            Gwenhael Goavec-Merou <gwenhael.goavec-merou@armadeus.com>
# Created:  29/04/2011
#-----------------------------------------------------------------------------
#  Copyright (2011)  Armadeus Systems
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

__doc__ = ""
__version__ = "1.0.0"
__versionTime__ = "29/04/2011"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com> and Gwenhael Goavec-Merou <gwenhael.goavec-merou@armadeus.com>"

import time
import datetime

from periphondemand.bin.define import *
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.error    import Error
from periphondemand.bin.utils          import wrappersystem as sy

from periphondemand.bin.core.component  import Component
from periphondemand.bin.core.port       import Port
from periphondemand.bin.core.interface  import Interface
from periphondemand.bin.core.hdl_file   import Hdl_file

settings = Settings()
TAB = "    "

def header(author,intercon):
    """ return vhdl header
    """
    header = open(settings.path + TEMPLATESPATH+"/"+HEADERTPL,"r").read()
    header = header.replace("$tpl:author$",__author__)
    header = header.replace("$tpl:date$",str(datetime.date.today()))
    header = header.replace("$tpl:filename$",intercon.getName()+VHDLEXT)
    header = header.replace("$tpl:abstract$",intercon.getDescription())
    return header

def entity(intercon):
    """ generate entity
    """
    entity = "Entity "+intercon.getName()+" is\n"
    entity = entity + TAB + "port\n" + TAB +"(\n"
    for interface in intercon.getInterfacesList():
        entity = entity+"\n"+TAB*2+"-- "+interface.getName()+" connection\n"
        for port in interface.getPortsList():
            entity = entity+TAB*2+"%-40s"%port.getName()+" : "+\
                    "%-5s"%port.getDir()
            if port.getSize() == "1":
                entity = entity + "std_logic;\n"
            else:
                entity = entity + "std_logic_vector("+port.getMaxPinNum()+\
                        " downto "+port.getMinPinNum() +");\n"
    # Suppress the #!@ last semicolon
    entity = entity[:-2]
    entity = entity + "\n"

    entity = entity + TAB + ");\n" + "end entity;\n\n"
    return entity

def architectureHead(masterinterface,intercon):
    """ Generate the head architecture
    """
    archead = "architecture "+intercon.getName()+"_1 of "\
               +intercon.getName()+" is\n"
    archead = archead + "begin\n"
    return archead

def connectClockandReset(masterinterface,intercon):
    """ Connect clock and reset
    """
    bus = masterinterface.getBus()
    masterinstance = masterinterface.getParent()
    masterinstancename = masterinstance.getInstanceName()
    masterinterfacename = masterinterface.getName()
    masterresetname = masterinstancename+"_"+masterinterface.getPortByType(bus.getSignalName("master","reset")).getName()
    masterclockname  = masterinstancename+"_"+masterinterface.getPortByType(bus.getSignalName("master","clock")).getName()

    out = "\n"+ TAB + "-- Clock and Reset connection\n"
    for slave in masterinterface.getSlavesList():
        slaveinstance = slave.getInstance()
        slaveinterface = slave.getInterface()
        slaveinstancename = slave.getInstanceName()
        slaveresetname = slaveinstancename+"_"+slaveinterface.getPortByType(bus.getSignalName("slave","reset")).getName()
        slaveclockname  = slaveinstancename+"_"+slaveinterface.getPortByType(bus.getSignalName("slave","clock")).getName()

        out=out+"\n"+TAB+"-- for "+slaveinstancename+"\n"
        #reset
        out=out+TAB+slaveresetname+" <= "+masterresetname+";\n"
        #clock
        out=out+TAB+slaveclockname+" <= "+ masterclockname+";\n"

    return out

def architectureFoot(intercon):
        """ Write foot architecture code
        """
        out = "\nend architecture "+intercon.getName()+"_1;\n"
        return out

def generateIntercon(masterinterface, intercon):
    """Generate intercon VHDL code for wishbone16 bus
    """
    masterinstance = masterinterface.getParent()
    project = masterinstance.getParent()

    ###########################
    #comment and header
    VHDLcode = header(settings.author,intercon)
    ###########################
    #entity
    VHDLcode = VHDLcode + entity(intercon)
    VHDLcode = VHDLcode + architectureHead(masterinterface, intercon)
    ###########################
    #Clock and Reset connection
    VHDLcode = VHDLcode + connectClockandReset(masterinterface,intercon)

    #Foot
    VHDLcode = VHDLcode + architectureFoot(intercon)

    ###########################
    # saving
    if not sy.dirExist(settings.projectpath +
                       COMPONENTSPATH+"/"+
                       intercon.getInstanceName()+"/"+HDLDIR):
        sy.makeDirectory(settings.projectpath+
                        COMPONENTSPATH+"/"+
                        intercon.getInstanceName()+"/"+HDLDIR)
    file = open(settings.projectpath +COMPONENTSPATH+"/"+
            intercon.getInstanceName()+
            "/"+HDLDIR+"/"+intercon.getInstanceName()+VHDLEXT,"w")
    file.write(VHDLcode)
    file.close()
    #hdl file path
    hdl = Hdl_file(intercon,
            filename=intercon.getInstanceName()+VHDLEXT,
            istop=1,scope="both")
    intercon.addHdl_file(hdl)
    return VHDLcode

