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

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.poderror import PodError

from periphondemand.bin.core.port import Port
from periphondemand.bin.core.register import Register
from periphondemand.bin.core.bus import Bus
from periphondemand.bin.core.slave import Slave
from periphondemand.bin.core.allocmem import AllocMem

# Class of interface supported:
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

        self.parent = parent

        if "name" in keys:
            WrapperXml.__init__(self, nodename="interface")
            self.name = keys["name"]
        elif "node" in keys:
            WrapperXml.__init__(self, node=keys["node"])
        elif "wxml" in keys:
            WrapperXml.__init__(self, nodestring=keys["wxml"])
        else:
            raise PodError("Keys unknown in Interface", 0)

        self.registerslist = []
        self.portslist = []
        self.slaveslist = []

        if self.interface_class == "master":
            self.alloc_mem = AllocMem(self)
        if self.interface_class == "slave":
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

    @property
    def master(self):
        """ Get the master bus if exist """
        if self.interface_class != "slave":
            raise PodError("Only slave interface could have a master", 0)
        if self.interfacemaster is None:
            raise PodError("Interface " + self.name +
                           " is not connected on a master", 0)
        return self.interfacemaster

    @master.setter
    def master(self, masterinterface):
        if self.interface_class != "slave":
            raise PodError("interface " + self.name + " must be slave", 0)
        elif masterinterface.interface_class != "master":
            raise PodError("interface " + masterinterface.interface_class +
                           " must be master", 0)
        self.interfacemaster = masterinterface

    @property
    def interface_class(self):
        """ Get the class interface """
        return self.getAttributeValue("class")

    @interface_class.setter
    def interface_class(self, classname):
        """ Set the class interface """
        if classname not in INTERFACE_CLASS:
            raise PodError("classname " + classname + " unknown")
        self.setAttribute("class", classname)

    @property
    def base_addr(self):
        try:
            base = self.getAttributeValue("base", "registers")
            if base is None:
                raise PodError("Base address register not set", 0)
            return int(base, 16)
        except AttributeError:
            raise PodError("Base address register not set", 0)

    @base_addr.setter
    def base_addr(self, baseoffset):
        """ Set the base offset for this interface
            baseoffset is an hexadecimal string
            the interface must be a slave bus
        """
        if type(baseoffset) is str:
            baseoffset = int(baseoffset, 16)

        if self.getBusName() is None:
            raise PodError("Interface is not a bus", 1)
        if self.interface_class != "slave":
            raise PodError("Bus must be slave", 1)
        size = self.getMemorySize()
        if (baseoffset % size) != 0:
            raise PodError("Offset must be a multiple of " + hex(size), 1)
        self.setAttribute("base", hex(baseoffset), "registers")

    @property
    def addr_port_size(self):
        """ How many pin in address port ?  """
        try:
            return int(
                self.getPortByType(
                    self.bus.getSignalName("slave", "address")).size)
        except PodError:
            return 0

    def getMemorySize(self):
        """ Get the memory size """
        return ((2 ** self.addr_port_size) * self.regStep())

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
            if port.name == portname:
                return port
        raise PodError("Port " + portname + " does not exists", 1)

    def addPort(self, port):
        """ Adding a port """
        port.parent = self
        self.portslist.append(port)
        self.addSubNode(nodename="ports", subnode=port)

    def getPortByType(self, porttypename):
        """ Get port using port type name as argument"""
        for port in self.portslist:
            if port.porttype == porttypename:
                return port
        raise PodError("No port with type " + str(porttypename), 1)

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
        self.alloc_mem.delInterfaceSlave(slave.getInterface())
        self.slaveslist.remove(slave)
        self.delSubNode("slaves", "slave",
                        {"instancename": slave.instancename,
                         "interfacename": slave.interfacename})

    def del_bus(self, instanceslavename, interfaceslavename=None):
        """ delete slave bus connection
        """
        for slave in self.getSlavesList():
            if slave.instancename == instanceslavename:
                if interfaceslavename is None:
                    self.delSlave(slave)
                    return
                elif slave.interfacename == interfaceslavename:
                    self.delSlave(slave)
                    return
        raise PodError("Bus connection " + str(self.name) +
                       " -> " + str(instanceslavename) + "." +
                       str(interfaceslavename) + " doesn't exist", 0)

    def connect_interface(self, interface_dest):
        """ Connect an interface between two components
        """
        if len(interface_dest.ports) != len(self.ports):
            raise PodError(self.parent.name + "." + self.name +
                           " and " + interface_dest.parent.name +
                           "." + interface_dest.name +
                           "are not the same number of ports")
        for port in self.ports:
            if port.porttype is None:
                raise PodError(self.parent.name + "." +
                               self.name + "." +
                               port.name + " has no type")
            try:
                port_dst = interface_dest.getPortByType(port.porttype)
            except PodError, e:
                raise PodError(interface_dest.parent.name + "." +
                               interface_dest.name + " have no " +
                               port.porttype + " port")
            if port_dst.direction == port.direction:
                raise PodError("Ports " + self.parent.name + "." +
                               self.name + "." + port.name +
                               " and " +
                               interface_dest.parent.name + "." +
                               interface_dest.name + "." +
                               port_dst.name + " are the same direction")
            if port_dst.direction == "in" and port_dst.isVoid() is not True:
                raise PodError("Ports " + interface_dest.parent.name +
                               "." + interface_dest.name + "." +
                               port_dst.name + " is already connected")
            if port.direction == "in" and port.isVoid() is not True:
                raise PodError("Ports " + self.parent.name +
                               "." + self.name +
                               "." + port.name +
                               " is already connected")

        for port in self.ports:
            port_dst = interface_dest.getPortByType(port.porttype)
            port.connect_port(port_dst)

    def connect_bus(self, instanceslave, interfaceslavename):
        """ Connect an interfaceslave to an interface bus master
        """
        interfaceslave = instanceslave.getInterface(interfaceslavename)
        for slave in self.getSlavesList():
            if slave.instancename == instanceslave.instancename and\
                    slave.interfacename == interfaceslavename:
                raise PodError("Bus connection for " +
                               slave.instancename + "." +
                               slave.interfacename +
                               " already exists", 1)
        if self.getBusName() is None:
            raise PodError("Interface " + self.name + " must be a bus ")
        if interfaceslave.getBusName() is None:
            raise PodError("Interface " + interfaceslave.name +
                           " must be a bus ")
        if self.getBusName() != interfaceslave.getBusName():
            raise PodError("Can't connect " + self.getBusName() +
                           " on " + interfaceslave.getBusName(), 1)
        if self.interface_class != "master":
            raise PodError(self.name + " is not a master", 0)
        if interfaceslave.getBusName() is None:
            raise PodError(instanceslave.instancename +
                           "." + interfaceslave.name + " is not a bus", 1)
        if interfaceslave.interface_class != "slave":
            raise PodError(instanceslave.instancename +
                           "." + interfaceslave.name +
                           " is not a slave", 1)
        self.addSubNode(nodename="slaves",
                        subnodename="slave",
                        attributedict={
                            "instancename": instanceslave.instancename,
                            "interfacename": interfaceslavename})
        self.slaveslist.append(Slave(self,
                               instancename=instanceslave.instancename,
                               interfacename=interfaceslavename))
        self.alloc_mem.addInterfaceSlave(interfaceslave)
        interfaceslave.master = self
        interfaceslave.setID(self.alloc_mem.getID())
        instanceslave.getGeneric(
            genericname="id").setValue(
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

    def autoconnect_pins(self):
        """ autoconnect pin """
        for port in self.ports:
            port.autoconnect_pins()

    def connectClkDomain(self, instancedestname, interfacedestname):
        """ Connect clock domain
        """
        for slave in self.getSlavesList():
            if slave.instancename == instancedestname\
                    and slave.interfacename == interfacedestname:
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
            if register.name == registername:
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
            # display each register
            for register in self.registerslist:
                listreg.append(
                    {"offset": int(register.getOffset(), 16) * self.regStep() +
                        self.base_addr, "name": register.name})
            return listreg
        else:
            return [{"offset": self.base_addr,
                     "name": self.name}]

    def regStep(self):
        """ Step between two register """
        return int(self.bus.getDataSize()) / 8

    def getSysconInstance(self):
        """ Return syscon instance that drive master interface """
        for instance in self.parent.parent.instances:
            for interface in instance.getInterfacesList():
                if interface.interface_class == "clk_rst":
                    for slave in interface.getSlavesList():
                        if slave.instancename ==\
                            self.parent.instancename and\
                                slave.interfacename == self.name:
                            return instance
        raise PodError("No syscon for interface " + self.name +
                       " of instance " + self.parent.instancename, 0)

    def addRegister(self, register_name):
        if self.getBusName() is None:
            raise PodError("Interface must be a bus")
        elif self.interface_class != "slave":
            raise PodError("Bus must be a slave")
        # TODO: check if enough space in memory mapping to add register
        register = Register(self, register_name=register_name)
        self.registerslist.append(register)
        self.addSubNode(nodename="registers", subnode=register)

    def delRegister(self, register_name):
        # TODO
        pass
