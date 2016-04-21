#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     TopGen.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  15/05/2008
# ----------------------------------------------------------------------------
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
# ----------------------------------------------------------------------------
""" Generate top component """

from periphondemand.bin.define import ONETAB
from periphondemand.bin.define import SYNTHESISPATH
from periphondemand.bin.define import VHDLEXT

from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.settings import Settings

import datetime

DISPLAY = Display()
SETTINGS = Settings()


class TopGen(object):
    """ Generate Top component from a project
    """

    def __init__(self, project):
        self.project = project

    @classmethod
    def file_extension(cls):
        """ return top file extension
        """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def header_template_name(cls):
        """ return template file name
        """
        raise NotImplementedError("method must be implemented", 0)

    def header(self):
        """ return header
        """
        header = open(self.header_template_name(), "r").read()
        header = header.replace("$tpl:author$", SETTINGS.author)
        header = header.replace("$tpl:date$", str(datetime.date.today()))
        header = header.replace("$tpl:filename$", "Top_" + self.project.name +
                                self.file_extension())
        header = header.replace("$tpl:abstract$",
                                self.project.description)
        return header

    def entity(self, entityname, portlist):
        """ return code for Top entity """
        raise NotImplementedError("method must be implemented", 0)

    def architecture(self, entityname, portlist, incompleteportslist):
        """ construct architecture part of the file """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def insert_comment(cls, comment):
        """ return one line comment """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def insert_comment_block(cls, indent, comment):
        """ return multi line comment """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def connect_ports(cls, srcname, destname):
        """ return port connection between to signals """
        raise NotImplementedError("method must be implemented", 0)

    def connect_inc_signals(self, srcname, destname, direction, pinnum):
        """ return incomplete connected signal """
        raise NotImplementedError("method must be implemented", 0)

    def instance_inc_sig(self, component, connect, pin):
        """ return pin connection when
            ports pins are connected individually
            to several oter ports
        """
        raise NotImplementedError("method must be implemented", 0)

    def instance_add_unc_port(self, port):
        """ return port unconnected """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def begin_component(cls, compname):
        """ return component start definition """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def end_component(cls):
        """ return component end definition """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def begin_attributes(cls):
        """ return component attribute start definition """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def end_attributes(cls):
        """ return component attribute end definition """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def insert_attribute(cls, attribute):
        """ return attribute """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def instance_begin_port(cls):
        """ return port start definition """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def instance_end_port(cls):
        """ return port end definition """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def add_scalar_sig(cls, signame, direction):
        """ return entity scalar signal definition """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def add_vector_sig(cls, signame, direction, lsb, msb):
        """ return entity scalar signal definition """
        raise NotImplementedError("method must be implemented", 0)

    def arch_add_line(self, instancename, port, direction):
        """ return signal definition """
        raise NotImplementedError("method must be implemented", 0)

    def entity_port_part(self, portlist):
        """ return code for Top entity
        """
        out = ""
        for port in portlist:
            if port.force_defined():
                portname = "force_" + port.name
                out += ONETAB * 2 + self.add_scalar_sig(portname,
                                                        "out")
            else:
                portname = port.name
                interfacename = port.parent.name
                instancename = port.parent.parent.instancename

                if port.is_hidden:
                    continue
                out += ONETAB + self.insert_comment(instancename +
                                                    "-" + interfacename)
                if port.is_fully_connected():
                    if (port.direction == "in") or (port.direction == "inout"):
                        same_connections_ports = \
                            port.ports_with_same_connection
                        if same_connections_ports == []:
                            raise PodError(str(port.extended_name) +
                                           " is left unconnected")
                        elif len(same_connections_ports) == 1:
                            signame = ONETAB * 2 + instancename + "_" + \
                                portname
                            size = port.connected_msb
                            if size < 1:
                                out += self.add_scalar_sig(signame,
                                                           port.direction)
                            else:
                                out += self.add_vector_sig(signame,
                                                           port.direction,
                                                           str(size), "0")
                        else:
                            same_connections_ports_names = \
                                sorted([aport.extended_name for
                                       aport in same_connections_ports])
                            if port.extended_name ==\
                                    same_connections_ports_names[0]:
                                signame = ONETAB * 2 + instancename + \
                                    "_" + portname
                                size = port.connected_msb
                                if size < 1:
                                    out += self.add_scalar_sig(signame,
                                                               port.direction)
                                else:
                                    out += self.add_vector_sig(signame,
                                                               port.direction,
                                                               str(size), "0")
                    else:
                        # signal declaration
                        signame = ONETAB * 2 + instancename + "_" + \
                            portname
                        size = port.connected_msb
                        if size < 1:
                            out += self.add_scalar_sig(signame,
                                                       port.direction)
                        else:
                            out += self.add_vector_sig(signame,
                                                       port.direction,
                                                       str(size), "0")
                # port not completely connected
                else:
                    for pin in port.pins:
                        if pin.is_connected_to_inst(self.project.platform):
                            out += ONETAB * 2 + \
                                self.add_scalar_sig(instancename + "_" +
                                                    port.name + "_pin" +
                                                    str(pin.num),
                                                    port.direction)
        # Suppress the #!@ last semicolon
        out = out[:-2]

        return out

    def declare_components(self):
        """ Declare components
        """
        if self.project.vhdl_version == "vhdl93":
            return ""

        out = self.insert_comment_block(ONETAB, "declare components")
        components = []
        for comp in self.project.instances:
            if comp.is_platform() is False:
                components.append(comp.name)

        # if multiple instance of the same component
        components = set(components)

        for compname in components:
            component = None
            for comp in self.project.instances:
                if comp.name == compname:
                    component = comp
                    break
            out += "\n" + ONETAB + self.begin_component(compname)
            if component.fpga_generics != []:
                out += ONETAB * 2 + self.begin_attributes()
                for generic in component.fpga_generics:
                    out += ONETAB * 3 + \
                        self.insert_attribute(generic)
                # suppress comma
                out = out[:-2] + "\n"
                out += ONETAB * 2 + self.end_attributes()

            out += ONETAB * 2 + self.instance_begin_port()
            for interface in component.interfaces:
                out += ONETAB * 3 + \
                    self.insert_comment(interface.name)
                for port in interface.ports:
                    if port.is_hidden:
                        continue
                    out += ONETAB * 3 + \
                        self.arch_add_line(port.name, port,
                                           port.direction)
            # Suppress the #!@ last semicolon
            out = out[:-2] + "\n"
            out += ONETAB * 2 + self.instance_end_port()
            out += ONETAB + self.end_component()
        return out

    def declare_signal(self, instancename, port):
        """ return signals declaration
        """
        raise NotImplementedError("method must be implemented", 0)

    def declare_signals(self, componentslist, incomplete_external_ports_list):
        """ Declare signals ports
        """
        platformname = self.project.platform.instancename

        out = self.insert_comment_block(ONETAB, "Signals declaration")
        for component in componentslist:
            if component.is_platform() is True:
                continue
            out += "\n" + ONETAB + self.insert_comment(component.instancename)
            for interface in component.interfaces:
                out += ONETAB + self.insert_comment(interface.name)

                for port in interface.ports:
                    if port.is_hidden:
                        continue
                    if port in incomplete_external_ports_list:
                        continue
                    if len(port.pins) == 0:
                        continue
                    connection_list = port.pins[0].connections
                    if len(connection_list) == 0:
                        continue
                    if connection_list[0]["instance_dest"] == platformname:
                        continue
                    instancename = component.instancename + "_" + port.name
                    out += ONETAB + \
                        self.declare_signal(instancename, port)

        out += "\n" + ONETAB + self.insert_comment("void pins")

        for port in incomplete_external_ports_list:
            if port.force_defined():
                continue
            out += "\n" + ONETAB + \
                self.declare_signal(port.parent.parent.instancename + "_" +
                                    port.name, port)
        return out

    def declare_instance(self):
        """ return instance declaration
        """
        raise NotImplementedError("method must be implemented", 0)

    def connect_in_port(self, component, interface, port):
        """ Connect all pins port"""
        platformname = self.project.platform.instancename
        out = ""
        if len(port.pins) != 0:
            if port.dest_port is not None and\
                    (port.dest_port.size == port.size):
                # If port is completely connected to one
                # and only one other port
                connect = port.pins[0].connections[0]
                if connect["instance_dest"] != platformname:
                    out += ONETAB * 2 + \
                        self.connect_ports(component.instancename +
                                           "_" + port.name,
                                           connect["instance_dest"] +
                                           "_" + connect["port_dest"])
            else:
                # If pins port are connected individualy
                # to several other ports
                for pin in port.pins:
                    # Connect pin individualy
                    if pin.num is not None and len(pin.connections) != 0:
                        connect = pin.connections[0]
                        if connect["instance_dest"] != platformname:
                            out += ONETAB * 2 + \
                                self.instance_inc_sig(component, connect, pin)
        # if port is void, connect '0' or open
        else:
            message = "port " + component.instancename + \
                "." + interface.name + "." +\
                port.name + " is void." + \
                " It will be set to '" + \
                str(port.unconnected_value) + "'"
            DISPLAY.msg(message, 2)
        return out

    @classmethod
    def instance_add_port(cls, portname, sig_name):
        """ return port connection """

    def instance_port_part(self, indent, component):
        """ Declare instance signals ports """
        out = ""
        for interface in component.interfaces:
            out += indent + self.insert_comment(interface.name)
            for port in interface.ports:
                if port.is_hidden:
                    continue
                destname = ""
                if len(port.pins) != 0:
                    if (port.direction == "inout") or\
                            (port.direction == "in"):
                        destname = sorted(
                            [aport.extended_name for aport in
                             port.ports_with_same_connection]
                            )[0]
                    else:
                        destname = port.extended_name
                    out += indent + \
                        self.instance_add_port(port.name, destname)

                else:
                    out += 3 * ONETAB + self.instance_add_unc_port(port)

        # Suppress the #!@ last comma
        out = out[:-2] + "\n"
        return out

    def connect_forces(self, portlist):
        """ Connecting Forces """

        out = "\n"
        out += self.insert_comment_block(ONETAB, "Set forces")
        for port in portlist:
            if port.is_hidden:
                continue
            if port.force_defined():
                if port.force == "gnd":
                    out += ONETAB + \
                        self.connect_ports("force_" + port.name, 0)
                else:
                    out += ONETAB + \
                        self.connect_ports("force_" + port.name, 1)
        return out

    def connect_instance(self, incomplete_external_ports_list):
        """ Connect instances
        """
        out = self.insert_comment_block(ONETAB, "instances connections")

        # connect incomplete_external_ports_list
        for port in incomplete_external_ports_list:
            if port.is_hidden:
                continue
            if not port.force_defined():
                instancename = port.parent.parent.instancename
                out += ONETAB + \
                    self.insert_comment("connect incomplete " +
                                        "external port " +
                                        str(port.name) + " pins")
                for pinnum in range(port.real_size):
                    pin = port.get_pin(pinnum)
                    if pin.is_connected_to_inst(self.project.platform):
                        basename = instancename + "_" + port.name
                        out += ONETAB + \
                            self.connect_inc_signals(basename, basename,
                                                     port.direction, pinnum)

        # connect all "in" ports pin
        for component in self.project.instances:
            if component.is_platform():
                continue
            out += "\n" + ONETAB + self.insert_comment("connect " +
                                                       component.instancename)
            for interface in component.interfaces:
                out += ONETAB * 2 + self.insert_comment(interface.name)
                for port in interface.ports:
                    if port.direction == "in":
                        out += self.connect_in_port(component, interface, port)
        return out

    def generate(self):
        """ generate code for top component
        """
        # checking if all intercons are done
        for masterinterface in self.project.interfaces_master:
            try:
                self.project.get_instance(
                    masterinterface.parent.instancename +
                    "_" +
                    masterinterface.name +
                    "_intercon")
            except PodError as error:
                raise PodError("Intercon missing, all intercon must be" +
                               "generated before generate top.\n" + str(error))

        # header
        out = self.header()
        # entity
        entityname = "top_" + self.project.name
        portlist = self.project.platform.connect_ports
        out = out + self.entity(entityname, portlist)

        # architecture
        incompleteportslist = self.project.platform.incomplete_ext_ports
        out += self.architecture(entityname, portlist, incompleteportslist)

        # save file
        try:
            top_file = open(self.project.projectpath + SYNTHESISPATH +
                            "/top_" + self.project.name + VHDLEXT, "w")
        except IOError as error:
            raise error
        top_file.write(out)
        top_file.close()
        return out
