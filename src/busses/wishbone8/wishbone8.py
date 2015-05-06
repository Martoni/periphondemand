#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     wishbone8.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  13/05/2008
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
# Revision list :
#
# Date       By        Changes
#
# ----------------------------------------------------------------------------

__doc__ = ""
__version__ = "1.0.0"
__versionTime__ = "20/07/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

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
    header = header.replace("$tpl:author$",author)
    header = header.replace("$tpl:date$",str(datetime.date.today()))
    header = header.replace("$tpl:filename$",intercon.getName()+VHDLEXT)
    header = header.replace("$tpl:abstract$",intercon.getDescription())
    return header

def entity(intercon):
    """ generate entity
    """
    entity = "Entity " + intercon.getName() + " is\n"
    entity = entity + TAB + "port\n" + TAB +"(\n"
    for interface in intercon.getInterfacesList():
        entity = entity + "\n" + TAB * 2 + "-- " +\
                 interface.getName() + " connection\n"
        for port in interface.ports:
            entity=entity + TAB * 2 +"%-40s" % port.getName() +\
                    " : " + "%-5s" % port.getDir()
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
    for slave in masterinterface.getSlavesList():
        archead=archead+TAB+"signal "+"%-40s"%(slave.getInstanceName()\
                +"_"+slave.getInterfaceName()+"_cs")+" : std_logic := '0' ;\n"
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
    masterclockname = masterinstancename+"_"+masterinterface.getPortByType(bus.getSignalName("master","clock")).getName()
    out = "\n"+ TAB + "-- Clock and Reset connection\n"

    for slave in masterinterface.getSlavesList():
        slaveinstance = slave.get_instance()
        slaveinterface = slave.getInterface()
        slaveinstancename = slave.getInstanceName()
        slaveresetname = slaveinstancename+"_"+slaveinterface.getPortByType(bus.getSignalName("slave","reset")).getName()
        slaveclockname = slaveinstancename+"_"+slaveinterface.getPortByType(bus.getSignalName("slave","clock")).getName()
        #reset
        out=out+TAB+slaveresetname+" <= "+masterresetname+";\n"
        #clock
        out=out+TAB+slaveclockname+" <= "+masterclockname+";\n"

    return out

def addressdecoding(masterinterface,masterinstancename,intercon):
    """ generate VHDL for address decoding
    """
    bus = masterinterface.getBus()
    masterinstance = masterinterface.getParent()
    masterinstancename = masterinstance.getInstanceName()
    rst_name = masterinstancename+"_"+masterinterface.getPortByType(bus.getSignalName("master","reset")).getName()
    clk_name = masterinstancename+"_"+masterinterface.getPortByType(bus.getSignalName("master","clock")).getName()
    masteraddressname = masterinstance.getInstanceName()+"_"+\
                      masterinterface.getPortByType(
                              bus.getSignalName("master","address")).getName()
    masterstrobename = masterinstancename+"_"+\
            masterinterface.getPortByType(
                    bus.getSignalName("master","strobe")).getName()
    mastersizeaddr = masterinterface.getAddressSize()

    out = TAB +       "-----------------------\n"
    out = out + TAB + "-- Address decoding  --\n"
    out = out + TAB + "-----------------------\n"
    for slave in masterinterface.getSlavesList():
        slaveinstance  = slave.get_instance()
        slaveinterface = slave.getInterface()
        slavesizeaddr  = slave.getInterface().getAddressSize()
        slavebase_address   = slaveinterface.getBaseInt()
        if slavesizeaddr > 0 :
            slaveaddressport = slave.getInterface().getPortByType(
                    bus.getSignalName("slave","address"))
            slavename_addr = slaveinstance.getInstanceName() +\
                    "_" + slaveaddressport.getName()
        if slavesizeaddr == 1:
            out=out+TAB+slavename_addr+" <= "+masteraddressname+"(0);\n"
        elif slavesizeaddr > 1:
            out=out+TAB+slavename_addr+" <= "+masteraddressname\
                    +"("+str(slavesizeaddr-1) +" downto 0);\n"
    out = out + "\n"


    out = out+TAB+"decodeproc : process("+clk_name+\
            ","+rst_name+","+masteraddressname+")\n"
    out = out+TAB+"begin\n"

    #initialize
    out = out+TAB*2+"if "+rst_name+"='1' then\n"
    for slave in masterinterface.getSlavesList():
        slaveinstance = slave.get_instance()
        slaveinterface = slave.getInterface()
        chipselectname = slaveinstance.getInstanceName()+\
                "_"+slaveinterface.getName()+"_cs"
        out = out+TAB*3+chipselectname+" <= '0';\n"
    out = out+TAB*2+"elsif rising_edge("+clk_name+") then\n"

    for slave in masterinterface.getSlavesList():
        slaveinstance  = slave.get_instance()
        slaveinterface = slave.getInterface()
        chipselectname = slaveinstance.getInstanceName()+\
                "_"+slaveinterface.getName()+"_cs"
        slavesizeaddr  = slave.getInterface().getAddressSize()
        slavebase_address   = slaveinterface.getBaseInt()
        if slavesizeaddr > 0 :
            slaveaddressport = slave.getInterface().getPortByType(
                    bus.getSignalName("slave","address"))
            slavename_addr = slaveinstance.getInstanceName() +\
                    "_" + slaveaddressport.getName()

        out=out+"\n"
        out=out+TAB*3+"if "+masteraddressname+"("\
                +str(int(mastersizeaddr-1))\
                +" downto "+str(slavesizeaddr)+')="'\
                +sy.inttobin(slavebase_address,
                        int(mastersizeaddr))[:-(slavesizeaddr)]+'"'\
                            +" and "+masterstrobename+"='1' then\n"

        out=out+TAB*4+chipselectname+" <= '1';\n"
        out=out+TAB*3+"else\n"
        out=out+TAB*4+chipselectname+" <= '0';\n"
        out=out+TAB*3+"end if;\n"

    out=out+"\n"+TAB*2+"end if;\n"+TAB+"end process decodeproc;\n\n"
    return out

def controlslave(masterinterface,intercon):
    """ Connect controls signals for slaves
    """

    bus = masterinterface.getBus()
    masterinstance = masterinterface.getParent()
    masterinstancename = masterinstance.getInstanceName()
    masterinterfacename = masterinterface.getName()
    masterstrobename = masterinstancename+"_"+\
            masterinterface.getPortByType(
                    bus.getSignalName("master","strobe")).getName()
    mastercyclename  = masterinstancename+"_"+\
                    masterinterface.getPortByType(
                            bus.getSignalName("master","cycle")).getName()

    out =TAB+         "-----------------------------\n"
    out = out + TAB + "-- Control signals to slave\n"
    out = out + TAB + "-----------------------------\n"

    for slave in masterinterface.getSlavesList():
        slaveinstance = slave.get_instance()
        slaveinterface = slave.getInterface()
        slaveinstancename = slave.getInstanceName()
        slavestrobename = slaveinstancename+"_"+\
                slaveinterface.getPortByType(
                        bus.getSignalName("slave","strobe")).getName()
        slavecyclename  = slaveinstancename+"_"+\
                        slaveinterface.getPortByType(
                                bus.getSignalName("slave","cycle")).getName()

        chipselectname = slaveinstancename+"_"+slaveinterface.getName()+"_cs"

        out=out+"\n"+TAB+"-- for "+slaveinstancename+"\n"
        #strobe
        out=out+TAB\
                +slavestrobename\
                +" <= ("\
                +masterstrobename\
                +" and " \
                +chipselectname +" );"\
                +"\n"
        #cycle
        out=out+TAB\
                +slavecyclename\
                +" <= ("\
                + mastercyclename\
                +" and " \
                +chipselectname+" );"\
                +"\n"

        #write connection if read/write, read or write
        try:
            datainname = slaveinstancename +"_"+\
                    slaveinterface.getPortByType(
                            bus.getSignalName("slave","datain")).getName()
        except Error,e:
            datainname = None

        try:
            dataoutname = slaveinstancename+"_"+\
                    slaveinterface.getPortByType(
                            bus.getSignalName("slave","dataout")).getName()
        except Error,e:
            dataoutname = None

        if datainname and dataoutname:
            #write
            out=out+TAB\
                    +slaveinstancename+"_"\
                    +slaveinterface.getPortByType(
                            bus.getSignalName("slave","write")).getName()+\
                    " <= ("+\
                    masterinstancename+"_"+\
                    masterinterface.getPortByType(
                              bus.getSignalName("master","write")).getName()+\
                    " and "+\
                    chipselectname +" );"+\
                    "\n"
        elif datainname:
            #write
            out=out+TAB+\
                    slaveinstancename+"_"+\
                    slaveinterface.getPortByType(
                            bus.getSignalName("slave","write")).getName()+\
                    " <= '1';\n"
        elif dataoutname:
            #write
            out=out+TAB+\
                    slaveinstancename+"_"+\
                    slaveinterface.getPortByType(
                            bus.getSignalName("slave","write")).getName()+\
                    " <= '0';\n"
        if datainname:
            out=out+TAB+\
                slaveinstancename+"_"+\
                slaveinterface.getPortByType(
                    bus.getSignalName("slave","datain")).getName()+\
                " <= "+\
                masterinstancename+"_"+\
                masterinterface.getPortByType(
                      bus.getSignalName("master","dataout")).getName()+\
                 " when ("+\
                 masterinstancename+"_"+\
                 masterinterface.getPortByType(
                              bus.getSignalName("master","write")).getName()+\
                 " and "+\
                 chipselectname+" ) = '1' else (others => '0');"+\
                 "\n"
    return out

def controlmaster(masterinterface,intercon):
    bus = masterinterface.getBus()
    masterinstance = masterinterface.getParent()
    masterinstancename = masterinstance.getInstanceName()
    masterinterfacename = masterinterface.getName()

    out = "\n\n"+TAB  + "-------------------------------\n"
    out = out   + TAB + "-- Control signal for master --\n"
    out = out   + TAB + "-------------------------------\n"

    out = out + TAB + masterinstance.getInstanceName() + "_"
    out = out +masterinterface.getPortByType(
            bus.getSignalName("master","datain")).getName()
    out = out + " <= "
    #READDATA
    for slave in masterinterface.getSlavesList():
        slaveinstance = slave.get_instance()
        slaveinterface = slave.getInterface()
        slaveinterfacename = slaveinterface.getName()
        slaveinstancename = slave.getInstanceName()
        try:
            dataoutname = slaveinstancename+"_"+\
                    slaveinterface.getPortByType(
                            bus.getSignalName("slave","dataout")).getName()
            out = out +" "+dataoutname
            out = out + " when "+slaveinstancename+"_"+\
                    slaveinterfacename+"_cs='1' else\n"
            out = out +TAB*9+"  "
        except Error,e:
            pass
    out = out + " (others => '0');\n"

    #ACK
    out = out + TAB + masterinstance.getInstanceName() + "_"
    out = out + masterinterface.getPortByType(
            bus.getSignalName("master","ack")).getName()
    out = out + " <= "
    count = 0
    if masterinterface.getSlavesList() :
        for slave in masterinterface.getSlavesList():
            slaveinstance = slave.get_instance()
            slaveinterface = slave.getInterface()
            slaveinterfacename = slaveinterface.getName()
            slaveinstancename = slave.getInstanceName()
            if count == 0:
                out=out+" "
                count = 1
            else:
                out = out+"\n"+TAB*9+"or \n"
                out = out+TAB*8
            out = out +"("+slaveinstancename+"_"\
                +slaveinterface.getPortByType(
                        bus.getSignalName("slave","ack")).getName()\
                                +" and "\
                                +slaveinstancename+"_"+slaveinterfacename+"_cs)"
    else: 
        out = out + "'0'"
    out = out+";\n"
    return out

def architectureFoot(intercon):
    """ Write foot architecture code
    """
    out = "\nend architecture "+intercon.getName()+"_1;\n"
    return out

def generate_intercon(masterinterface,intercon):
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
    VHDLcode = VHDLcode + architectureHead(masterinterface,intercon)

    listslave = masterinterface.getSlavesList()
    listinterfacesyscon = []
    for slaveinstance in [slave.get_instance() for slave in listslave]:
        listinterfacesyscon.append(slaveinstance.getSysconInterface())
    listinterfacesyscon.append(masterinstance.getSysconInterface())

    ###########################
    #Clock and Reset connection
    VHDLcode = VHDLcode + connectClockandReset(masterinterface,intercon)


    ###########################
    #address decoding
    VHDLcode = VHDLcode + addressdecoding(masterinterface,masterinstance,intercon)

    ###########################
    #controls slaves
    VHDLcode = VHDLcode + controlslave(masterinterface,intercon)
    ###########################
    #controls master
    VHDLcode = VHDLcode+controlmaster(masterinterface,intercon)
    ###########################
    #Foot
    VHDLcode = VHDLcode + architectureFoot(intercon)

    ###########################
    # saving
    if not sy.dirExist(settings.projectpath +COMPONENTSPATH+"/"+\
            intercon.getInstanceName()+"/"+HDLDIR):
        sy.makeDirectory(settings.projectpath +COMPONENTSPATH+"/"+\
                intercon.getInstanceName()+"/"+HDLDIR)
    file = open(settings.projectpath +COMPONENTSPATH+"/"+\
            intercon.getInstanceName()+"/"+HDLDIR+"/"+\
            intercon.getInstanceName()+VHDLEXT,"w")
    file.write(VHDLcode)
    file.close()
    #hdl file path
    hdl = Hdl_file(intercon,
            filename=intercon.getInstanceName()+\
                    VHDLEXT,istop=1,scope="both")
    intercon.addHdl_file(hdl)
    return VHDLcode

