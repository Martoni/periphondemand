#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     TopVHDL.py
# Purpose:  
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  15/05/2008
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
__versionTime__ = "15/05/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import periphondemand.bin.define
from   periphondemand.bin.define import *
from   periphondemand.bin.code.topgen    import TopGen
from   periphondemand.bin.utils.settings import Settings
from   periphondemand.bin.utils.display  import Display
from   periphondemand.bin.utils.error    import Error
from   periphondemand.bin.utils          import wrappersystem as sy

import time
import datetime

TAB = "    "

settings = Settings()
display  = Display()

class TopVHDL(TopGen):
    """ Generate VHDL Top component
    """

    def __init__(self,project):
        TopGen.__init__(self,project) 

    def header(self):
        """ return vhdl header 
        """
        header = open(settings.path + TEMPLATESPATH+ "/"+HEADERTPL,"r").read() 
        header = header.replace("$tpl:author$",settings.author)
        header = header.replace("$tpl:date$",str(datetime.date.today()))
        header = header.replace("$tpl:filename$","Top_"\
                +settings.active_project.getName()+".vhd")
        header = header.replace(
                    "$tpl:abstract$",
                    settings.active_project.getDescription())
        return header

    def entity(self,entityname,portlist):
        """ return VHDL code for Top entity
        """
        out = "entity "+entityname+" is\n"
        out = out +"\n"+ TAB+ "port\n"+TAB+"(\n"
        for port in portlist:
            # TODO: display comment with instance-interface name
            portname = port.getName()
            interfacename = port.getParent().getName()
            instancename = port.getParent().getParent().getInstanceName()

            if port.isCompletelyConnected():
                # sig declaration
                out = out + TAB +\
                        instancename+"_"+portname+\
                        " : " + port.getDir()
                if port.getMSBConnected() < 1:
                    out = out + " std_logic;"
                else:
                    out = out + " std_logic_vector("+str(port.getMSBConnected())\
                            +" downto 0);"
                out = out + "\n"
            else:
                for pin in port.getListOfPin():
                    if pin.isConnected():
                        out = out + TAB + \
                            instancename+"_"+portname+"_pin"+str(pin.getNum())+\
                            " : "+port.getDir()+" std_logic;\n"
       # Suppress the #!@ last semicolon
        out = out[:-2]

        out = out+"\n" +TAB+");\nend entity "+entityname+";\n\n"
        return out

    def architectureHead(self,entityname):
        """
        """
        out = "architecture " + entityname+"_1 of "+entityname+" is\n"
        return out

    def architectureFoot(self,entityname):
        """
        """
        out = "\nend architecture "+entityname + "_1;\n"
        return out

    def declareComponents(self):
        """ Declare components
        """
        out =       TAB + "-------------------------\n"
        out = out + TAB + "-- declare components  --\n"
        out = out + TAB + "-------------------------\n"
        out = out + "\n"
        component = []
        for comp in self.project.getInstancesList():
            if comp.getName() != "platform":
                component.append(comp.getName())

        # if multiple instance of the same component
        component = set(component) 

        for compname in component:
            for component in self.project.getInstancesList():
                if component.getName() == compname: break;

            out = out +"\n"+ TAB + "component " +compname + "\n"
            if component.getFPGAGenericsList() != []:
                out = out + TAB*2 + "generic(\n"
                for generic in component.getFPGAGenericsList():
                    out = out + TAB*3\
                            +generic.getName()+" : "\
                            +generic.getType()+" := "\
                            +str(generic.getValue())\
                            +";\n"
                # suppress comma
                out = out[:-2]+"\n"
                out = out + TAB*2 + ");\n"

            out = out + TAB*2+"port (\n"
            for interface in component.getInterfacesList():
                out = out + TAB*3 + "-- " + interface.getName()+"\n"
                for port in interface.getPortsList():
                    out = out + TAB*3\
                            +port.getName()\
                            +"  : "\
                            +port.getDir()
                    if int(port.getSize()) == 1:
                        out = out + " std_logic;\n"
                    else:
                        out = out + " std_logic_vector("\
                                +str(int(port.getRealSize())-1)+\
                                " downto "+port.getMinPinNum()+");\n"
            # Suppress the #!@ last semicolon
            out = out[:-2] + "\n"
            out = out + TAB*2 + ");\n"
            out = out + TAB + "end component;\n"
        return out

    def declareSignals(self,componentslist,incomplete_external_ports_list):
        """ Declare signals ports
        """
        platformname = self.project.getPlatform().getInstanceName()
        out = TAB + "-------------------------\n"
        out = out+TAB + "-- Signals declaration\n"
        out = out +TAB + "-------------------------\n"
        for component in componentslist:
            if component.getName() != "platform":
                out = out +"\n" + TAB + "-- " +component.getInstanceName()+"\n"

                for interface in component.getInterfacesList():
                    out = out + TAB + "-- " + interface.getName()+"\n"

                    for port in interface.getPortsList():
                        
                        if len(port.getListOfPin())!=0:
                          if len(port.getListOfPin()[0].getConnections())!=0:
                            if port.getListOfPin()[0].getConnections()[0]["instance_dest"]\
                                                    !=platformname:
                                out=out+TAB+"signal "+component.getInstanceName()\
                                        +"_"+port.getName()\
                                        +" : "
                                if int(port.getSize()) == 1:
                                   out = out + " std_logic;\n"
                                else:
                                   out = out + " std_logic_vector("\
                                         +port.getMaxPinNum()\
                                         +" downto "\
                                         +port.getMinPinNum()\
                                         +");\n"
        out = out +"\n"+ TAB + "-- void pins\n"

        for port in incomplete_external_ports_list:
            portname = port.getName()
            interfacename = port.getParent().getName()
            instancename = port.getParent().getParent().getInstanceName()
            out = out +"\n"+TAB+"signal "+instancename+"_"+portname+": std_logic_vector("+\
                            str(int(port.getRealSize())-1)+" downto 0);\n" 
            for pinnum in range(int(port.getSize())):
                try:
                    if len(port.getPin(pinnum).getConnections()) == 0:
                        raise Error("",0)
                except Error:
                    out = out + TAB+ "signal "+instancename+"_"+portname+"_pin"+\
                            str(pinnum)+" : std_logic;\n"
        return out

    def declareInstance(self):
        out = TAB + "-------------------------\n"
        out = out + TAB + "-- declare instances\n"
        out = out + TAB + "-------------------------\n"
        for component in self.project.getInstancesList():
            if component.getName() != "platform":
                out = out + "\n" + TAB+component.getInstanceName()\
                        +" : "\
                        +component.getName()\
                        +"\n"
                if component.getFPGAGenericsList() != []:
                    out = out + TAB + "generic map (\n"
                    for generic in component.getFPGAGenericsList():
                        out = out + TAB*3\
                                +generic.getName()+" => "\
                                +str(generic.getValue())\
                                +",\n"
                    # suppress comma
                    out = out[:-2]+"\n"
                    out = out + TAB*2 + ")\n"
    
    
    
    
                out = out + TAB + "port map (\n"
                for interface in component.getInterfacesList():
                    out = out + TAB*3 + "-- " + interface.getName()+"\n"
                    for port in interface.getPortsList():
                        if len(port.getListOfPin())!=0:
                            out=out+TAB*3\
                                    +port.getName()\
                                    +" => "
                            out = out +component.getInstanceName()+"_"+port.getName()
                            out = out +",\n"
                        else:
                            if int(port.getSize()) == 1:
                                if port.getDir() == "out":
                                    out=out+TAB*3+port.getName()\
                                            +" => open,\n"
                                else:
                                    out=out+TAB*3+port.getName()\
                                            +" => '0',\n"
                            else:
                                if port.getDir() == "out":
                                    out=out+TAB*3+port.getName()\
                                            +" => open,\n"
                                else:
                                    out=out+TAB*3+port.getName()\
                                            +" => \""+sy.inttobin(0,int(port.getSize()))+"\",\n"


                # Suppress the #!@ last comma
                out = out[:-2] + "\n"
                out = out + TAB*3 + ");\n"
        out = out + "\n"
        return out

    def connectInstance(self,incomplete_external_ports_list):
        """ Connect instances
        """
        out =       TAB  + "---------------------------\n"
        out = out + TAB  + "-- instances connections --\n"
        out = out + TAB  + "---------------------------\n"

        platformname = self.project.getPlatform().getInstanceName()
        # connect incomplete_external_ports_list
        for port in incomplete_external_ports_list:
            portname = port.getName()
            interfacename = port.getParent().getName()
            instancename = port.getParent().getParent().getInstanceName()
            out = out+"\n"+TAB+"-- connect incomplete port\n"
            for pinnum in range(int(port.getSize())):
                out = out+TAB+instancename+"_"+portname+"_pin"+\
                        str(pinnum)+" <= "+instancename+"_"+portname+"("+\
                        str(pinnum)+");\n"
                try:
                    if len(port.getPin(pinnum).getConnections()) == 0:
                        raise Error("",0)
                except Error:
                    out = out+TAB+instancename+"_"+portname+"_pin"+\
                            str(pinnum)+" <= '0';\n"
            
        # connect all "in" ports pin
        for component in self.project.getInstancesList():
            if component.getInstanceName() != platformname:
                out = out + "\n"+TAB +"-- connect " +\
                        component.getInstanceName() + "\n"
                for interface in component.getInterfacesList():
                    out = out + TAB*2 + "-- " + interface.getName()+"\n"
                    for port in interface.getPortsList():
                        if port.getDir() == "in":
                            # Connect all pins port
                            if len(port.getListOfPin())!=0:
                                portdest = port.getDestinationPort()
                                if portdest != None and\
                                       (portdest.getSize() == port.getSize()):
                                    # If port is completely connected to one 
                                    # and only one other port 
                                    pin = port.getListOfPin()[0]
                                    connect =  pin.getConnections()[0]
                                    if connect["instance_dest"] != platformname:
                                        out = out + TAB*2\
                                            + component.getInstanceName()+"_"+port.getName()\
                                            + " <= "\
                                            + connect["instance_dest"]+"_"+connect["port_dest"]\
                                            + ";\n"
                                else:
                                    # If pins port are connected individualy to several other ports
                                    for pin in port.getListOfPin():
                                        # Connect pin individualy
                                        if pin.getNum() != None and len(pin.getConnections())!= 0:
                                            connect = pin.getConnections()[0]
                                            if connect["instance_dest"] != platformname:
                                                out = out + TAB*2\
                                                    + component.getInstanceName()+"_"+port.getName()
                                                if port.getSize() != "1": 
                                                    out = out + "("+ pin.getNum() +")"
                                                out = out + " <= "+ connect["instance_dest"]+\
                                                        "_"+connect["port_dest"]
                                                # is destination vector or simple net ?
                                                for comp in self.project.getInstancesList():
                                                    if comp.getInstanceName() == connect["instance_dest"]:
                                                        for inter in comp.getInterfacesList():
                                                            if inter.getName() == connect["interface_dest"]:
                                                                for port2 in inter.getPortsList():
                                                                    if port2.getSize() != "1":
                                                                        out = out +"("+\
                                                                                connect["pin_dest"]+")"
                                                out = out + ";\n"
                            # if port is void, connect '0' or open
                            else:
                                 display.msg("port "+ component.getInstanceName()\
                                                    +"."+interface.getName()+"."\
                                                    +port.getName()+" is void",1)
                    
        return out

    def architectureBegin(self):
        return "\nbegin\n"

