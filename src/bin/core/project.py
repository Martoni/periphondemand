#!/usr/bin/python
# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------------
# Name:     Project.py
# Purpose:
#
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
#
# Created:  24/04/2008
# Licence:  GPLv3 or newer
#
# ----------------------------------------------------------------------------
""" Main class to manage project"""

__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import os
import re
from periphondemand.bin.define import XMLEXT
from periphondemand.bin.define import BINARYPROJECTPATH
from periphondemand.bin.define import COMPONENTSPATH
from periphondemand.bin.define import OBJSPATH
from periphondemand.bin.define import SIMULATIONPATH
from periphondemand.bin.define import SYNTHESISPATH
from periphondemand.bin.define import DRIVERSPATH
from periphondemand.bin.define import TOOLCHAINPATH
from periphondemand.bin.define import PLATFORMPATH
from periphondemand.bin.define import ONETAB

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils.error import Error

from periphondemand.bin.utils import wrappersystem as sy

from periphondemand.bin.core.component import Component
from periphondemand.bin.core.platform import Platform
from periphondemand.bin.core.library import Library

from periphondemand.bin.toolchain.simulation import Simulation
from periphondemand.bin.toolchain.synthesis import Synthesis
from periphondemand.bin.toolchain.driver import Driver

SETTINGS = Settings()
DISPLAY = Display()


class Project(WrapperXml):
    """This class manage the project

    attributes:
    instanceslist  -- list of objects component in the project
    settings       -- Settings object containing system parameters
    platform       -- platform oblect containing platform dependances

    """

    def __init__(self, projectpathname, void=0,
                 description="insert a description here"):
        """ create project if doesn't exist
        """
        self.void = void
        WrapperXml.__init__(self, nodename="void")
        self._instanceslist = []
        self._vhdl_version = "vhdl87"

        self.simulation = None
        self.synthesis = None
        self.driver = None

        self.library = Library()

        self.bspdir = None
        self.bspos = None
        if not self.isVoid():
            if projectpathname.find(XMLEXT) >= 0:
                try:
                    SETTINGS.projectpath =\
                        os.path.abspath(os.path.dirname(projectpathname))
                except IOError, error:
                    raise Error(str(error), 0)
            else:
                SETTINGS.projectpath = projectpathname
            SETTINGS.author = ""
            name = os.path.basename(projectpathname)
            if sy.fileExist(projectpathname):
                self.load_project(projectpathname)
            else:
                self.create_project(name)
            self.setDescription(description)

            SETTINGS.active_project = self

    def create_project(self, name):
        """ Create a project """
        if sy.dirExist(SETTINGS.projectpath):
            raise Error("Can't create project, directory " + name +
                        " allready exists", 0)
        sy.makeDirectory(SETTINGS.projectpath)

        sy.makeDirectory(SETTINGS.projectpath + BINARYPROJECTPATH)
        sy.makeDirectory(SETTINGS.projectpath + COMPONENTSPATH)
        sy.makeDirectory(SETTINGS.projectpath + OBJSPATH)

        sy.makeDirectory(SETTINGS.projectpath + SIMULATIONPATH)
        sy.makeDirectory(SETTINGS.projectpath + SYNTHESISPATH)
        sy.makeDirectory(SETTINGS.projectpath + DRIVERSPATH)

        self.createXml("project")
        self.setName(name)
        self.setVersion("1.0")
        self.void = 0
        self.save()

    def load_project(self, pathname):
        """ Load the  project
        """
        self.openXml(pathname)
        components = self.getNode("components")
        # load components
        if(components):
            for node in components.getNodeList("component"):
                if node.getAttributeValue("platform") is None:
                    comp = Component(self)
                else:
                    comp = Platform(self, node=self.getNode("platform"))
                try:
                    comp.loadInstance(node.getAttributeValue("name"))
                except IOError:
                    self.delSubNode("components",
                                    "component",
                                    "name", node.getAttributeValue("name"))
                    raise Error("Can't open " +
                                node.getAttributeValue("name") + " directory",
                                0)
                else:
                    self._instanceslist.append(comp)

        # load toolchains
        # toolchains = self.getNode("toolchain")
        # if(toolchains):
        #       node = toolchains.getNode("simulation")
        #       if node!=None:
        #           self.simulation = Simulation(self, node.getName())
        #       node = toolchains.getNode("synthesis")
        #       if node!=None:
        #           self.synthesis = Synthesis(self, node.getName())
        try:
            self.synthesis = Synthesis(self)
        except Error, error:
            DISPLAY.msg(str(error))
        try:
            self.simulation = Simulation(self)
        except Error, error:
            DISPLAY.msg(str(error))

        # Set bus master-slave
        for masterinterface in self.interfaces_master:
            for slave in masterinterface.getSlavesList():
                slaveinterface = slave.getInterface()
                masterinterface.allocMem.addInterfaceSlave(slaveinterface)
                slaveinterface.setMaster(masterinterface)

        # set bsp directory
        if self.getNode(nodename="bsp") is not None:
            self.bspdir = self.getNode(
                nodename="bsp").getAttributeValue("directory")
        self.void = 0

    @property
    def synthesis_toolchain(self):
        """ Get synthesis toolchain """
        return self.synthesis

    @synthesis_toolchain.setter
    def synthesis_toolchain(self, toolchainname):
        """ Set the synthesis toolchain """
        if toolchainname not in self.get_synthesis_toolchains():
            raise Error("No toolchain named " + toolchainname + " in POD")
        sy.copyFile(SETTINGS.path + TOOLCHAINPATH + SYNTHESISPATH +
                    "/" + toolchainname + "/" + toolchainname + XMLEXT,
                    SETTINGS.projectpath + SYNTHESISPATH + "/")
        sy.renameFile(SETTINGS.projectpath + SYNTHESISPATH +
                      "/" + toolchainname + XMLEXT,
                      SETTINGS.projectpath + SYNTHESISPATH +
                      "/synthesis" + XMLEXT)
        self.synthesis = Synthesis(self)
        self.save()

    @property
    def fpga_speed_grade(self):
        """ Get FPGA speedgrade """
        return self.platform.getSpeed()

    @fpga_speed_grade.setter
    def fpga_speed_grade(self, speed):
        """ Set FPGA speedgrade """
        self.platform.setSpeed(speed)
        self.save()

    @property
    def fpga_device(self):
        """ get fpgadevice """
        return self.platform.getDevice()

    @fpga_device.setter
    def fpga_device(self, device):
        """ set fpga device """
        self.platform.setDevice(device)
        self.save()

    @property
    def simulation_toolchain(self):
        """ get simulation toolchain """
        return self.simulation

    @simulation_toolchain.setter
    def simulation_toolchain(self, toolchainname):
        """ Set simulation toolchain """
        if toolchainname not in self.get_simulation_toolchains():
            raise Error("No toolchain named " + toolchainname + " in POD")
        sy.copyFile(SETTINGS.path + TOOLCHAINPATH + SIMULATIONPATH +
                    "/" + toolchainname + "/" + toolchainname + XMLEXT,
                    SETTINGS.projectpath + SIMULATIONPATH + "/")
        sy.renameFile(SETTINGS.projectpath + SIMULATIONPATH +
                      "/" + toolchainname + XMLEXT,
                      SETTINGS.projectpath + SIMULATIONPATH +
                      "/simulation" + XMLEXT)
        self.simulation = Simulation(self)
        self.save()

    @property
    def driver_toolchain(self):
        """ get driver toolchain """
        return self.driver

    @driver_toolchain.setter
    def driver_toolchain(self, toolchainname):
        """ set driver toolchain """
        if toolchainname not in self.get_driver_toolchains():
            raise Error("No toolchain named " + toolchainname + " in POD")
        sy.copyFile(SETTINGS.path + TOOLCHAINPATH + DRIVERSPATH +
                    "/" + toolchainname + "/" + toolchainname + XMLEXT,
                    SETTINGS.projectpath + DRIVERSPATH + "/")
        sy.renameFile(SETTINGS.projectpath + DRIVERSPATH +
                      "/" + toolchainname + XMLEXT,
                      SETTINGS.projectpath + DRIVERSPATH +
                      "/drivers" + XMLEXT)
        self.driver = Driver(self)
        self.save()

    def set_unconnected_value(self, instancename, interfacename,
                              portname, value):
        """ Set port unconnected value
        """
        port = self.get_instance(
            instancename).getInterface(
                interfacename).getPort(portname)
        port.set_unconnected_value(value)
        self.save()

    def set_force(self, portname, state):
        """ May the force be with you """
        platform = self.platform
        interfaces_list = platform.getInterfacesList()
        if len(interfaces_list) != 1:
            raise Error("I found " + str(len(interfaces_list)) +
                        " FPGAs (" + str(interfaces_list) +
                        ") and multiple FPGA project is not implemented yet.")
        port = interfaces_list[0].getPort(portname)
        if port.getDir() == "in":
            raise Error("The value of this port can't be set " +
                        "because of it's direction (in)")
        port.force = state
        self.save()

    @property
    def forced_ports(self):
        """ List FPGA forced FPGA pin """
        platform = self.platform
        return platform.getForcesList()

    @property
    def vhdl_version(self):
        """ get vhdl version (VHDL '87 or '93) """
        return self._vhdl_version

    @vhdl_version.setter
    def vhdl_version(self, version):
        """ select vhdl version (VHDL '87 or '93) """
        if (version != "vhdl93") and (version != "vhdl87"):
            raise Error(str(version) + " is not acceptable version")
        self._vhdl_version = version
        self.save()

    def add_component_lib(self, path):
        """ Adding a component library under the project """
        if sy.dirExist(path):
            if self.getNode("componentslibs") is None:
                self.addNode(nodename="componentslibs")
            self.addSubNode(nodename="componentslibs",
                            subnodename="componentslib",
                            attributename="path",
                            value=path)
            self.save()
        else:
            raise Error("ComponentsLib directory " +
                        str(path) + " doesn't exists")

    def add_platforms_lib(self, path):
        """ Adding a platforms library under the project """
        if sy.dirExist(path):
            if self.getNode("platformlibs") is None:
                self.addNode(nodename="platformlibs")
            self.addSubNode(nodename="platformlibs",
                            subnodename="platformlib",
                            attributename="path",
                            value=path)
            self.save()
        else:
            raise Error("ComponentsLib directory " + str(path) +
                        " doesn't exists")

    def add_instance(self, **keys):
        """ Add a component in project

        add_instance(self, component)
        add_instance(self, libraryname, componentname)
        add_instance(self, libraryname, componentname, instancename)
        add_instance(self, libraryname, componentname, componentversion)
        add_instance(self, libraryname, componentname,
                            componentversion, instancename)
        """
        if "component" in keys:
            comp = keys["component"]
            instancename = comp.getInstanceName()
        elif ("componentname" in keys) and ("libraryname" in keys):
            componentname = keys["componentname"]
            libraryname = keys["libraryname"]
            if "instancename" in keys:
                instancename = keys["instancename"]
                # check if instancename is not <componentname><number><number>
                if re.match(r'^' + componentname + r'\d{2}$', instancename):
                    raise Error("Instance name forbiden, it's reserved for " +
                                "automatic instance name generation :" +
                                instancename, 0)
                # check instance availability
                for instance in self.instances:
                    if instance.getName() == instancename:
                        raise Error("This instance name already exists", 0)
            else:
                instancename =\
                    componentname +\
                    "%02d" %\
                    len(self.get_instances_list_of_component(componentname))
            if "componentversion" in keys:
                componentversion = keys["componentversion"]
            else:
                componentversion = None
            # Load and create component
            if (componentname == instancename):
                raise Error("Instance name can't be the" +
                            "same as component name", 0)
            comp = Component(self)
            comp.loadNewInstance(libraryname,
                                 componentname,
                                 componentversion,
                                 instancename)
            comp.setNum(
                len(self.get_instances_list_of_component(componentname)))
        else:
            raise Error("Key not known in add_instance", 0)

        # Add component to project
        self._instanceslist.append(comp)
        if comp.getName() != "platform":
            self.addSubNode(nodename="components",
                            subnodename="component",
                            attributename="name",
                            value=instancename)
        else:
            attrib = {"name": instancename, "platform": "true"}
            self.addSubNode(nodename="components",
                            subnodename="component",
                            attributedict=attrib)
        DISPLAY.msg("Component " + comp.getName() +
                    " added as " + instancename)
        self.save()

    @property
    def interfaces_master(self):
        """ Return a list of master interface
        """
        interfacelist = []
        for instance in self.instances:
            for interface in instance.getInterfacesList():
                if interface.getClass() == "master":
                    interfacelist.append(interface)
        return interfacelist

    @property
    def interfaces_slave(self):
        """ Return a list of slave interface
        """
        interfacelist = []
        for instance in self.instances:
            for interface in instance.getInterfacesList():
                if interface.getClass() == "slave":
                    interfacelist.append(interface)
        return interfacelist

    def get_instance(self, instancename):
        """ Return the instance by name
        """
        for instance in self.instances:
            if instance.getInstanceName() == instancename:
                return instance
        raise Error("Instance " + instancename + " doesn't exists")

    @property
    def instances(self):
        """ Get instances list of project """
        return self._instanceslist

    @property
    def variable_ports(self):
        """ Get list of all variable ports available in project
        """
        variable_ports_list = []
        for port in self.ports:
            if port.isvariable():
                variable_ports_list.append(port)
        return variable_ports_list

    @property
    def ports(self):
        """ Get list of all ports available in project
        """
        ports_list = []
        for instance in self.instances:
            for interface in instance.getInterfacesList():
                for port in interface.ports:
                    ports_list.append(port)
        return ports_list

    def get_instances_list_of_component(self, componentname):
        """ return a list of instances for a componentname """
        listinstance = []
        for instance in self.instances:
            if instance.getName() == componentname:
                listinstance.append(instance)
        return listinstance

    @property
    def platform(self):
        """ return component instance platform
        """
        for component in self.instances:
            if component.getName() == "platform":
                return component
        raise Error("No platform in project", 1)

    @property
    def platform_name(self):
        """ return platform name """
        return self.getNode("platform").getAttributeValue("name")

    @property
    def clock_ports(self):
        """ return a list of external clock port
        """
        # looking for port connected to platform
        # with type="CLK" and "in" direction
        portlist = []
        platformname = self.platform.getInstanceName()
        for instance in self.instances:
            if not instance.isPlatform():
                for interface in instance.getInterfacesList():
                    for port in interface.ports:
                        if (port.getDir() == "in") and \
                            (port.getSize() == "1") and \
                                (port.getType() == "CLK"):
                            for pin in port.getPinsList():
                                if len(pin.getConnections()) == 1:
                                    connection = pin.getConnections()[0]
                                    if connection["instance_dest"] == \
                                            platformname:
                                        portlist.append(port)
        return portlist

    def select_platform(self, platformname, platformlibname):
        """ Select a platform for the project
        """
        # suppress platform if already exists
        try:
            self.del_platform()
        except Error, error:
            if error.getLevel() < 2:
                raise error
            print error

        if platformlibname == "standard":
            platformdir = SETTINGS.path + PLATFORMPATH +\
                "/" + platformname + "/"
        else:
            # if not standard platform, try personnal platform
            try:
                platformdir = SETTINGS.getPlatformLibPath(platformlibname) +\
                    "/" + platformname + "/"
            except TypeError:
                # if not personnal platform, try project specific
                # platform (added with add_platforms_lib cmd)
                platformdir = ""
                for node in self.getSubNodeList("platformlibs", "platformlib"):
                    apath = node.getAttributeValue("path")
                    if apath.split("/")[-1] == platformlibname:
                        platformdir = apath + "/" + platformname + "/"
                if platformdir == "":
                    raise Error("Platform name error")
        platform = Platform(self, file=platformdir + platformname + XMLEXT)

        if sy.fileExist(platformdir + SIMULATIONPATH):
            sy.copyAllFile(platformdir + SIMULATIONPATH,
                           SETTINGS.projectpath + SIMULATIONPATH)
        self.add_instance(component=platform)
        self.addNode(node=platform)
        # Adding platform default components
        for component in platform.getComponentsList():
            self.add_instance(libraryname=component["type"],
                              componentname=component["name"])
        self.save()

    def del_platform(self):
        """ Suppress platform from project
        """
        # find platform in components list
        try:
            platform = self.platform
        except Error:
            raise Error("No platform in project", 2)

        self.del_instance(platform.getInstanceName())
        self.delNode("platform")
        self.save()

    @classmethod
    def availables_plat(cls):
        """ List all supported platforms names
        """
        platformlist = sy.listDirectory(SETTINGS.path + PLATFORMPATH)
        return platformlist

    def del_instance(self, instancename):
        """ Remove instance from project
        """
        instance = self.get_instance(instancename)
        # remove pins connections from project instances to this instancename
        for interface in instance.getInterfacesList():
            for port in interface.ports:
                for pin in port.getPinsList():
                    pin.delAllConnections()
        # remove busses connections from project instances to this instancename
        for comp in self.instances:
            if comp.getName() != "platform":
                comp.del_bus(instanceslavename=instancename)
        # Remove components from project
        self._instanceslist.remove(instance)
        self.reorder_instances(instance.getName())
        self.delSubNode("components",
                        "component",
                        "name",
                        instance.getInstanceName())
        instance.delInstance()
        DISPLAY.msg("Component " + instancename + " deleted")
        self.save()

    def save(self):
        """ Save the project """
        for comp in self._instanceslist:
            comp.saveInstance()
        if self.synthesis is not None:
            self.synthesis.save()
        if self.simulation is not None:
            self.simulation.save()
        self.saveXml(SETTINGS.projectpath + "/" + self.getName() + XMLEXT)

    def connect_pin_cmd(self, pin_source, pin_dest):
        """ connect pin between two instances
        """
        if pin_source.getParent().getParent().isBus():
            raise Error("One of this pin is under a bus interface." +
                        "Please use connectbus.")
        if pin_dest.getParent().getParent().isBus():
            raise Error("One of this pin is under a bus interface." +
                        "Please use connectbus.")
        pin_source.connectPin(pin_dest)
        self.save()

    def delete_pin_connection_cmd(self,
                                  instance_source_name, interface_source_name,
                                  port_source_name, pin_source_num,
                                  instance_dest_name, interface_dest_name,
                                  port_dest_name, pin_dest_num):
        """ delete pin between two instances
        """
        instance_source = self.get_instance(instance_source_name)
        interface_source = instance_source.getInterface(interface_source_name)
        port_source = interface_source.getPort(port_source_name)
        if pin_source_num is None:
            if(port_source.getSize()) == 1:
                pin_source_num = "0"
            else:
                raise Error("Source pin number not given, and port size > 1")
        pin_source = port_source.getPin(pin_source_num)

        # test if destination given
        if (instance_dest_name is not None) and\
           (interface_dest_name is not None) and\
           (port_dest_name is not None) and\
           (pin_dest_num is not None):
            instance_dest = self.get_instance(instance_dest_name)
            interface_dest = instance_dest.getInterface(interface_dest_name)
            port_dest = interface_dest.getPort(port_dest_name)
            pin_dest = port_dest.getPin(pin_dest_num)

            pin_source.delConnection(pin_dest)
            pin_dest.delConnection(pin_source)
            # if only instance_source given,
        else:  # delete all connection from this instance_source
            for connection in pin_source.getConnections():
                instance_dest = self.get_instance(connection["instance_dest"])
                interface_dest =\
                    instance_dest.getInterface(connection["interface_dest"])
                port_dest = interface_dest.getPort(connection["port_dest"])
                pin_dest = port_dest.getPin(connection["pin_dest"])

                pin_source.delConnection(pin_dest)
                pin_dest.delConnection(pin_source)
        self.save()

    def generate_intercon(self, instance_name, interface_name):
        """ generate intercon for interface interface_name """
        # test if intercon already exists
        from periphondemand.bin.code.intercon import Intercon
        try:
            intercon = self.get_instance(instance_name + "_" +
                                         interface_name + "_intercon")
        except Error:
            pass
        else:
            self.del_instance(intercon.getInstanceName())

        intercon = Intercon(self.get_instance(
                            instance_name).getInterface(interface_name),
                            self)
        self.add_instance(component=intercon)
        self.save()

    def connect_port(self,
                     instance_source_name, interface_source_name,
                     port_source_name,
                     instance_dest_name, interface_dest_name,
                     port_dest_name):
        """ Connect all pins of a port source on all pins of
            port dest
        """
        instance_source = self.get_instance(instance_source_name)
        interface_source = instance_source.getInterface(interface_source_name)
        port_source = interface_source.getPort(port_source_name)

        instance_dest = self.get_instance(instance_dest_name)
        interface_dest = instance_dest.getInterface(interface_dest_name)
        port_dest = interface_dest.getPort(port_dest_name)

        port_source.connect_port(port_dest)
        self.save()

    def connect_interface(self, instance_name1, interface_name1,
                          instance_name2, interface_name2):
        """ Connect an interface between two components
        """
        instance_src = self.get_instance(instance_name1)
        interface_src = instance_src.getInterface(interface_name1)
        instance_dest = self.get_instance(instance_name2)
        interface_dest = instance_dest.getInterface(interface_name2)
        interface_src.connect_interface(interface_dest)
        self.save()

    def connect_bus(self, instancemaster, interfacemaster,
                    instanceslave, interfaceslave):
        """ Connect a master bus to a slave bus
        """
        instance = self.get_instance(instancemaster)
        instance.connect_bus(interfacemaster,
                             self.get_instance(instanceslave),
                             interfaceslave)
        self.save()

    def del_bus(self, instancemaster, instanceslave,
                interfacemaster=None, interfaceslave=None):
        """ Delete a slave bus connection
        """
        instance = self.get_instance(instancemaster)
        instance.del_bus(instanceslave, interfacemaster, interfaceslave)
        self.save()

    def reorder_instances(self, componentname):
        """ Renum all instances in the correct order """
        complist = []
        for comp in self._instanceslist:
            if comp.getName() == componentname:
                complist.append(comp)
        num = 0
        for comp in complist:
            comp.setNum(num)
            num = num + 1
        self.save()

    def auto_connect_busses(self):
        """ autoconnect busses """
        masters = self.interfaces_master
        # autoconnection can be made only if they are 1 master interface
        if len(masters) < 1:
            raise Error("No bus master in project", 0)
        elif len(masters) > 1:
            for i in range(len(masters) - 1):
                for j in range(i + 1, len(masters)):
                    if (masters[i].getBusName() == masters[j].getBusName()):
                        raise Error(masters[i].getParent().getInstanceName() +
                                    " and " +
                                    masters[j].getParent().getInstanceName() +
                                    " has the same bus type : , " +
                                    masters[i].getBusName() +
                                    " bus connection must be made by hand", 0)
        # find slaves bus
        slaves = self.interfaces_slave
        if len(slaves) == 0:
            raise Error(" No slave bus in project", 0)

        # connect each slave with the same bus name than master
        for master in masters:
            for interfaceslave in slaves:
                if interfaceslave.getBusName() == master.getBusName():
                    try:
                        # connect bus
                        master.connect_bus(interfaceslave.getParent(),
                                           interfaceslave.getName())
                    except Error, error:
                        error.setLevel(2)
                        DISPLAY.msg(str(error))

        DISPLAY.msg("Bus connected")
        self.save()

    def check(self):
        """ This function check all the project wiring
        """

        ##########################################
        # Check connections on variable ports
        for port in self.variable_ports:
            if port.checkVariablePort() is False:
                raise Error(
                    "Pin connections on port " +
                    str(port.getParent().getParent().getInstanceName()) +
                    "." + str(port.getParent().getName()) + "." +
                    str(port.getName()) +
                    "is wrong, pin number must be followed.")

        ###########################################
        # check Busses, all slaves bus need a master
        listmaster = self.interfaces_master
        listslave = self.interfaces_slave

        # Delete all slaves component from listslave
        for master in listmaster:
            for slave in master.getSlavesList():
                for slave2 in listslave:
                    if slave2.getParent().getInstanceName() ==\
                        slave.getInstanceName() and \
                            slave2.getName() == slave.getInterfaceName():
                        listslave.remove(slave2)

        for slave in listslave:
            DISPLAY.msg(slave.getParent().getInstanceName() +
                        " is not connected on a master bus", 1)
        if len(listslave) != 0:
            DISPLAY.msg("Some slave bus are not connected", 1)

        ##########################################
        # Check bus address
        dict_reg = {}
        newmaster = []
        for master in listmaster:
            if (master.getName() != "candroutput"):
                newmaster.append(master)
        for master in newmaster:
            for slave in master.getSlavesList():
                for register in slave.getInterface().getRegisterMap():
                    if register["offset"] in dict_reg:
                        DISPLAY.msg(
                            "Register conflict at " +
                            hex(register["offset"]) + " between " +
                            str(slave.getInstanceName()) + "." +
                            str(register["name"]) + " and " +
                            str(dict_reg[register["offset"]][0]) + "." +
                            str(dict_reg[register["offset"]][1]), 0)
                        dict_reg[register["offset"]] =\
                            (str(dict_reg[register["offset"]][0]) + "," +
                             slave.getInstanceName() + "/!\\",
                             str(dict_reg[register["offset"]][1]) + "," +
                             register["name"] + "/!\\")
                    else:
                        dict_reg[register["offset"]] =\
                            (slave.getInstanceName(), register["name"])
            DISPLAY.msg("")
            DISPLAY.msg("Mapping for interface " + master.getName() + ":")
            DISPLAY.msg("Address  | instance.interface             |" +
                        " size        ")
            DISPLAY.msg("-----------------------------" +
                        "----------------------------")
            for register in master.allocMem.getMapping():
                DISPLAY.msg("%8s" % register[0] + " | " +
                            "%30s" % register[1] +
                            " | " + "%10s" % register[2])
            DISPLAY.msg("----------------------------" +
                        "-----------------------------")

    @classmethod
    def get_simulation_toolchains(cls):
        """ list all toolchain availables """
        filelist = sy.listDirectory(SETTINGS.path +
                                    TOOLCHAINPATH + SIMULATIONPATH)
        return filelist

    @classmethod
    def get_synthesis_toolchains(cls):
        """ list all toolchains availables """
        filelist = sy.listDirectory(SETTINGS.path +
                                    TOOLCHAINPATH + SYNTHESISPATH)
        return filelist

    @classmethod
    def get_driver_toolchains(cls):
        """ list all toolchains availables """
        filelist = sy.listDirectory(SETTINGS.path +
                                    TOOLCHAINPATH + DRIVERSPATH)
        return filelist

    def get_ios(self):
        """ return a list of IOs avaiable in platform """
        platform = self.platform
        return platform.getInterfacesList()[0].ports

    def get_io(self, io_name):
        """ return IO with io_name given """
        for an_io in self.get_ios():
            if an_io.getName() == io_name:
                return an_io
        raise Error("No IO with name " + str(io_name))

    def get_components_versions(self, libraryname, componentname):
        """ list component version name in archive
        """
        filelist = sy.listFiles(self.library.getLibraryPath(libraryname) +
                                "/" + componentname)
        outlist = []
        for name in filelist:
            # take only xml file
            ext = XMLEXT[1:]  # suppress dot
            pattern = ".*%s" % ext + "$"
            if re.match(pattern, name):
                # Suppress extension
                name = name.split(".")[0]
                outlist.append(name)
        return outlist

    def generate_report(self, filename=None):
        """ generate a project report """
        if filename is None:
            report_file = open(SETTINGS.projectpath +
                               "/" + self.getName() +
                               "_report.txt", "w")
        else:
            report_file = open(filename, "w")
        text = "* Master interfaces mapping:\n"
        for master in self.interfaces_master:
            masterinstance = master.getParent()
            text += "\n  " + masterinstance.getInstanceName() + "." +\
                    master.getName() + ":\n"
            for slave in master.getSlavesList():
                interfaceslave = slave.getInterface()
                instance = interfaceslave.getParent()
                text += ONETAB + instance.getInstanceName() +\
                    "." + interfaceslave.getName() + ":\n"
                try:
                    for reg in interfaceslave.getRegisterMap():
                        text += ONETAB + "  " +\
                            "0x%02x : %s\n" % (reg["offset"], reg["name"])
                except Error:
                    text += "\n"
        report_file.write(text)
        report_file.close()
        return text
