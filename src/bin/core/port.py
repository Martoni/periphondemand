#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Port.py
# Purpose:  
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/04/2008
#-----------------------------------------------------------------------------
#  Copyright (2008)  Armadeus Systems
#
# This program is free software; you an redistribute it and/or modify
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
__versionTime__ = "30/04/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"


from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils            import wrappersystem as sy
from periphondemand.bin.utils.error      import Error

from periphondemand.bin.core.pin import Pin

class Port(WrapperXml):
    """ Manage port
        attributes:
            pinlist -- list of pin
    """

    def __init__(self,parent,**keys):
        """ Init port,
            __init__(self,parent,name)
            __init__(self,parent,wxml)
        """
        if "name" in keys:
            self.__initname(keys["name"])
        elif "node" in keys:
            self.__initnode(keys["node"])
        else:
            raise Error("Keys not known in Port ",0)

        self.parent = parent
        self.pinlist = []
        for element in self.getNodeList("pin"):
            pin = Pin(self,node=element)
            self.pinlist.append(pin)

    def __initname(self,name):
        WrapperXml.__init__(self,nodename="port")
        self.setAttribute("name",name)
    def __initnode(self,node):
        WrapperXml.__init__(self,node=node)

    def getListOfPin(self):
        return self.pinlist

    def addPin(self,pin):
        """ Connect an object Pin in Port
            attributes:
                pin -- object Pin()
        """
        if pin.isAll() and len(self.pinlist)==1:
            if self.pinlist[0].isAll():
                return self.pinlist[0]
        else:
            for pintmp in self.pinlist:
                if pintmp.getNum() == pin.getNum():
                    return pintmp
        self.pinlist.append(pin)
        self.addNode(node=pin)
        return pin
        
    def delPin(self,arg):
        """ delete pin
            delPin(self,number)
            delPin(self,node)
        """
        if type(arg) == str or type(arg) == int:
            number = arg
            for pin in self.getListOfPin():
               if pin.getAttribute("num") == str(number):
                    self.delNode("pin","num",str(number))
                    self.pinlist.remove(pin)
        else:
            pin = arg
            self.pinlist.remove(pin)
            self.delNode(pin)
 
    def getPin(self,num):
        """ return pin with num
        """
        for pin in self.getListOfPin():
            if pin.getNum() == str(num):
                return pin
        raise Error("No pin with num "+str(num)+" in port "+str(self.getName()),0)
    def getType(self):
        return self.getAttribute("type")
    def setType(self,type):
        #TODO: check if type is known
        self.setAttribute("type",type)
    def getDir(self):
        return self.getAttribute("dir")
    def setDir(self,dir):
        if not dir.lower() in ["out","in","inout"]:
            raise Error("Direction wrong : "+str(dir))
        self.setAttribute("dir",dir)
    def getStandart(self):
        return self.getAttribute("standard")
    def setStandard(self,standard):
        self.setAttribute("standard",standard)
    def setDrive(self,drive):
        self.setAttribute("drive",drive)
    def getDrive(self):
        return self.getAttribute("drive")
    def getPosition(self):
        return self.getAttribute("position")
    def setPosition(self,position):
        self.setAttribute("position",position)
    def getFreq(self):
        freq = self.getAttribute("freq")
        if freq == None:
            raise Error("No frequency attribute for "+self.getName())
        return freq
    def isvariable(self):
        try:
            if self.getAttribute("variable_size") == "1":
                return 1
            else:
                return 0
        except AttributeError:
            return 0
    def getRealSize(self):
        """ if port is variable, return the size set by generic"""
        if self.isvariable():
            return str(int(self.getMaxPinNum())+1)
        else:
            return str(self.getSize())
    def getMaxPinNum(self):
        """ return the max num pin value
        """
        num="0"
        listofpin = self.getListOfPin()
        if listofpin == []:
            return str(int(self.getSize())-1)
        for pin in self.getListOfPin():
            if pin.getNum() == None:
                return str(int(self.getSize())-1)
            if int(pin.getNum()) > int(num):
                num = pin.getNum()
        return num
    def getMinPinNum(self):
        """ return the min pin value
        """
        num = self.getSize()
        listofpin = self.getListOfPin()
        if listofpin == []:
            return "0"
        for pin in self.getListOfPin():
           if pin.getNum() == None:
               return "0"
           if int(pin.getNum()) < int(num):
               num = pin.getNum()
        return num
    def checkConnection(self,portdest):
        """ Check the compatibility between the two pin with following rules:
        src\dest|  out in  inout lock clock
        ------------------------------------
        out     |   x   v    v     x    x
        in      |   v   v    v     x    v
        inout   |   v   v    v     x    x
        lock    |   v   v    v     x    x
        clock   |   x   v    x     x    x
        """
        listdir  = ["out","in","inout","lock","clock"]
        checktab = ((0,1,1,0,0),
                    (1,1,1,0,1),
                    (1,1,1,0,0),
                    (1,1,1,0,0),
                    (0,1,0,0,0))
        if checktab[listdir.index(self.getDir())][listdir.index(portdest.getDir())] == 0:
            raise Error("incompatible pin : " + self.getDir() + " => " + portdest.getDir(),0)

    def connectPort(self,port_dest):
        """ Connect all pins of a port on all pin on same size port dest
        """
        size = self.getSize()
        if size != port_dest.getSize():
            raise Error("The two ports have differents size")
        if self.getListOfPin() != []:
            raise Error("Port connection " + self.getName() + " is not void")
        if port_dest.getListOfPin() != []:
            raise Error("Port connection "+port_dest.getName()+" is not void")

        self.connectAllPin(port_dest)

    def connectPin(self,pinsourcenum,portdest,pindest):
        """ connect a pin to a destination instance
        """
        if (pinsourcenum is not None):
            # if non void port
            if self.getListOfPin() != []:
                for pin in self.getListOfPin():
                    if int(pin.getNum()) == int(pinsourcenum):
                        #check pin compatibility
                        self.checkConnection(portdest)
                        if pindest is not None:
                            pin.connectPin(portdest,pindest)
                        else:
                            pin.connectPin(portdest,"0")
                        return
            # check port size
            if int(self.getSize()) >= int(pinsourcenum):
                #check pin compatibility 
                self.checkConnection(portdest)
                pin = self.addPin(Pin(self,num=int(pinsourcenum)))
                if pindest is not None:
                    pin.connectPin(portdest,pindest)
                else:
                    pin.connectPin(portdest,"0")
            else:
                raise Error("Port size is too small",0)
        # if port size is just 1
        elif int(self.getSize())==1:
            #check pin compatibility 
            self.checkConnection(portdest)
            if self.getListOfPin() != []:
                pin = self.getListOfPin()[0]
            else:
                pin = self.addPin(Pin(self,num=0))
            if pindest is not None:
                pin.connectPin(portdest,pindest)
            else:
                pin.connectPin(portdest,"0")
            return
        else:
            raise Error("Pin source number must be entered",0)

    def connectAllPin(self,portdest):
        """ Connect all port pin to a destination instance
        """
        for pinnum in range(int(self.getSize())):
            self.connectPin(pinnum,portdest,pinnum)

    def deletePin(self,instancedest,interfacedest=None,portdest=None,
                       pindest=None,pinsource=None):
        """ delete a pin to a destination instance
        """
        if pinsource == None:
            pinlist = self.getListOfPin()
            for pin in pinlist:
                try:
                    pin.delConnection(instance_dest=instancedest)
                except Error:
                    pass
 
        else:
            if self.getListOfPin() != []:
                for pin in self.getListOfPin():
                    if int(pin.getNum()) == int(pinsource):
                        pin.delConnection(instancedest.getInstanceName(),
                                          interfacedest,portdest,pindest)
                        if pin.isEmpty():
                            self.delPin(pin)
                        return
            raise Error("Pin "+pinsource+" doesn't exists",0)

    def autoconnectPin(self):
        for pin in self.getListOfPin():
            pin.autoconnectPin()

    def getDestinationPort(self):
        """ get destination port connected to this port 
        if only one port connected
        """
        # check if port is connected to only one other port
        portdest = None
        for pin in self.getListOfPin():
            if len(pin.getConnectedPinList())!= 1:
                return None
            portconnect = pin.getConnectedPinList()[0].getParent()

            instanceconnect = \
                portconnect.getParent().getParent()
            if (portdest != None):
                if(portdest.getName() != portconnect.getName()\
                        or \
                   portdest.getParent().getParent().getInstanceName() \
                        != instanceconnect.getInstanceName()\
                        ):
                    return None
            else:
                portdest = portconnect
        return portdest
    
    def getMSBConnected(self):
        """Return the MSB that is connected to an another pin
        """
        num = -1
        for pin in self.getListOfPin():
            if pin.isConnected():
                if int(pin.getNum()) > num:
                    num = int(pin.getNum())
        return num
    
    def isCompletelyConnected(self):
        """ return 1 if all pin has connection"""
        if len(self.getListOfPin()) != int(self.getSize()):
            return 0
        for pin in self.getListOfPin():
            if not pin.isConnected():
                return 0
        return 1

