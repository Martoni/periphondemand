#! /usr/bin/python3
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

from periphondemand.bin.define import COMPONENTSPATH
from periphondemand.bin.define import XMLEXT

from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.display import Display

from periphondemand.bin.core.interface import Interface
from periphondemand.bin.core.hdl_file import HdlFile
from periphondemand.bin.core.driver_templates import DriverTemplates
from periphondemand.bin.core.generic import Generic

SETTINGS = Settings()
DISPLAY = Display()


class Component(WrapperXml):
    """Manage components

    attributes:
        _interfaceslist -- list of interfaces
        _genericslist   -- list of generics

    """

    def __init__(self, parent, node=None, afile=None):
        """ Init Component,
            __init__(self)
        """

        if node is not None:
            WrapperXml.__init__(self, node=node)
        elif afile is not None:
            WrapperXml.__init__(self, file=afile)
        else:
            WrapperXml.__init__(self, nodename="void")

        self._interfaceslist = []
        self._genericslist = []
        self._hdl_fileslist = []
        self._driver_templateslist = []
        self._interruptslist = []
        self._constraintslist = []

        # Project that use the component
        self.parent = parent
        self.void = 0

    def load_new_instance(self, libraryname, componentname,
                          componentversion, instancename):
        """ Load a new component from library
        """
        project = self.parent
        # verify component name
        if project.name == instancename:
            raise PodError("Instance name can't be " +
                           "the same name as projectname", 0)
        # test if component exist
        if not sy.file_exist(project.library.library_path(libraryname) +
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
        sy.cp_dir(project.library.library_path(libraryname) +
                  "/" + componentname,
                  self.parent.projectpath + COMPONENTSPATH)
        try:
            sy.rename_dir(self.parent.projectpath +
                          COMPONENTSPATH + "/" + componentname,
                          self.parent.projectpath + COMPONENTSPATH +
                          "/" + instancename)
        except PodError:  # if directory exist
            pass

        # Rename xml file
        sy.rename_file(self.parent.projectpath +
                       COMPONENTSPATH + "/" + instancename +
                       "/" + componentversion + XMLEXT,
                       self.parent.projectpath + COMPONENTSPATH +
                       "/" + instancename + "/" + instancename + XMLEXT)

        # load component
        self.load(instancename)
        # Connect platform connection
        self.autoconnect_pins()

    def load(self, instancename):
        """ Load an instance from project directory
        """
        # load xml file
        WrapperXml.__init__(self, file=self.parent.projectpath +
                            COMPONENTSPATH + "/" + instancename +
                            "/" + instancename + XMLEXT)

        # Fill objects list
        if self.get_node("interfaces") is not None:
            for element in self.get_subnodes("interfaces", "interface"):
                self._interfaceslist.append(Interface(self, node=element))

        if self.get_node("generics") is not None:
            for element in self.get_subnodes("generics", "generic"):
                self._genericslist.append(Generic(self, node=element))

        if self.get_node("hdl_files") is not None:
            for element in self.get_subnodes("hdl_files", "hdl_file"):
                self._hdl_fileslist.append(HdlFile(self, node=element))

        if self.get_node("driver_files") is not None:
            for element in\
                    self.get_subnodes("driver_files", "driver_templates"):
                self._driver_templateslist.append(
                    DriverTemplates(self, node=element))

        if self.get_node("interrupts") is not None:
            for element in self.get_subnodes("interrupts", "interrupt"):
                self._interruptslist.append(
                    self.get_interface(
                        element.get_attr_value("interface")).get_port(
                            element.get_attr_value("port")))

        if self.get_node("constraints") is not None:
            for element in self.get_subnodes("constraints", "constraint"):
                self._constraintslist.append(element)

        self.instancename = instancename

    @property
    def constraints(self):
        """ Get list of constraints """
        return self._constraintslist

    def autoconnect_pins(self):
        """ Auto connect platform default pins
        """
        for interface in self.interfaces:
            interface.autoconnect_pins()

    @property
    def hdl_files(self):
        """ Get list of HDL files """
        return self._hdl_fileslist

    def get_hdl_top(self):
        """ Get hdl top file """
        for hdlfile in self.hdl_files:
            if hdlfile.istop():
                return hdlfile
        return None

    def get_hdl(self, filename):
        """ get hdl file """
        for hdlfile in self.hdl_files:
            if hdlfile.filename == filename:
                return hdlfile
        raise PodError("no hdl file named " + filename)

    def add_hdl_file(self, hdl_file):
        """ add hdl file """
        self.add_subnode(nodename="hdl_files", subnode=hdl_file)
        return self._hdl_fileslist.append(hdl_file)

    @property
    def interrupts(self):
        """ Get interrupt list """
        return self._interruptslist

    @property
    def generics(self):
        """ Get generics parameters list """
        return self._genericslist

    @property
    def fpga_generics(self):
        """ Get fpga specifics generic list """
        fpgalist = []
        for generic in self.generics:
            if generic.destination == "fpga" or\
                    generic.destination == "both":
                fpgalist.append(generic)
        return fpgalist

    def get_generic(self, genericname):
        """ get a generic """
        for generic in self.generics:
            if generic.name == genericname:
                return generic
        raise PodError("No generic with name " + genericname, 0)

    def get_interface(self, interfacename):
        """ Get an interface by name """
        for interface in self._interfaceslist:
            if interface.name == interfacename:
                return interface
        raise PodError("Interface " + str(interfacename) +
                       " does not exists", 0)

    @property
    def master_interfaces(self):
        """ return a list of master interface """
        interfacelist = []
        for interface in self.interfaces:
            if interface.interface_class == "master":
                interfacelist.append(interface)
        return interfacelist

    @property
    def slave_interfaces(self):
        """ return a list of slave interface """
        interfacelist = []
        for interface in self.interfaces:
            if interface.interface_class == "slave":
                interfacelist.append(interface)
        return interfacelist

    def get_one_syscon(self):
        """ Get the syscon interface
            raise an error if more than one syscon
        """
        syscons = []
        for interface in self.interfaces:
            if interface.interface_class == "clk_rst":
                syscons.append(interface)
        if len(syscons) > 1:
            raise PodError("More than one (" + len(syscons) +
                           ") in the instance " + self.name)
        if syscons == []:
            return None
        return syscons[0]

    def add_interface(self, interface):
        """ Add an interface in component """
        interface.parent = self
        self._interfaceslist.append(interface)
        self.add_subnode(nodename="interfaces", subnode=interface)

    @property
    def interfaces(self):
        """ Get the list of interfaces """
        return self._interfaceslist

    @property
    def driver_templates(self):
        """ get the driver template list """
        return self._driver_templateslist

    def get_driver_template(self, architecturename):
        """ Get a driver template """
        for drivert in self.driver_templates:
            if drivert.architecture_name == architecturename:
                return drivert
        return None

    def save(self):
        """ Save component in project directory files """
        if not sy.dir_exist(self.parent.projectpath + COMPONENTSPATH +
                            "/" + self.instancename):
            sy.mkdir(self.parent.projectpath + COMPONENTSPATH +
                     "/" + self.instancename)
        self.save_xml(self.parent.projectpath + COMPONENTSPATH + "/" +
                      self.instancename + "/" +
                      self.instancename + ".xml")

    def del_instance(self):
        """ suppress component instance """
        if not self.is_platform():
            sy.rm_dir(self.parent.projectpath + COMPONENTSPATH +
                      "/" + self.instancename)

    @property
    def instancename(self):
        """ get the name of this component instance"""
        return self.get_attr_value("instance_name")

    @instancename.setter
    def instancename(self, instancename):
        """ set the name of this instance """
        return self.set_attr("instance_name", instancename)

    @classmethod
    def inv_direction(cls, dirname):
        """ invert direction given in params """
        if dirname == "in":
            return "out"
        if dirname == "out":
            return "in"
        if dirname == "inout":
            return "inout"

    def del_pin(self, instancedest, interfacedest=None, portdest=None,
                pindest=None, interfacesource=None, portsource=None,
                pinsource=None):
        """ Delete component pin connection, if only instancedest given,
            all connection towards this instance are removed
        """
        if interfacesource is None:
            for interface in self.interfaces:
                interface.del_pin(instancedest=instancedest)
        else:
            interface = self.get_interface(interfacesource)
            interface.del_pin(instancedest, interfacedest, portdest,
                              pindest, portsource, pinsource)

    def connect_bus(self, interfacemaster, instanceslave, interfaceslave):
        """ Connect an interface bus master to slave """
        interface = self.get_interface(interfacemaster)
        if interface.name is None:
            raise PodError(interfacemaster + " is not a bus", 1)
        interface.connect_bus(instanceslave, interfaceslave)

    def del_bus(self, instanceslavename, interfacemaster=None,
                interfaceslavename=None):
        """ Delete bus connection that refer to instanceslavename """
        if interfacemaster is None:
            for interface in self.interfaces:
                try:
                    interface.del_bus(instanceslavename)
                except PodError:
                    pass
        else:
            interface = self.get_interface(interfacemaster)
            interface.del_bus(instanceslavename, interfaceslavename)

    def connect_clk_domain(self, instancedestname, interfacesourcename,
                           interfacedestname):
        """ Connect clock domain """
        interface = self.get_interface(interfacesourcename)
        interface.connect_clk_domain(instancedestname, interfacedestname)

    def add_port(self, portname, interfacename):
        """ Add port named portname in interface named interfacename """
        # verify if portname exist in vhdl file
        hdltop = self.get_hdl_top()
        if not hdltop:
            raise PodError("No HDL top file in component " +
                           str(self.name))
        portlist = hdltop.ports
        if portname not in [port.name for port in portlist]:
            raise PodError("Port named " + portname + " can't be found in " +
                           hdltop.filename)

        # verify if port is not already placed
        isinfreelist, interface_old = self.port_is_in_free_list(portname)
        if isinfreelist is False:
            raise PodError("Port named " + portname +
                           " is already placed in " + interface_old)
        # take interface
        interface = self.get_interface(interfacename)
        # create port object
        port = hdltop.get_port(portname)
        # place port in interface
        interface.add_port(port)

    def port_is_in_free_list(self, portname):
        """ If port named portname is not in interface, return 1
            else return 0 and interface
        """
        interfaceslist = self.interfaces
        for interface in interfaceslist:
            portlist = interface.ports
            for port in portlist:
                if port.name == portname:
                    return (False, interface.name)
        return (True, "")

    @property
    def ports(self):
        """ return list of ports in component
            display_port = list of:
                {"interfacename":[portname1,portname2]}
        """
        display_port = {}
        tophdlfile = self.get_hdl_top()
        notassignedports = [port.name for
                            port in tophdlfile.ports]
        interfacelist = self.interfaces
        for interface in interfacelist:
            key = interface.name
            display_port[key] = []
            port_name_list = [port.name for
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

    @classmethod
    def is_platform(cls):
        """ is this component instance is a Platform ?"""
        return False

    # Settings attributes for nodes
    def set_generic(self, generic_name, attribute_name,
                    attribute_value):
        """Add or modify attribute value for a node """
        generic = self.get_generic(generic_name)
        if attribute_name == "name":
            generic.name = attribute_value
        elif attribute_name == "public":
            generic.set_public(attribute_value)
        elif attribute_name == "value":
            generic.value = attribute_value
        elif attribute_name == "match":
            generic.match = attribute_value
        elif attribute_name == "type":
            generic.setType(attribute_value)
        elif attribute_name == "destination":
            generic.destination = attribute_value
        else:
            raise PodError("Unknown attribute " + str(attribute_name))
