#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Component.py
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
""" Manage component class """

import os
from periphondemand.bin.define import COMPONENTSPATH
from periphondemand.bin.define import XMLEXT

from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.display import Display

from periphondemand.bin.core.interface import Interface
from periphondemand.bin.core.hdl_file import Hdl_file
from periphondemand.bin.core.driver_templates import Driver_Templates
from periphondemand.bin.core.generic import Generic

SETTINGS = Settings()
DISPLAY = Display()


class Component(WrapperXml):
    """Manage components

    attributes:
        tree           -- root tree xml component
        settings       -- Settings object with system settings
        interfaceslist -- list of interfaces
        genericslist   -- list of generics

    """

    def __init__(self, parent=None, void=0):
        """ Init Component,
            __init__(self,parent)
        """
        self.void = void

        self.interfaceslist = []
        self.genericslist = []
        self.hdl_fileslist = []
        self.driver_templateslist = []
        self.interruptslist = []
        self.constraintslist = []

        # Project that use the component
        self.parent = parent

    def loadNewInstance(self, libraryname, componentname,
                        componentversion, instancename):
        """ Load a new component from library
        """
        project = self.parent
        # verify component name
        if project.getName() == instancename:
            raise PodError("Instance name can't be " +
                           "the same name as projectname", 0)
        # test if component exist
        if not sy.fileExist(project.library.getLibraryPath(libraryname) +
                            "/" + componentname):
            raise PodError("No component with name " +
                           libraryname + "." + componentname, 0)

        # test if several componentversion
        if componentversion is None:
            if len(project.get_components_versions(libraryname,
                                                   componentname)) > 1:
                raise PodError("Component version must be chosen :" +
                               str(project.get_components_versions(
                                   libraryname, componentname)), 0)
            else:
                try:
                    componentversion = project.get_components_versions(
                        libraryname, componentname)[0]
                except IndexError:
                    raise PodError("No xml description of component", 0)
        if instancename is None:
            instancename =\
                componentname + "%02d" %\
                len(project.get_instances_list_of_component(componentname))

        # copy and rename directory
        sy.copyDirectory(project.library.getLibraryPath(libraryname) +
                         "/" + componentname,
                         SETTINGS.projectpath + COMPONENTSPATH)
        try:
            sy.renameDirectory(SETTINGS.projectpath +
                               COMPONENTSPATH + "/" + componentname,
                               SETTINGS.projectpath + COMPONENTSPATH +
                               "/" + instancename)
        except PodError:  # if directory exist
            pass
        # Rename xml file
        sy.renameFile(SETTINGS.projectpath +
                      COMPONENTSPATH + "/" + instancename +
                      "/" + componentversion + XMLEXT,
                      SETTINGS.projectpath + COMPONENTSPATH +
                      "/" + instancename + "/" + instancename + XMLEXT)

        # load component
        self.loadInstance(instancename)
        # Connect platform connection
        self.autoconnectPin()

    def loadInstance(self, instancename):
        """ Load an instance from project directory
        """
        # load xml file
        WrapperXml.__init__(self, file=SETTINGS.projectpath +
                            COMPONENTSPATH + "/" + instancename +
                            "/" + instancename + XMLEXT)

        # Fill objects list
        if self.getNode("interfaces") is not None:
            for element in self.getSubNodeList("interfaces", "interface"):
                self.interfaceslist.append(Interface(self, node=element))

        if self.getNode("generics") is not None:
            for element in self.getSubNodeList("generics", "generic"):
                self.genericslist.append(Generic(self, node=element))

        if self.getNode("hdl_files") is not None:
            for element in self.getSubNodeList("hdl_files", "hdl_file"):
                self.hdl_fileslist.append(Hdl_file(self, node=element))

        if self.getNode("driver_files") is not None:
            for element in\
                    self.getSubNodeList("driver_files", "driver_templates"):
                self.driver_templateslist.append(
                    Driver_Templates(self, node=element))

        if self.getNode("interrupts") is not None:
            for element in self.getSubNodeList("interrupts", "interrupt"):
                self.interruptslist.append(
                    self.getInterface(
                        element.getAttributeValue("interface")).getPort(
                            element.getAttributeValue("port")))

        if self.getNode("constraints") is not None:
            for element in self.getSubNodeList("constraints", "constraint"):
                self.constraintslist.append(element)

        self.setInstanceName(instancename)

    def getConstraintsList(self):
        """ Get list of constraints """
        return self.constraintslist

    def autoconnectPin(self):
        """ Auto connect platform default pins
        """
        for interface in self.getInterfacesList():
            interface.autoconnectPin()

    def getHdl_filesList(self):
        """ Get list of HDL files """
        return self.hdl_fileslist

    def getHDLTop(self):
        """ Get hdl top file """
        for hdlfile in self.getHdl_filesList():
            if hdlfile.isTop():
                return hdlfile
        return None

    def getHDLFile(self, filename):
        """ get hdl file """
        for hdlfile in self.getHdl_filesList():
            if hdlfile.getFileName() == filename:
                return hdlfile
        raise PodError("no hdl file named " + filename)

    def addHdl_file(self, hdl_file):
        """ add hdl file """
        self.addSubNode(nodename="hdl_files", subnode=hdl_file)
        return self.hdl_fileslist.append(hdl_file)

    def getComponentPath(self):
        """ return path of component in system
        """
        librarypath = SETTINGS.active_library.getLibraryPath()
        return os.path.join(librarypath, self.getName())

    def getInterruptList(self):
        """ Get interrupt list """
        return self.interruptslist

    def getGenericsList(self):
        """ Get generics parameters list """
        return self.genericslist

    def getFPGAGenericsList(self):
        """ Get fpga specifics generic list """
        fpgalist = []
        for generic in self.getGenericsList():
            if generic.getDestination() == "fpga" or\
                    generic.getDestination() == "both":
                fpgalist.append(generic)
        return fpgalist

    def getGeneric(self, genericname):
        """ get a generic """
        for generic in self.getGenericsList():
            if generic.getName() == genericname:
                return generic
        raise PodError("No generic with name " + genericname, 0)

    def addGeneric(self, generic):
        """ Adding a generic """
        generic.parent = self
        self.genericslist.append(generic)
        self.addSubNode(nodename="generics", subnode=generic)

    def getInterface(self, interfacename):
        """ Get an interface by name """
        for interface in self.interfaceslist:
            if interface.getName() == interfacename:
                return interface
        raise PodError("Interface " + str(interfacename) +
                       " does not exists", 0)

    def getMasterInterfaceList(self):
        """ return a list of master interface """
        interfacelist = []
        for interface in self.getInterfacesList():
            if interface.getClass() == "master":
                interfacelist.append(interface)
        return interfacelist

    def getSlaveInterfaceList(self):
        """ return a list of slave interface """
        interfacelist = []
        for interface in self.getInterfacesList():
            if interface.getClass() == "slave":
                interfacelist.append(interface)
        return interfacelist

    def getSysconInterface(self):
        """ Get the syscon interface"""
        for interface in self.getInterfacesList():
            if interface.getClass() == "clk_rst":
                break
        return interface

    def createInterface(self, interfacename):
        """ Create an interface and add it in component """
        if interfacename in [interface.getName() for
                             interface in self.getInterfacesList()]:
            raise PodError("Interface " + interfacename +
                           " already exist in component")
        interface = Interface(self, name=interfacename)
        self.addInterface(interface)

    def addInterface(self, interface):
        """ Add an interface in component """
        interface.parent = self
        self.interfaceslist.append(interface)
        self.addSubNode(nodename="interfaces", subnode=interface)

    def getInterfacesList(self):
        """ Get the list of interfaces """
        return self.interfaceslist

    def getDriver_TemplateList(self):
        """ get the driver template list """
        return self.driver_templateslist

    def getDriver_Template(self, architecture):
        """ Get a driver template """
        for driverT in self.getDriver_TemplateList():
            if driverT.getArchitecture() == architecture:
                return driverT
        return None

    def saveInstance(self):
        """ Save component in project directory files """
        if not sy.dirExist(SETTINGS.projectpath + COMPONENTSPATH +
                           "/" + self.getInstanceName()):
            sy.makeDirectory(SETTINGS.projectpath + COMPONENTSPATH +
                             "/" + self.getInstanceName())
        self.saveXml(SETTINGS.projectpath + COMPONENTSPATH + "/" +
                     self.getInstanceName() + "/" +
                     self.getInstanceName() + ".xml")

    def delInstance(self):
        """ suppress component instance """
        if not self.isPlatform():
            sy.delDirectory(SETTINGS.projectpath + COMPONENTSPATH + "/" +
                            self.getInstanceName())

    def getInstanceName(self):
        """ get the name of this component instance"""
        return self.getAttributeValue("instance_name")

    def setInstanceName(self, instancename):
        """ set the name of this instance """
        return self.setAttribute("instance_name", instancename)

    def setNum(self, num):
        """ select the instance number """
        return self.setAttribute("num", str(num))

    def getNum(self):
        """ Get the instance number """
        return self.getAttributeValue("num")

    def invertDir(self, dirname):
        """ invert direction given in params """
        if dirname == "in":
            return "out"
        if dirname == "out":
            return "in"
        if dirname == "inout":
            return "inout"

    def deletePin(self,
                  instancedest, interfacedest=None, portdest=None,
                  pindest=None, interfacesource=None, portsource=None,
                  pinsource=None):
        """ Delete component pin connection, if only instancedest given,
            all connection towards this instance are removed
        """
        if interfacesource is None:
            for interface in self.getInterfacesList():
                interface.deletePin(instancedest=instancedest)
        else:
            interface = self.getInterface(interfacesource)
            interface.deletePin(instancedest,
                                interfacedest,
                                portdest,
                                pindest,
                                portsource,
                                pinsource)

    def connect_bus(self, interfacemaster, instanceslave, interfaceslave):
        """ Connect an interface bus master to slave """
        interface = self.getInterface(interfacemaster)
        if interface.getName() is None:
            raise PodError(interfacemaster + " is not a bus", 1)
        interface.connect_bus(instanceslave, interfaceslave)

    def del_bus(self, instanceslavename, interfacemaster=None,
                interfaceslavename=None):
        """ Delete bus connection that refer to instanceslavename """
        if interfacemaster is None:
            for interface in self.getInterfacesList():
                try:
                    interface.del_bus(instanceslavename)
                except PodError:
                    pass
        else:
            interface = self.getInterface(interfacemaster)
            interface.del_bus(instanceslavename, interfaceslavename)

    def connectClkDomain(self, instancedestname, interfacesourcename,
                         interfacedestname):
        """ Connect clock domain """
        interface = self.getInterface(interfacesourcename)
        interface.connectClkDomain(instancedestname, interfacedestname)

    def addPort(self, portname, interfacename):
        """ Add port named portname in interface named interfacename """
        # verify if portname exist in vhdl file
        hdltop = self.getHDLTop()
        if not hdltop:
            raise PodError("No HDL top file in component " +
                           str(self.getName()))
        portlist = hdltop.ports
        if portname not in [port.getName() for port in portlist]:
            raise PodError("Port named " + portname + " can't be found in " +
                           hdltop.getFileName())

        # verify if port is not already placed
        isinfreelist, interface_old = self.portIsInFreeList(portname)
        if not isinfreelist:
            raise PodError("Port named " + portname +
                           " is already placed in " + interface_old)
        # take interface
        interface = self.getInterface(interfacename)
        # create port object
        port = hdltop.getPort(portname)
        # place port in interface
        interface.addPort(port)

    def portIsInFreeList(self, portname):
        """ If port named portname is not in interface, return 1
            else return 0 and interface
        """
        interfaceslist = self.getInterfacesList()
        for interface in interfaceslist:
            portlist = interface.ports
            for port in portlist:
                if port.getName() == portname:
                    return (0, interface.getName())
        return (1, "")

    def getFreePortsList(self):
        """ return not assignated ports list """
        ports_list = self.getHDLTop().ports
        freeportlist = []
        for port in ports_list:
            if self.portIsInFreeList(port.getName()):
                freeportlist.append(port)
        return freeportlist

    @property
    def ports(self):
        """ return list of ports in component
            display_port = list of:
                {"interfacename":[portname1,portname2]}
        """
        display_port = {}
        tophdlfile = self.getHDLTop()
        notassignedports = [port.getName() for
                            port in tophdlfile.ports]
        interfacelist = self.getInterfacesList()
        for interface in interfacelist:
            key = interface.getName()
            display_port[key] = []
            port_name_list = [port.getName() for
                              port in interface.ports]
            for port_name in port_name_list:
                try:
                    notassignedports.remove(port_name)
                except ValueError:
                    raise PodError("HDL top file and XML component " +
                                   "description are not consistant. Port " +
                                   port_name + " in component" +
                                   " description is not present in HDL file ")
                display_port[key].append(port_name)
        if len(notassignedports) != 0:
            display_port["Not_assigned_Ports"] = notassignedports
        return display_port

    def isPlatform(self):
        """ is this component instance is a Platform ?"""
        return False

    # Settings attributes for nodes
    def setGeneric(self, generic_name, attribute_name,
                   attribute_value):
        """Add or modify attribute value for a node """
        generic = self.getGeneric(generic_name)
        if attribute_name == "name":
            generic.setName(attribute_value)
        elif attribute_name == "public":
            generic.setPublic(attribute_value)
        elif attribute_name == "value":
            generic.setValue(attribute_value)
        elif attribute_name == "match":
            generic.setMatch(attribute_value)
        elif attribute_name == "type":
            generic.setType(attribute_value)
        elif attribute_name == "destination":
            generic.setDestination(attribute_value)
        else:
            raise PodError("Unknown attribute " + str(attribute_name))

    def setHDL(self, file_name, attribute_name,
               attribute_value):
        """ Setting HDL files """
        HDL = self.getHDLFile(file_name)
        if attribute_name == "filename":
            HDL.setFileName(attribute_value)
        elif attribute_name == "scope":
            HDL.setScope(attribute_value)
        elif attribute_name == "istop":
            if attribute_value == "1":
                HDL.setTop()
            elif attribute_value == "0":
                HDL.unsetTop()
            else:
                raise PodError("Unknown top value " + str(attribute_value))
        else:
            raise PodError("Unknown attribute " + str(attribute_name))

    def setInterface(self, interface_name, attribute_name,
                     attribute_value):
        """Add or modify attribute value for a node """
        interface = self.getInterface(interface_name)
        if attribute_name == "name":
            interface.setName(attribute_value)
        elif attribute_name == "bus":
            interface.setBus(attribute_value)
        elif attribute_name == "class":
            interface.setClass(attribute_value)
        elif attribute_name == "clockandreset":
            interface.setClockAndReset(attribute_value)
        else:
            raise PodError("Unknown attribute " + str(attribute_name))

    def setPort(self, interface_name, port_name,
                attribute_name, attribute_value):
        """ Setting port"""
        interface = self.getInterface(interface_name)
        port = interface.getPort(port_name)
        if attribute_name == "name":
            port.setName(attribute_value)
        elif attribute_name == "type":
            port.setType(attribute_value)
        elif attribute_name == "size":
            port.setSize(attribute_value)
        elif attribute_name == "dir":
            port.setDir(attribute_value)
        else:
            raise PodError("Attribute " + str(attribute_name) + " unknown")

    def setRegister(self, interface_name, register_name,
                    attribute_name, attribute_value):
        """ Setting register """
        interface = self.getInterface(interface_name)
        register = interface.getRegister(register_name)
        if attribute_name == "name":
            register.setName(attribute_value)
        elif attribute_name == "offset":
            register.setOffset(attribute_value)
        elif attribute_name == "size":
            register.setSize(attribute_value)
        elif attribute_name == "rows":
            register.setRows(attribute_value)
        else:
            raise PodError("Attribute " + str(attribute_name) + " unknown")

    def addRegister(self, interface_name, register_name):
        """ Add register in interface, interface must be a bus slave"""
        interface = self.getInterface(interface_name)
        interface.addRegister(register_name)
