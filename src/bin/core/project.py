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
from periphondemand.bin.utils.poderror import PodError

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

        self._library = Library(self)

        self.bspdir = None
        self.bspos = None
        if not self.void:
            if projectpathname.find(XMLEXT) >= 0:
                try:
                    self._projectpath =\
                        os.path.abspath(os.path.dirname(projectpathname))
                except IOError, error:
                    raise PodError(str(error), 0)
            else:
                self._projectpath = projectpathname
            SETTINGS.projectpath = self.projectpath
            SETTINGS.author = ""
            SETTINGS.active_project = self
            name = os.path.basename(projectpathname)
            if sy.file_exist(projectpathname):
                self.load_project(projectpathname)
            else:
                self.create_project(name)
            self.description = description

            SETTINGS.active_project = self

    def create_project(self, name):
        """ Create a project """
        if sy.dir_exist(self.projectpath):
            raise PodError("Can't create project, directory " +
                           self.projectpath +
                           " already exists", 0)
        sy.mkdir(self.projectpath)

        sy.mkdir(self.projectpath + BINARYPROJECTPATH)
        sy.mkdir(self.projectpath + COMPONENTSPATH)
        sy.mkdir(self.projectpath + OBJSPATH)

        sy.mkdir(self.projectpath + SIMULATIONPATH)
        sy.mkdir(self.projectpath + SYNTHESISPATH)
        sy.mkdir(self.projectpath + DRIVERSPATH)

        self.create_xml("project")
        self.name = name
        self.version = "1.0"
        self.void = 0
        self.save()

    def load_project(self, pathname):
        """ Load the  project
        """
        self.open_xml(pathname)
        components = self.get_node("components")
        # load components
        if(components):
            for node in components.get_nodes("component"):
                if node.get_attr_value("platform") is None:
                    comp = Component(self)
                else:
                    comp = Platform(self, node=self.get_node("platform"))
                try:
                    comp.load(node.get_attr_value("name"))
                except IOError:
                    self.del_subnode("components",
                                     "component",
                                     "name", node.get_attr_value("name"))
                    raise PodError("Can't open " +
                                   node.get_attr_value("name") +
                                   " directory", 0)
                else:
                    self._instanceslist.append(comp)

        # load toolchains
        # toolchains = self.get_node("toolchain")
        # if(toolchains):
        #       node = toolchains.get_node("simulation")
        #       if node!=None:
        #           self.simulation = Simulation(self, node.name)
        #       node = toolchains.get_node("synthesis")
        #       if node!=None:
        #           self.synthesis = Synthesis(self, node.name)
        try:
            self.synthesis = Synthesis(self)
        except PodError, error:
            DISPLAY.msg(str(error))
        try:
            self.simulation = Simulation(self)
        except PodError, error:
            DISPLAY.msg(str(error))

        # Set bus master-slave
        for masterinterface in self.interfaces_master:
            for slave in masterinterface.slaves:
                slaveinterface = slave.get_interface()
                masterinterface.alloc_mem.add_slave_interface(slaveinterface)
                slaveinterface.master = masterinterface

        # set bsp directory
        if self.get_node(nodename="bsp") is not None:
            self.bspdir = self.get_node(
                nodename="bsp").get_attr_value("directory")
        self.void = 0

    @property
    def library(self):
        """ Get library """
        return self._library

    @property
    def projectpath(self):
        """ Get projectpath directory name """
        return self._projectpath

    @property
    def synthesis_toolchain(self):
        """ Get synthesis toolchain """
        return self.synthesis

    @synthesis_toolchain.setter
    def synthesis_toolchain(self, toolchainname):
        """ Set the synthesis toolchain """
        if toolchainname not in self.get_synthesis_toolchains():
            raise PodError("No toolchain named " + toolchainname + " in POD")
        sy.cp_file(SETTINGS.path + TOOLCHAINPATH + SYNTHESISPATH +
                   "/" + toolchainname + "/" + toolchainname + XMLEXT,
                   self.projectpath + SYNTHESISPATH + "/")
        sy.rename_file(self.projectpath + SYNTHESISPATH +
                       "/" + toolchainname + XMLEXT,
                       self.projectpath + SYNTHESISPATH +
                       "/synthesis" + XMLEXT)
        self.synthesis = Synthesis(self)
        self.save()

    @property
    def fpga_speed_grade(self):
        """ Get FPGA speedgrade """
        return self.platform.speed

    @fpga_speed_grade.setter
    def fpga_speed_grade(self, speed):
        """ Set FPGA speedgrade """
        self.platform.speed = speed
        self.save()

    @property
    def fpga_device(self):
        """ get fpgadevice """
        return self.platform.device

    @fpga_device.setter
    def fpga_device(self, device):
        """ set fpga device """
        self.platform.device = device
        self.save()

    @property
    def simulation_toolchain(self):
        """ get simulation toolchain """
        return self.simulation

    @simulation_toolchain.setter
    def simulation_toolchain(self, toolchainname):
        """ Set simulation toolchain """
        if toolchainname not in self.get_simulation_toolchains():
            raise PodError("No toolchain named " + toolchainname + " in POD")
        sy.cp_file(SETTINGS.path + TOOLCHAINPATH + SIMULATIONPATH +
                   "/" + toolchainname + "/" + toolchainname + XMLEXT,
                   self.projectpath + SIMULATIONPATH + "/")
        sy.rename_file(self.projectpath + SIMULATIONPATH +
                       "/" + toolchainname + XMLEXT,
                       self.projectpath + SIMULATIONPATH +
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
            raise PodError("No toolchain named " + toolchainname + " in POD")
        sy.cp_file(SETTINGS.path + TOOLCHAINPATH + DRIVERSPATH +
                   "/" + toolchainname + "/" + toolchainname + XMLEXT,
                   self.projectpath + DRIVERSPATH + "/")
        sy.rename_file(self.projectpath + DRIVERSPATH +
                       "/" + toolchainname + XMLEXT,
                       self.projectpath + DRIVERSPATH +
                       "/drivers" + XMLEXT)
        self.driver = Driver(self)
        self.save()

    def set_unconnected_value(self, portdict, value):
        """ Set port unconnected value
            portdict = {"instance":"name", "interface":"name", "port":name"}
        """
        instance = self.get_instance(portdict["instance"])
        interface = instance.get_interface(portdict["interface"])
        port = interface.get_port(portdict["port"])
        port.set_unconnected_value(value)
        self.save()

    def set_force(self, portname, state):
        """ May the force be with you """
        platform = self.platform
        interfaces_list = platform.interfaces
        if len(interfaces_list) != 1:
            raise PodError("I found " + str(len(interfaces_list)) +
                           " FPGAs (" + str(interfaces_list) +
                           ") and multiple FPGA project " +
                           "is not implemented yet.")
        port = interfaces_list[0].get_port(portname)
        if port.direction == "in":
            raise PodError("The value of this port can't be set " +
                           "because of it's direction (in)")
        port.force = state
        self.save()

    @property
    def forced_ports(self):
        """ List FPGA forced FPGA pin """
        platform = self.platform
        return platform.forces

    @property
    def vhdl_version(self):
        """ get vhdl version (VHDL '87 or '93) """
        return self._vhdl_version

    @vhdl_version.setter
    def vhdl_version(self, version):
        """ select vhdl version (VHDL '87 or '93) """
        if (version != "vhdl93") and (version != "vhdl87"):
            raise PodError(str(version) + " is not acceptable version")
        self._vhdl_version = version
        self.save()

    def add_component_lib(self, path):
        """ Adding a component library under the project """
        if sy.dir_exist(path):
            # TODO: adding node management in Library add_library() method
            if self.get_node("componentslibs") is None:
                self.add_node(nodename="componentslibs")
            self.add_subnode(nodename="componentslibs",
                             subnodename="componentslib",
                             attributename="path",
                             value=path)
            self.library.add_library(path)
            self.save()
        else:
            raise PodError("ComponentsLib directory " +
                           str(path) + " doesn't exists")

    def add_platforms_lib(self, path):
        """ Adding a platforms library under the project """
        if sy.dir_exist(path):
            if self.get_node("platformlibs") is None:
                self.add_node(nodename="platformlibs")
            self.add_subnode(nodename="platformlibs",
                             subnodename="platformlib",
                             attributename="path",
                             value=path)
            self.save()
        else:
            raise PodError("ComponentsLib directory " + str(path) +
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
            instancename = comp.instancename
        elif ("componentname" in keys) and ("libraryname" in keys):
            componentname = keys["componentname"]
            libraryname = keys["libraryname"]
            if "instancename" in keys:
                instancename = keys["instancename"]
                # check if instancename is not <componentname><number><number>
                if re.match(r'^' + componentname + r'\d{2}$', instancename):
                    raise PodError("Instance name forbiden, " +
                                   "it's reserved for " +
                                   "automatic instance name generation :" +
                                   instancename, 0)
                # check instance availability
                for instance in self.instances:
                    if instance.name == instancename:
                        raise PodError("This instance name already exists", 0)
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
                raise PodError("Instance name can't be the" +
                               "same as component name", 0)
            comp = Component(self)
            comp.load_new_instance(libraryname, componentname,
                                   componentversion, instancename)
            comp.num = str(len(
                self.get_instances_list_of_component(componentname)))
        else:
            raise PodError("Key not known in add_instance", 0)

        # Add component to project
        self._instanceslist.append(comp)
        if comp.is_platform() is False:
            self.add_subnode(nodename="components",
                             subnodename="component",
                             attributename="name",
                             value=instancename)
        else:
            attrib = {"name": instancename, "platform": "true"}
            self.add_subnode(nodename="components",
                             subnodename="component",
                             attributedict=attrib)
        DISPLAY.msg("Component " + comp.name + " added as " + instancename)
        self.save()

    @property
    def interfaces_master(self):
        """ Return a list of master interface
        """
        interfacelist = []
        for instance in self.instances:
            for interface in instance.interfaces:
                if interface.interface_class == "master":
                    interfacelist.append(interface)
        return interfacelist

    @property
    def interfaces_slave(self):
        """ Return a list of slave interface
        """
        interfacelist = []
        for instance in self.instances:
            for interface in instance.interfaces:
                if interface.interface_class == "slave":
                    interfacelist.append(interface)
        return interfacelist

    def get_instance(self, instancename=None):
        """ Return the instance by name
        """
        for instance in self.instances:
            if instance.instancename == instancename:
                return instance
        raise PodError("Instance " + instancename + " doesn't exists")

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
            for interface in instance.interfaces:
                for port in interface.ports:
                    ports_list.append(port)
        return ports_list

    def get_instances_list_of_component(self, componentname):
        """ return a list of instances for a componentname """
        listinstance = []
        for instance in self.instances:
            if instance.name == componentname:
                listinstance.append(instance)
        return listinstance

    @property
    def platform(self):
        """ return component instance platform
        """
        for instance in self.instances:
            if instance.is_platform() is True:
                return instance
        raise PodError("No platform in project", 1)

    @property
    def platform_name(self):
        """ return platform name """
        return self.get_node("platform").get_attr_value("name")

    @property
    def clock_ports(self):
        """ return a list of external clock port
        """
        # looking for port connected to platform
        # with type="CLK" and "in" direction
        portlist = []
        platformname = self.platform.instancename
        for instance in self.instances:
            if not instance.is_platform():
                for interface in instance.interfaces:
                    for port in interface.ports:
                        if (port.direction == "in") and \
                            (port.size == "1") and \
                                (port.porttype == "CLK"):
                            for pin in port.pins:
                                if len(pin.connections) == 1:
                                    connection = pin.connections[0]
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
        except PodError, error:
            if error.level < 2:
                raise error
            print error

        if platformlibname == "standard":
            platformdir = SETTINGS.path + PLATFORMPATH +\
                "/" + platformname + "/"
        else:
            # if not standard platform, try personnal platform
            try:
                platformdir = SETTINGS.get_platform_lib_path(platformlibname) +\
                    "/" + platformname + "/"
            except TypeError:
                # if not personnal platform, try project specific
                # platform (added with add_platforms_lib cmd)
                platformdir = ""
                for node in self.get_subnodes("platformlibs", "platformlib"):
                    apath = node.get_attr_value("path")
                    if apath.split("/")[-1] == platformlibname:
                        platformdir = apath + "/" + platformname + "/"
                if platformdir == "":
                    raise PodError("Platform name error")
        platform = Platform(self, file=platformdir + platformname + XMLEXT)

        if sy.file_exist(platformdir + SIMULATIONPATH):
            sy.copy_all_files(platformdir + SIMULATIONPATH,
                              self.projectpath + SIMULATIONPATH)
        self.add_instance(component=platform)
        self.add_node(node=platform)
        # Adding platform default components
        for component in platform.components:
            self.add_instance(libraryname=component["type"],
                              componentname=component["name"])
        self.save()

    def del_platform(self):
        """ Suppress platform from project
        """
        # find platform in components list
        try:
            platform = self.platform
        except PodError:
            raise PodError("No platform in project", 2)

        self.del_instance(platform.instancename)
        self.del_node("platform")
        self.save()

    @classmethod
    def availables_plat(cls):
        """ List all supported platforms names
        """
        platformlist = sy.list_dir(SETTINGS.path + PLATFORMPATH)
        return platformlist

    def del_instance(self, instancename):
        """ Remove instance from project
        """
        instance = self.get_instance(instancename)
        # remove pins connections from project instances to this instancename
        for interface in instance.interfaces:
            for port in interface.ports:
                for pin in port.pins:
                    pin.del_connections()
        # remove busses connections from project instances to this instancename
        for comp in self.instances:
            if comp.name != "platform":
                comp.del_bus(instanceslavename=instancename)
        # Remove components from project
        self._instanceslist.remove(instance)
        self.reorder_instances(instance.name)
        self.del_subnode("components",
                         "component",
                         "name",
                         instance.instancename)
        instance.del_instance()
        DISPLAY.msg("Component " + instancename + " deleted")
        self.save()

    def save(self):
        """ Save the project """
        for comp in self._instanceslist:
            comp.save()
        if self.synthesis is not None:
            self.synthesis.save()
        if self.simulation is not None:
            self.simulation.save()
        self.save_xml(self.projectpath + "/" + self.name + XMLEXT)

    def connect_pin_cmd(self, pin_source, pin_dest):
        """ connect pin between two instances
        """
        if pin_source.parent.parent.is_bus():
            raise PodError("One of this pin is under a bus interface." +
                           "Please use connectbus.")
        if pin_dest.parent.parent.is_bus():
            raise PodError("One of this pin is under a bus interface." +
                           "Please use connectbus.")
        if int(pin_source.parent.size)-1 < int(pin_source.get_attr_value("num")):
            raise PodError("Pin source number is greater than port size")
        if int(pin_dest.parent.size)-1 < int(pin_dest.get_attr_value("num")):
            raise PodError("Pin dest number is greater than port size")
        pin_source.connect_pin(pin_dest)
        self.save()

    def delete_pin_connection_cmd(self, sourcedict, destdict):
        """ delete pin between two instances
            sourcedict = {"instance":"name", "interface":name,
                            "port":"name", "num":"num"}
            destdict =  {"instance":"name", "interface":name,
                            "port":"name", "num":"num"}
        """
        instance_source = self.get_instance(sourcedict["instance"])
        interface_source =\
            instance_source.get_interface(sourcedict["interface"])
        port_source = interface_source.get_port(sourcedict["port"])
        if sourcedict["num"] is None:
            if(port_source.size) == 1:
                sourcedict["num"] = "0"
            else:
                raise PodError("Source pin number not given, " +
                               "and port size > 1")
        pin_source = port_source.get_pin(sourcedict["num"])

        # test if destination given
        if (destdict["instance"] is not None) and\
           (destdict["interface"] is not None) and\
           (destdict["port"] is not None) and\
           (destdict["num"] is not None):
            instance_dest = self.get_instance(destdict["instance"])
            interface_dest = instance_dest.get_interface(destdict["interface"])
            port_dest = interface_dest.get_port(destdict["port"])
            pin_dest = port_dest.get_pin(destdict["num"])

            pin_source.del_connection(pin_dest)
            pin_dest.del_connection(pin_source)
            # if only instance_source given,
        else:  # delete all connection from this instance_source
            for connection in pin_source.connections:
                instance_dest = self.get_instance(connection["instance_dest"])
                interface_dest =\
                    instance_dest.get_interface(connection["interface_dest"])
                port_dest = interface_dest.get_port(connection["port_dest"])
                pin_dest = port_dest.get_pin(connection["pin_dest"])

                pin_source.del_connection(pin_dest)
                pin_dest.del_connection(pin_source)
        self.save()

    def generate_intercon(self, interfacedict):
        """ generate intercon for interface interface_name """
        # test if intercon already exists
        from periphondemand.bin.code.intercon import Intercon
        try:
            intercon = self.get_instance(interfacedict["instance"] + "_" +
                                         interfacedict["interface"] +
                                         "_intercon")
        except PodError:
            pass
        else:
            self.del_instance(intercon.instancename)

        instance = self.get_instance(interfacedict["instance"])
        interface = instance.get_interface(interfacedict["interface"])
        intercon = Intercon(self, interface)
        self.add_instance(component=intercon)
        self.save()

    def connect_port(self, sourcedict, destdict):
        """ Connect all pins of a port source on all pins of
            port dest
            sourcedict = {"instance": "name", "interface": "name",
                          "port": "name"}
            destdict = {"instance": "name", "interface": "name",
                        "port": "name"}
        """
        instance_source = self.get_instance(sourcedict["instance"])
        interface_source =\
            instance_source.get_interface(sourcedict["interface"])
        port_source = interface_source.get_port(sourcedict["port"])

        instance_dest = self.get_instance(destdict["instance"])
        interface_dest = instance_dest.get_interface(destdict["interface"])
        port_dest = interface_dest.get_port(destdict["port"])

        port_source.connect_port(port_dest)
        self.save()

    def connect_interface(self, sourcedict, destdict):
        """ Connect an interface between two components
        """
        instance_src = self.get_instance(sourcedict["instance"])
        interface_src = instance_src.get_interface(sourcedict["interface"])
        instance_dest = self.get_instance(destdict["instance"])
        interface_dest = instance_dest.get_interface(destdict["interface"])
        interface_src.connect_interface(interface_dest)
        self.save()

    def connect_bus(self, masterdict, slavedict):
        """ Connect a master bus to a slave bus
        """
        instance = self.get_instance(masterdict["instance"])
        instance.connect_bus(masterdict["interface"],
                             self.get_instance(slavedict["instance"]),
                             slavedict["interface"])
        self.save()

    def del_bus(self, masterdict, slavedict):
        """ Delete a slave bus connection
        """
        instance = self.get_instance(masterdict["instance"])
        instance.del_bus(slavedict["instance"],
                         masterdict["interface"],
                         slavedict["interface"])
        self.save()

    def reorder_instances(self, componentname):
        """ Renum all instances in the correct order """
        complist = []
        for comp in self._instanceslist:
            if comp.name == componentname:
                complist.append(comp)
        num = 0
        for comp in complist:
            comp.num = num
            num = num + 1
        self.save()

    def auto_connect_busses(self):
        """ autoconnect busses """
        masters = self.interfaces_master
        # autoconnection can be made only if they are 1 master interface
        if len(masters) < 1:
            raise PodError("No bus master in project", 0)
        elif len(masters) > 1:
            for i in range(len(masters) - 1):
                for j in range(i + 1, len(masters)):
                    if (masters[i].bus_name == masters[j].bus_name):
                        raise PodError(masters[i].parent.instancename +
                                       " and " +
                                       masters[j].parent.instancename +
                                       " has the same bus type : , " +
                                       masters[i].bus_name +
                                       " bus connection " +
                                       "must be made by hand", 0)
        # find slaves bus
        slaves = self.interfaces_slave
        if len(slaves) == 0:
            raise PodError(" No slave bus in project", 0)

        # connect each slave with the same bus name than master
        for master in masters:
            for interfaceslave in slaves:
                if interfaceslave.bus_name == master.bus_name:
                    try:
                        # connect bus
                        master.connect_bus(interfaceslave.parent,
                                           interfaceslave.name)
                    except PodError, error:
                        error.level = 2
                        DISPLAY.msg(str(error))

        DISPLAY.msg("Bus connected")
        self.save()

    def check(self):
        """ This function check all the project wiring
        """

        ##########################################
        # Check connections on variable ports
        for port in self.variable_ports:
            if port.check_variable_port() is False:
                raise PodError(
                    "Pin connections on port " +
                    str(port.parent.parent.instancename) +
                    "." + str(port.parent.name) + "." +
                    str(port.name) +
                    "is wrong, pin number must be followed.")

        ###########################################
        # check Busses, all slaves bus need a master
        listmaster = self.interfaces_master
        listslave = self.interfaces_slave

        # Delete all slaves component from listslave
        for master in listmaster:
            for slave in master.slaves:
                for slave2 in listslave:
                    if slave2.parent.instancename ==\
                        slave.instancename and \
                            slave2.name == slave.interfacename:
                        listslave.remove(slave2)

        for slave in listslave:
            DISPLAY.msg(slave.parent.instancename +
                        " is not connected on a master bus", 1)
        if len(listslave) != 0:
            DISPLAY.msg("Some slave bus are not connected", 1)

        ##########################################
        # Check bus address
        dict_reg = {}
        newmaster = []
        for master in listmaster:
            if (master.name != "candroutput"):
                newmaster.append(master)
        for master in newmaster:
            for slave in master.slaves:
                for register in slave.get_interface().registers_map:
                    if register["offset"] in dict_reg:
                        DISPLAY.msg(
                            "Register conflict at " +
                            hex(register["offset"]) + " between " +
                            str(slave.instancename) + "." +
                            str(register["name"]) + " and " +
                            str(dict_reg[register["offset"]][0]) + "." +
                            str(dict_reg[register["offset"]][1]), 0)
                        dict_reg[register["offset"]] =\
                            (str(dict_reg[register["offset"]][0]) + "," +
                             slave.instancename + "/!\\",
                             str(dict_reg[register["offset"]][1]) + "," +
                             register["name"] + "/!\\")
                    else:
                        dict_reg[register["offset"]] =\
                            (slave.instancename, register["name"])
            DISPLAY.msg("")
            DISPLAY.msg("Mapping for interface " + master.name + ":")
            DISPLAY.msg("Address  | instance.interface             |" +
                        " size        ")
            DISPLAY.msg("-----------------------------" +
                        "----------------------------")
            for register in master.alloc_mem.mapping:
                DISPLAY.msg("%8s" % register[0] + " | " +
                            "%30s" % register[1] +
                            " | " + "%10s" % register[2])
            DISPLAY.msg("----------------------------" +
                        "-----------------------------")

    @classmethod
    def get_simulation_toolchains(cls):
        """ list all toolchain availables """
        filelist = sy.list_dir(SETTINGS.path +
                               TOOLCHAINPATH + SIMULATIONPATH)
        return filelist

    @classmethod
    def get_synthesis_toolchains(cls):
        """ list all toolchains availables """
        filelist = sy.list_dir(SETTINGS.path +
                               TOOLCHAINPATH + SYNTHESISPATH)
        return filelist

    @classmethod
    def get_driver_toolchains(cls):
        """ list all toolchains availables """
        filelist = sy.list_dir(SETTINGS.path +
                               TOOLCHAINPATH + DRIVERSPATH)
        return filelist

    def get_ios(self):
        """ return a list of IOs avaiable in platform """
        platform = self.platform
        return platform.interfaces[0].ports

    def get_io(self, io_name):
        """ return IO with io_name given """
        for an_io in self.get_ios():
            if an_io.name == io_name:
                return an_io
        raise PodError("No IO with name " + str(io_name))

    def get_components_versions(self, libraryname, componentname):
        """ list component version name in archive
        """
        filelist = sy.list_files(self.library.library_path(libraryname) +
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
            report_file = open(self.projectpath +
                               "/" + self.name +
                               "_report.txt", "w")
        else:
            report_file = open(filename, "w")
        text = "* Master interfaces mapping:\n"
        for master in self.interfaces_master:
            masterinstance = master.parent
            text += "\n  " + masterinstance.instancename + "." +\
                    master.name + ":\n"
            for slave in master.slaves:
                interfaceslave = slave.get_interface()
                instance = interfaceslave.parent
                text += ONETAB + instance.instancename +\
                    "." + interfaceslave.name + ":\n"
                try:
                    for reg in interfaceslave.registers_map:
                        text += ONETAB + "  " +\
                            "0x%02x : %s\n" % (reg["offset"], reg["name"])
                except PodError:
                    text += "\n"
        report_file.write(text)
        report_file.close()
        return text
