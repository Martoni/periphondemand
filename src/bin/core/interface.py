#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Interface.py
# Purpose:
#
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
#
# Created:  24/04/2008
# Licence:  GPLv3 or newer
# ----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
# ----------------------------------------------------------------------------
""" Class that manage interfaces"""

__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import os
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError

from periphondemand.bin.core.hdl_file import Hdl_file
from periphondemand.bin.core.generic import Generic
from periphondemand.bin.core.port import Port
from periphondemand.bin.core.register import Register
from periphondemand.bin.core.bus import Bus
from periphondemand.bin.core.slave import Slave
from periphondemand.bin.core.allocmem import AllocMem

settings = Settings()

#Class of interface supported:
INTERFACE_CLASS = ["master", "slave", "clk_rst", "gls", "intercon"]


class Interface(WrapperXml):
    """ Manage components interfaces
        attributes:
            registerbaseaddress -- register base address
            registerslist       -- list of register object
            portslist           -- list of port object
            bus                 -- bustype
    """

    def __init__(self, parent, **keys):
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
            raise PodError("Keys unknown in Interface", 0)

        self.parent = parent
        self.registerslist = []
        self.portslist = []
        self.slaveslist = []

        if self.getClass() == "master":
            self.allocMem = AllocMem(self)
        if self.getClass() == "slave":
            self.interfacemaster = None

        if self.getNode("slaves") is not None:
            for element in self.getSubNodeList("slaves", "slave"):
                    self.slaveslist.append(Slave(self, node=element))

        if self.getNode("registers") is not None:
            for element in self.getSubNodeList("registers", "register"):
                    self.registerslist.append(Register(self, node=element))

        if self.getNode("ports") is not None:
            for node in self.getSubNodeList("ports", "port"):
                self.portslist.append(Port(self, node=node))

        # set bus
        if self.getBusName() is not None:
            self.setBus(self.getBusName())

    def __initname(self, name):
        WrapperXml.__init__(self, nodename="interface")
        self.setAttribute("name", name)

    def __initnode(self, node):
        WrapperXml.__init__(self, node=node)

    def __initwxml(self, nodestring):
        WrapperXml.__init__(self, nodestring=nodestring)

    def setMaster(self, masterinterface):
        if self.getClass() != "slave":
            raise PodError("interface " + self.getName() + " must be slave", 0)
        elif masterinterface.getClass() != "master":
            raise PodError("interface " + masterinterface.getClass() +
                        " must be master", 0)
        self.interfacemaster = masterinterface

    def getMaster(self):
        """ Get the master bus if exist """
        if self.getClass() != "slave":
            raise PodError("Only slave interface could have a master", 0)
        if self.interfacemaster is None:
            raise PodError("Interface " + self.getName() +
                        " is not connected on a master", 0)
        return self.interfacemaster

    def getClass(self):
        """ Get the class interface """
        return self.getAttributeValue("class")

    def setClass(self, classname):
        """ Set the class interface """
        if not classname in INTERFACE_CLASS:
            raise PodError("classname " + classname + " unknown")
        self.setAttribute("class", classname)

    def getBase(self):
        try:
            base = self.getAttributeValue("base", "registers")
        except AttributeError:
            raise PodError("Base address register not set", 0)

        if base is None:
            raise PodError("Base address register not set", 0)
        else:
            return base

    def getBaseInt(self):
        try:
            return int(self.getBase(), 16)
        except PodError:
            return 0

    def getAddressSize(self):
        """ Return the size of address port
        """
        try:
            return int(
                self.getPortByType(
                  self.bus.getSignalName("slave", "address")).getSize())
        except PodError:
            return 0

    def getMemorySize(self):
        """ Get the memory size """
        return ((2 ** (self.getAddressSize())) * self.regStep())

    def setBase(self, baseoffset):
        """ Set the base offset for this interface
            baseoffset is an hexadecimal string
            the interface must be a slave bus
        """
        if self.getBusName() is None:
            raise PodError("Interface is not a bus", 1)
        if self.getClass() != "slave":
            raise PodError("Bus must be slave", 1)
        size = self.getMemorySize()
        if (int(baseoffset, 16) % size) != 0:
            raise PodError("Offset must be a multiple of " + hex(size), 1)
        self.setAttribute("base", baseoffset, "registers")

    def getBusName(self):
        """ Get the bus name """
        return self.getAttributeValue("bus")

    def getBus(self):
        """ Get the interface bus"""
        return self.bus

    def setBus(self, attribute):
        """ Set bus attribute"""
        self.bus = Bus(self, name=attribute)
        self.setAttribute("bus", attribute)

    def isBus(self):
        """ Test if this interface is a bus """
        try:
            self.getBus()
        except AttributeError:
            return False
        return True

    @property
    def ports(self):
        """ get the ports list of interface"""
        return self.portslist

    def getPort(self, portname):
        """ Get port by its name """
        for port in self.portslist:
            if port.getName() == portname:
                return port
        raise PodError("Port " + portname + " does not exists", 1)

    def getPortByType(self, porttypename):
        """ Get port using port type name as argument"""
        for port in self.portslist:
            if port.getType() == porttypename:
                return port
        raise PodError("No port with type " + str(porttypename), 1)

    def addPort(self, port):
        """ Adding a port """
        port.parent = self
        self.portslist.append(port)
        self.addSubNode(nodename="ports", subnode=port)

    def deletePin(self, instancedest, interfacedest=None, portdest=None,
                        pindest=None, portsource=None, pinsource=None):
        """ Delete all interface pins
        """
        if portsource is None:
            for port in self.ports:
                port.deletePin(instancedest=instancedest)
        else:
            port = self.getPort(portsource)
            port.deletePin(instancedest,
                           interfacedest,
                           portdest,
                           pindest,
                           pinsource)

    def getSlavesList(self):
        """ Get the slaves list of interface"""
        return self.slaveslist

    def delSlave(self, slave):
        """ Delet slave """
        self.allocMem.delInterfaceSlave(slave.getInterface())
        self.slaveslist.remove(slave)
        self.delSubNode("slaves",
                        "slave",
                        {"instancename": slave.getInstanceName(),
                         "interfacename": slave.getInterfaceName()})

    def del_bus(self, instanceslavename, interfaceslavename=None):
        """ delete slave bus connection
        """
        for slave in self.getSlavesList():
            if slave.getInstanceName() == instanceslavename:
                if interfaceslavename is None:
                    self.delSlave(slave)
                    return
                elif slave.getInterfaceName() == interfaceslavename:
                    self.delSlave(slave)
                    return
        raise PodError("Bus connection " + str(self.getName()) +
                    " -> " + str(instanceslavename) + "." +
                    str(interfaceslavename) + " doesn't exist", 0)

    def connect_interface(self, interface_dest):
        """ Connect an interface between two components
        """
        if len(interface_dest.ports) != len(self.ports):
            raise PodError(self.parent.getName() + "." + self.getName() +
                        " and " + interface_dest.parent.getName() +
                        "." + interface_dest.getName() +
                        "are not the same number of ports")
        for port in self.ports:
            if port.getType() is None:
                raise PodError(self.parent.getName() + "." +
                            self.getName() + "." +
                            port.getName() + " has no type")
            try:
                port_dst = interface_dest.getPortByType(port.getType())
            except PodError, e:
                raise PodError(interface_dest.parent.getName() + "." +
                            interface_dest.getName() + " have no " +
                            port.getType() + " port")
            if port_dst.getDir() == port.getDir():
                raise PodError("Ports " + self.parent.getName() + "." +
                            self.getName() + "." + port.getName() + " and " +
                            interface_dest.parent.getName() + "." +
                            interface_dest.getName() + "." +
                            port_dst.getName() + " are the same direction")
            if port_dst.getDir() == "in" and port_dst.isVoid() is not True:
                raise PodError("Ports " + interface_dest.parent.getName() +
                            "." + interface_dest.getName() + "." +
                            port_dst.getName() + " is already connected")
            if port.getDir() == "in" and port.isVoid() is not True:
                raise PodError("Ports " + self.parent.getName() +
                            "." + self.getName() +
                            "." + port.getName() +
                            " is already connected")

        for port in self.ports:
            port_dst = interface_dest.getPortByType(port.getType())
            port.connect_port(port_dst)

    def connect_bus(self, instanceslave, interfaceslavename):
        """ Connect an interfaceslave to an interface bus master
        """
        interfaceslave = instanceslave.getInterface(interfaceslavename)
        for slave in self.getSlavesList():
            if slave.getInstanceName() == instanceslave.getInstanceName()\
                    and slave.getInterfaceName() == interfaceslavename:
                        raise PodError("Bus connection for " +
                                    slave.getInstanceName() + "." +
                                    slave.getInterfaceName() +
                                    " already exists", 1)
        if self.getBusName() is None:
            raise PodError("Interface " + self.getName() + " must be a bus ", 0)
        if interfaceslave.getBusName() is None:
            raise PodError("Interface " + interfaceslave.getName() +
                        " must be a bus ", 0)
        if self.getBusName() != interfaceslave.getBusName():
            raise PodError("Can't connect " + self.getBusName() +
                        " on " + interfaceslave.getBusName(), 1)
        if self.getClass() != "master":
            raise PodError(self.getName() + " is not a master", 0)
        if interfaceslave.getBusName() is None:
            raise PodError(instanceslave.getInstanceName() +
                        "." + interfaceslave.getName() + " is not a bus", 1)
        if interfaceslave.getClass() != "slave":
            raise PodError(instanceslave.getInstanceName() +
                        "." + interfaceslave.getName() + " is not a slave", 1)
        self.addSubNode(nodename="slaves",
                        subnodename="slave",
                        attributedict={
                        "instancename": instanceslave.getInstanceName(),
                        "interfacename": interfaceslavename
                        })
        self.slaveslist.append(Slave(self,
                               instancename=instanceslave.getInstanceName(),
                               interfacename=interfaceslavename))
        self.allocMem.addInterfaceSlave(interfaceslave)
        interfaceslave.setMaster(self)
        interfaceslave.setID(self.allocMem.getID())
        instanceslave.getGeneric(genericname="id").setValue(
                                    str(interfaceslave.getID()))

    def setID(self, unique_id):
        """ Set the Identifiant number"""
        self.setAttribute("unique_id", str(unique_id))

    def getID(self):
        """ Get the Identifiant number"""
        try:
            return self.getAttributeValue("unique_id")
        except PodError:
            return None

    def autoconnectPin(self):
        """ autoconnect pin """
        for port in self.ports:
            port.autoconnectPin()

    def connectClkDomain(self, instancedestname, interfacedestname):
        """ Connect clock domain
        """
        for slave in self.getSlavesList():
            if slave.getInstanceName() == instancedestname\
                    and slave.getInterfaceName() == interfacedestname:
                        raise PodError("Clock connection " + instancedestname +
                                    "." + interfacedestname + " exists", 1)

        self.addSubNode(nodename="slaves", subnodename="slave",
                        attributedict={"instancename": instancedestname,
                                       "interfacename": interfacedestname})
        self.slaveslist.append(Slave(self,
                                     instancename=instancedestname,
                                     interfacename=interfacedestname))

    def getRegister(self, registername):
        for register in self.getRegisterList():
            if register.getName() == registername:
                return register
        raise PodError("No register with name " + registername, 0)

    def getRegisterList(self):
        return self.registerslist

    def getRegisterMap(self):
        """ Return the memory mapping for slave interface
        """
        if len(self.registerslist) != 0:
            listreg = []
            # sort registers dict by offset order
            self.registerslist.sort(lambda x, y: cmp(int(x.getOffset(), 16),
                                    int(y.getOffset(), 16)))
            #display each register
            for register in self.registerslist:
                listreg.append({"offset": int(register.getOffset(), 16)
                                         * self.regStep() +
                                         int(self.getBase(), 16),
                               "name": register.getName()})
            return listreg
        else:
            return [{"offset": int(self.getBase(), 16),
                     "name": self.getName()}]

    def regStep(self):
        """ Step between two register
        """
        return int(self.bus.getDataSize()) / 8

    def getSysconInstance(self):
        """ Return syscon instance that drive master interface
        """
        for instance in self.parent.parent.instances:
            for interface in instance.getInterfacesList():
                if interface.getClass() == "clk_rst":
                    for slave in interface.getSlavesList():
                        if slave.getInstanceName() ==\
                            self.parent.getInstanceName() and\
                                    slave.getInterfaceName() == self.getName():
                            return instance
        raise PodError("No syscon for interface " + self.getName() +
                    " of instance " + self.parent.getInstanceName(), 0)

    def addRegister(self, register_name):
        if self.getBusName() is None:
            raise PodError("Interface must be a bus")
        elif self.getClass() != "slave":
            raise PodError("Bus must be a slave")
        #TODO: check if enough space in memory mapping to add register
        register = Register(self, register_name=register_name)
        self.registerslist.append(register)
        self.addSubNode(nodename="registers", subnode=register)

    def delRegister(self, register_name):
        #TODO
        pass
