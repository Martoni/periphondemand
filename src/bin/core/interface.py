#! /usr/bin/python3
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

from functools import cmp_to_key

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

        self._parent = parent

        if "name" in keys:
            WrapperXml.__init__(self, nodename="interface")
            self.name = keys["name"]
        elif "node" in keys:
            WrapperXml.__init__(self, node=keys["node"])
        elif "wxml" in keys:
            WrapperXml.__init__(self, nodestring=keys["wxml"])
        else:
            raise PodError("Keys unknown in Interface", 0)

        self._registerslist = []
        self.portslist = []
        self._slaveslist = []
        self._bus = None

        if self.interface_class == "master":
            self.alloc_mem = AllocMem(self)
        if self.interface_class == "slave":
            self.interfacemaster = None

        if self.get_node("slaves") is not None:
            for element in self.get_subnodes("slaves", "slave"):
                self._slaveslist.append(Slave(self, node=element))

        if self.get_node("registers") is not None:
            for element in self.get_subnodes("registers", "register"):
                self._registerslist.append(Register(self, node=element))

        if self.get_node("ports") is not None:
            for node in self.get_subnodes("ports", "port"):
                self.portslist.append(Port(self, node=node))

        # set bus
        if self.bus_name is not None:
            self.bus = self.bus_name

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
        """ set master interface """
        if self.interface_class != "slave":
            raise PodError("interface " + self.name + " must be slave", 0)
        elif masterinterface.interface_class != "master":
            raise PodError("interface " + masterinterface.interface_class +
                           " must be master", 0)
        self.interfacemaster = masterinterface

    @property
    def interface_class(self):
        """ Get the class interface """
        return self.get_attr_value("class")

    @interface_class.setter
    def interface_class(self, classname):
        """ Set the class interface """
        if classname not in INTERFACE_CLASS:
            raise PodError("classname " + classname + " unknown")
        self.set_attr("class", classname)

    @property
    def base_addr(self):
        """ get base address register value """
        try:
            base = self.get_attr_value("base", "registers")
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

        if self.bus_name is None:
            raise PodError("Interface is not a bus", 1)
        if self.interface_class != "slave":
            raise PodError("Bus must be slave", 1)
        size = self.mem_size
        if (baseoffset % size) != 0:
            raise PodError("Offset must be a multiple of " + hex(size), 1)
        self.set_attr("base", hex(baseoffset), "registers")

    @property
    def addr_port_size(self):
        """ How many pin in address port ?  """
        size = self.get_attr_value("addr_size")
        if size is not None:
            return int(size)
        try:
            return int(
                self.get_port_by_type(
                    self.bus.sig_name("slave", "address")).size)
        except PodError:
            return 0

    @property
    def mem_size(self):
        """ Get the memory size """
        return int((2 ** self.addr_port_size) * self.regstep)

    @property
    def data_size(self):
        """ Get bus size """
        size = self.get_attr_value("data_size")
        if size is None:
            return self.bus.data_size
        else:
            return size

    @property
    def addr_size(self):
        """ Get bus size """
        size = self.get_attr_value("addr_size")
        if size is None:
            return int(self.addr_port_size)
        else:
            return int(size)

    @property
    def bus_name(self):
        """ Get the bus name """
        return self.get_attr_value("bus")

    @property
    def bus(self):
        """ Get the interface bus"""
        return self._bus

    @bus.setter
    def bus(self, attribute):
        """ Set bus attribute"""
        self._bus = Bus(self, name=attribute)
        self.set_attr("bus", attribute)

    def is_bus(self):
        """ Test if this interface is a bus """
        if self._bus is None:
            return False
        return True

    @property
    def ports(self):
        """ get the ports list of interface"""
        return self.portslist

    def get_port(self, portname):
        """ Get port by its name """
        for port in self.portslist:
            if port.name == portname:
                return port
        raise PodError("Port " + portname + " does not exists", 1)

    def add_port(self, port):
        """ Adding a port """
        port.parent = self
        self.portslist.append(port)
        self.add_subnode(nodename="ports", subnode=port)

    def get_port_by_type(self, porttypename):
        """ Get port using port type name as argument"""
        for port in self.portslist:
            if port.porttype == porttypename:
                return port
        raise PodError("No port with type " + str(porttypename), 1)

    def del_pin(self, instancedest, interfacedest=None, portdest=None,
                pindest=None, portsource=None, pinsource=None):
        """ Delete all interface pins
        """
        if portsource is None:
            for port in self.ports:
                port.del_pin(instancedest=instancedest)
        else:
            port = self.get_port(portsource)
            port.del_pin(instancedest, interfacedest,
                         portdest, pindest, pinsource)

    @property
    def slaves(self):
        """ Get the slaves list of interface"""
        return self._slaveslist

    def del_slave(self, slave):
        """ Delet slave """
        self.alloc_mem.del_slave_interface(slave.get_interface())
        self._slaveslist.remove(slave)
        self.del_subnode("slaves", "slave",
                         {"instancename": slave.instancename,
                          "interfacename": slave.interfacename})

    def del_bus(self, instanceslavename, interfaceslavename=None):
        """ delete slave bus connection
        """
        for slave in self.slaves:
            if slave.instancename == instanceslavename:
                if interfaceslavename is None:
                    self.del_slave(slave)
                    return
                elif slave.interfacename == interfaceslavename:
                    self.del_slave(slave)
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
                port_dst = interface_dest.get_port_by_type(port.porttype)
            except PodError:
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
            port_dst = interface_dest.get_port_by_type(port.porttype)
            port.connect_port(port_dst)

    def connect_bus(self, instanceslave, interfaceslavename):
        """ Connect an interfaceslave to an interface bus master
        """
        interfaceslave = instanceslave.get_interface(interfaceslavename)
        for slave in self.slaves:
            if slave.instancename == instanceslave.instancename and\
                    slave.interfacename == interfaceslavename:
                raise PodError("Bus connection for " +
                               slave.instancename + "." +
                               slave.interfacename +
                               " already exists", 1)
        if self.bus_name is None:
            raise PodError("Interface " + self.name + " must be a bus ")
        if interfaceslave.bus_name is None:
            raise PodError("Interface " + interfaceslave.name +
                           " must be a bus ")
        if self.bus_name != interfaceslave.bus_name:
            raise PodError("Can't connect " + self.bus_name +
                           " on " + interfaceslave.bus_name, 1)
        if self.interface_class != "master":
            raise PodError(self.name + " is not a master", 0)
        if interfaceslave.bus_name is None:
            raise PodError(instanceslave.instancename +
                           "." + interfaceslave.name + " is not a bus", 1)
        if interfaceslave.interface_class != "slave":
            raise PodError(instanceslave.instancename +
                           "." + interfaceslave.name +
                           " is not a slave", 1)
        self.add_subnode(nodename="slaves",
                         subnodename="slave",
                         attributedict={
                             "instancename": instanceslave.instancename,
                             "interfacename": interfaceslavename})
        self._slaveslist.append(
            Slave(self,
                  instancename=instanceslave.instancename,
                  interfacename=interfaceslavename))
        self.alloc_mem.add_slave_interface(interfaceslave)
        interfaceslave.master = self
        interfaceslave.unique_id = self.alloc_mem.unique_id
        instanceslave.get_generic(genericname="id").value =\
            str(interfaceslave.unique_id)

    @property
    def unique_id(self):
        """ Get the Identifiant number"""
        try:
            return self.get_attr_value("unique_id")
        except PodError:
            return None

    @unique_id.setter
    def unique_id(self, unique_id):
        """ Set the Identifiant number"""
        self.set_attr("unique_id", str(unique_id))

    def autoconnect_pins(self):
        """ autoconnect pin """
        for port in self.ports:
            port.autoconnect_pins()

    def connect_clk_domain(self, instancedestname, interfacedestname):
        """ Connect clock domain
        """
        for slave in self.slaves:
            if slave.instancename == instancedestname\
                    and slave.interfacename == interfacedestname:
                raise PodError("Clock connection " + instancedestname +
                               "." + interfacedestname + " exists", 1)

        self.add_subnode(nodename="slaves", subnodename="slave",
                         attributedict={"instancename": instancedestname,
                                        "interfacename": interfacedestname})
        self._slaveslist.append(
            Slave(self,
                  instancename=instancedestname,
                  interfacename=interfacedestname))

    def get_register(self, registername):
        """ Get register by name """
        for register in self.registers:
            if register.name == registername:
                return register
        raise PodError("No register with name " + registername, 0)

    @property
    def parent(self):
        """ return parent instance """
        return self._parent

    @parent.setter
    def parent(self, parent):
        """ set parent instance """
        self._parent = parent

    @property
    def registers(self):
        """ return registers list """
        return self._registerslist

    @property
    def registers_map(self):
        """ Return the memory mapping for slave interface """
        if len(self._registerslist) != 0:
            listreg = []
            # sort registers dict by offset order
            self._registerslist.sort(key=lambda x: int(x.offset, 16))
            # display each register
            for register in self._registerslist:
                listreg.append(
                    {"offset": int(register.offset, 16) * self.regstep +
                        self.base_addr, "name": register.name})
            return listreg
        else:
            return [{"offset": self.base_addr, "name": self.name}]

    @property
    def regstep(self):
        """ Step between two register """
        return int(self.data_size) / 8
