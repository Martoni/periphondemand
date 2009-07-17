#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Interface.py
# Purpose:  
#
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
#
# Created:  24/04/2008
# Licence:  GPLv3 or newer
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

__doc__ = ""
__version__ = "1.0.0"
__versionTime__ = "24/04/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import os
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings   import Settings
from periphondemand.bin.utils.error      import Error


from periphondemand.bin.core.hdl_file  import Hdl_file
from periphondemand.bin.core.generic   import Generic
from periphondemand.bin.core.port      import Port
from periphondemand.bin.core.register  import Register
from periphondemand.bin.core.bus       import Bus
from periphondemand.bin.core.slave     import Slave
from periphondemand.bin.core.allocmem  import AllocMem

settings = Settings()

#Class of interface supported:
INTERFACE_CLASS = ["master","slave","clk_rst","gls","intercon"]

class Interface(WrapperXml):
    """ Manage components interfaces
        attributes:
            registerbaseaddress -- register base address
            registerslist       -- list of register object
            portslist           -- list of port object
            bus                 -- bustype
    """

    def __init__(self,parent,**keys):
        """ Create interface object
            if node is a node or name.
            __init__(self,parent,name)
            __init__(self,parent,node)
            __init__(self,parent,nodestring)
        """

        if "name" in keys:
            self.__initname(keys["name"])
        elif "node" in keys:
            self.__initnode(keys["node"])
        elif "wxml" in keys:
            self.__initwxml(keys["wxml"])
        else:
            raise Error("Keys unknown in Interface",0)

        self.parent = parent
        self.registerslist = []
        self.portslist     = []
        self.slaveslist    = []
        self.id = None # each slave bus has unique identifiant num

        if self.getClass()=="master":
            self.allocMem = AllocMem(self)
        if self.getClass()=="slave":
            self.interfacemaster = None

        if self.getNode("slaves") != None:
            for element in self.getSubNodeList("slaves","slave"):
                    self.slaveslist.append(Slave(self,node=element))

        if self.getNode("registers") != None:
            for element in self.getSubNodeList("registers","register"):
                    self.registerslist.append(Register(self,node=element))

        if self.getNode("ports") != None:
            for node in self.getSubNodeList("ports","port"):
                self.portslist.append(Port(self,node=node))

        # set bus
        if self.getBusName() != None:
            self.setBus(self.getBusName())


    def __initname(self,name):
        WrapperXml.__init__(self,nodename="interface")
        self.setAttribute("name",name)
    def __initnode(self,node):
        WrapperXml.__init__(self,node=node)
    def __initwxml(self,nodestring):
        WrapperXml.__init__(self,nodestring=nodestring)

    def setMaster(self,masterinterface):
        if self.getClass() != "slave":
            raise Error("interface "+self.getName()+" must be slave",0)
        elif masterinterface.getClass() != "master":
            raise Error("interface "+masterinterface.getClass()+" must be master",0)
        self.interfacemaster = masterinterface

    def getMaster(self):
        if self.getClass() != "slave":
            raise Error("Only slave interface could have a master",0)
        if self.interfacemaster==None:
            raise Error("Interface "+self.getName()+" is not connected on a master",0)
        return self.interfacemaster

    def getClass(self):
        return self.getAttribute("class")
    def setClass(self,classname):
        if not classname in INTERFACE_CLASS:
            raise Error("classname "+classname+" unknown")
        self.setAttribute("class",classname)
    def getClockAndResetName(self):
        value = self.getAttribute("clockandreset")
        if value == None:
            raise Error("No clock and reset name in '"+self.getName()+"' interface")
        return value
    def getClockAndResetInterface(self):
        print "TODO getclockandresetinterface"
    def setClockAndReset(self,interfacename):
        #TODO: check if interfacename exist
        self.setAttribute("clockandreset",interfacename)
    def getBase(self):
        try:
           base = self.getAttribute("base","registers")
        except AttributeError:
            raise Error("Base address register not set",0)

        if base == None:
            raise Error("Base address register not set",0)
        else:
            return base
    
    def getBaseInt(self):
        try:
            return int(self.getBase(),16)
        except Error,e:
            return 0

    def getAddressSize(self):
        """ Return the size of address port
        """
        try:
            return int(
                self.getPortByType(
                  self.bus.getSignalName("slave","address")).getSize())
        except Error:
            return 0

    def getMemorySize(self):
        return ((2**(self.getAddressSize()))*self.regStep())

    def setBase(self,baseoffset):
        """ Set the base offset for this interface
            baseoffset is an hexadecimal string
            the interface must be a slave bus
        """
        if self.getBusName() == None:
            raise Error("Interface is not a bus",1)
        if self.getClass() != "slave":
            raise Error("Bus must be slave",1)
        size = self.getMemorySize()
        if int(baseoffset,16)%(size)!=0:
            raise Error("Offset must be a multiple of " + hex(size),1)
        self.setAttribute("base",baseoffset,"registers")

    def getBusName(self):
        return self.getAttribute("bus")

    def getBus(self):
        return self.bus

    def setBus(self,attribute):
        self.bus = Bus(self,name=attribute)
        self.setAttribute("bus",attribute)

    def getPortsList(self):
        return self.portslist

    def getPort(self,portname):
        for port in self.portslist:
            if port.getName() == portname:
                return port
        raise Error("Port "+portname+" does not exists",1)

    def getPortByType(self,porttypename):
        for port in self.portslist:
            if port.getType() == porttypename:
                return port
        raise Error("Not port with type "+ str(porttypename),1)

    def addPort(self,port):
        port.setParent(self)
        self.portslist.append(port)
        self.addSubNode(nodename="ports",subnode=port)

    def deletePin(self,instancedest,interfacedest=None,portdest=None,\
                       pindest=None,portsource=None,pinsource=None):
        """ Delete all interface pins
        """
        if portsource==None:
            for port in self.getPortsList():
                port.deletePin(instancedest=instancedest)
        else:
            port = self.getPort(portsource)
            port.deletePin(instancedest,
                           interfacedest,
                           portdest,
                           pindest,
                           pinsource)

    def getSlavesList(self):
        return self.slaveslist

    def delSlave(self,slave):
        self.allocMem.delInterfaceSlave(slave.getInterface())
        self.slaveslist.remove(slave)
        self.delSubNode("slaves","slave",{"instancename":slave.getInstanceName(),\
                                          "interfacename":slave.getInterfaceName()})

    def deleteBus(self,instanceslavename,interfaceslavename=None):
        """ delete slave bus connection
        """
        for slave in self.getSlavesList():
            if slave.getInstanceName() == instanceslavename:
                if interfaceslavename==None:
                    self.delSlave(slave)
                    return
                elif slave.getInterfaceName() == interfaceslavename:
                    self.delSlave(slave)
                    return
        raise Error("Bus connection "+str(self.getName())+" -> "+str(instanceslavename)+"."+str(interfaceslavename) +" doesn't exist",0)

    def connectBus(self,instanceslave,interfaceslavename):
        """ Connect an interfaceslave to an interface bus master
        """
        interfaceslave = instanceslave.getInterface(interfaceslavename)
        for slave in self.getSlavesList():
            if slave.getInstanceName()==instanceslave.getInstanceName()\
                    and slave.getInterfaceName()==interfaceslavename:
                        raise Error("Bus connection for "+\
                                slave.getInstanceName()+"."+\
                                slave.getInterfaceName()+\
                                " already exists",1)
        if self.getBusName() == None:
            raise Error("Interface "+self.getName()+" must be a bus ",0)
        if interfaceslave.getBusName() == None:
            raise Error("Interface "+interfaceslave.getName()+" must be a bus ",0)
        if self.getBusName() != interfaceslave.getBusName():
            raise Error("Can't connect "+self.getBusName()+\
                        " on "+interfaceslave.getBusName(),1)
        if self.getClass() != "master":
            raise Error(self.getName() + " is not a master",0)
        if interfaceslave.getBusName() == None :
            raise Error(instanceslave.getInstanceName()+\
                    "."+interfaceslave.getName()+" is not a bus",1)
        if interfaceslave.getClass() != "slave":
            raise Error(instanceslave.getInstanceName()+\
                    "."+interfaceslave.getName()+" is not a slave",1)
        self.addSubNode(nodename="slaves",\
                        subnodename="slave",\
                        attributedict=
                        {"instancename":instanceslave.getInstanceName(),\
                         "interfacename":interfaceslavename})
        self.slaveslist.append(Slave(self,\
                             instancename=instanceslave.getInstanceName(),\
                             interfacename=interfaceslavename))
        self.allocMem.addInterfaceSlave(interfaceslave)
        interfaceslave.setMaster(self)
        interfaceslave.setID(self.allocMem.getID())
        instanceslave.getGeneric(genericname="id").setValue(
                        str(interfaceslave.getID()))
   
    def setID(self,id):
        self.id = id
    def getID(self):
        return self.id

    def autoconnectPin(self):
        for port in self.getPortsList():
            port.autoconnectPin()

    def connectClkDomain(self,instancedestname,interfacedestname):
        """ Connect clock domain
        """
        for slave in self.getSlavesList():
           if slave.getInstanceName()==instancedestname \
                   and slave.getInterfaceName()==interfacedestname:

                       raise Error("Clock connection "+instancedestname+"."+interfacedestname+" exists",1)
       
        self.addSubNode(nodename="slaves",subnodename="slave",
                        attributedict={"instancename":instancedestname,
                                       "interfacename":interfacedestname})
        self.slaveslist.append(Slave(self,\
                                     instancename=instancedestname,\
                                     interfacename=interfacedestname))

    def getRegister(self,registername):
        for register in self.getRegisterList():
            if register.getName() == registername:
                return register
        raise Error("No register with name "+registername,0)

    def getRegisterList(self):
        return self.registerslist

    def getRegisterMap(self):
        """ Return the memory mapping for slave interface
        """
        if len(self.registerslist)!=0:
            listreg = []
            # sort registers dict by offset order
            self.registerslist.sort(lambda x, y:cmp(int(x.getOffset(),16),
                                    int(y.getOffset(),16)))
            #display each register 
            for register in self.registerslist:
               listreg.append({"offset":int(register.getOffset(),16)*self.regStep()+\
                                 int(self.getBase(),16),\
                            "name":register.getName()})
            return listreg
        else:
            return [{"offset":int(self.getBase(),16),"name":self.getName()}]

    def regStep(self):
        """ Step between two register
        """
        return int(self.bus.getDataSize())/8

    def getSysconInstance(self):
        """ Return syscon instance that drive master interface
        """
        for instance in self.getParent().getParent().getInstancesList():
            for interface in instance.getInterfacesList():
                if interface.getClass() == "clk_rst":
                    for slave in interface.getSlavesList():
                        if slave.getInstanceName() == self.getParent().getInstanceName() and slave.getInterfaceName() == self.getName():
                            return instance
        raise Error("No syscon for interface "+self.getName()+" of instance "+self.getParent().getInstanceName(),0)

    def addRegister(self,register_name):
        if self.getBusName() == None:
            raise Error("Interface must be a bus")
        elif self.getClass() != "slave":
            raise Error("Bus must be a slave")
        #TODO: check if enough space in memory mapping to add register
        register = Register(self,register_name=register_name)
        self.registerslist.append(register)
        self.addSubNode(nodename="registers",subnode=register)

    def delRegister(self,register_name):
        #TODO
        pass
