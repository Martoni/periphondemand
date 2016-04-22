#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Driver.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  16/07/2008
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
""" Manage driver code generation """

import re

from periphondemand.bin.define import XMLEXT
from periphondemand.bin.define import DRIVERSPATH
from periphondemand.bin.define import COMPONENTSPATH
from periphondemand.bin.define import DRIVERS_TEMPLATES_PATH

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.display import Display

SETTINGS = Settings()
DISPLAY = Display()


class Driver(WrapperXml):
    """ Generate driver class """

    def __init__(self, project):
        self.project = project
        filepath = self.project.projectpath + "/" + \
            DRIVERSPATH + "/drivers" + XMLEXT
        if not sy.file_exist(filepath):
            raise PodError("No driver project found", 3)
        WrapperXml.__init__(self, file=filepath)
        self.bspdir = None

    def generate_project(self):
        """ copy template drivers files """
        project = self.project
        op_sys = self.name
        if op_sys is None:
            raise PodError("Operating system must be selected", 0)
        for component in project.instances:
            if component.num == "0":
                driver_template = component.get_driver_template(op_sys)
                if driver_template is not None:
                    if sy.dir_exist(self.project.projectpath + DRIVERSPATH +
                                    "/" + component.name):
                        DISPLAY.msg("Driver directory for " +
                                    component.name +
                                    " allready exist. suppressing it")
                        sy.rm_dir(self.project.projectpath + DRIVERSPATH +
                                  "/" + component.name)
                    DISPLAY.msg("Create directory for " +
                                component.name + " driver")
                    # create component directory
                    sy.mkdir(self.project.projectpath +
                             DRIVERSPATH + "/" +
                             component.name)
                else:
                    DISPLAY.msg("No driver for " + component.name)

    def fill_all_templates(self):
        """ fill template """
        project = self.project
        op_sys = self.name
        if op_sys is None:
            raise PodError("Operating system must be selected", 0)
        for component in project.instances:
            if component.num == "0":
                driver_template = component.get_driver_template(op_sys)
                if driver_template is not None:
                    DISPLAY.msg("Copy and fill template for " +
                                component.name)
                    for templatefile in driver_template.template_names:
                        try:
                            template = open(
                                self.project.projectpath + COMPONENTSPATH +
                                "/" + component.instancename + "/" +
                                DRIVERS_TEMPLATES_PATH + "/" +
                                op_sys + "/" +
                                templatefile, "r")
                            destfile = open(
                                self.project.projectpath + DRIVERSPATH + "/" +
                                component.name + "/" + templatefile,
                                "w")
                        except IOError as error:
                            raise PodError(str(error), 0)
                        self.fill_template(template, destfile, component)
                        template.close()
                        destfile.close()

    def fill_template_for_each_instance(self, template, component):
        """ fill template for each instance of component """
        out = ""
        for instance in\
                self.project.get_instances_list_of_component(component.name):
            for writeline in template.split("\n"):
                # instance_name
                writeline = re.sub(r'\/\*\$instance_name\$\*\/',
                                   instance.instancename.upper(),
                                   writeline)
                # instance_num
                writeline = re.sub(r'\/\*\$instance_num\$\*\/',
                                   instance.num,
                                   writeline)
                # generic:generic_name
                exp = re.compile(r'\/\*\$generic\:(.*?)\$\*\/')
                iterator = exp.finditer(writeline)
                for generic in iterator:
                    writeline = re.sub(
                        r'\/\*\$generic:' + generic.group(1) + r'\$\*\/',
                        instance.get_generic(generic.group(1)).value,
                        writeline)
                # register_base_address:interface_name
                exp = re.compile(r'\/\*\$registers_base_address:(.*?)\$\*\/')
                iterator = exp.finditer(writeline)
                for interface in iterator:
                    writeline = re.sub(
                        r'\/\*\$registers_base_address:' +
                        interface.group(1) + r'\$\*\/',
                        hex(instance.get_interface(
                            interface.group(1)).base_addr),
                        writeline)
                # register:interfacename:registername:attribute
                exp = re.compile(r'\/\*\$register:(.*?):(.*?):(.*?)\$\*\/')
                iterator = exp.finditer(writeline)
                for match in iterator:
                    attributevalue = instance.get_interface(
                        match.group(1)).get_register(
                            match.group(2)).get_attr_value(
                                match.group(3))
                    if not attributevalue:
                        raise PodError(
                            "Wrong register value -> " +
                            match.group(1) + ":" + match.group(2) +
                            ":" + match.group(3) + "\n", 0)
                    writeline = re.sub(
                        r'\/\*\$register:' + match.group(1) +
                        r':' + match.group(2) + r':' +
                        match.group(3) + r'\$\*\/',
                        attributevalue, writeline)
                # interrupt_number
                if re.search(r'\/\*\$interrupt_number\$\*\/',
                             writeline) is not None:
                    interruptlist = instance.interrupts
                    if len(interruptlist) == 0:
                        raise PodError("No interruption port in " +
                                       instance.instancename, 0)
                    elif len(interruptlist) > 1:
                        DISPLAY.msg(
                            "More than one interrupt port in " +
                            instance.instancename +
                            "." + interruptlist[0].name + " is used")
                    interruptport = interruptlist[0]

                    try:
                        connect = interruptport.get_pin(0).connections
                    except PodError:
                        raise PodError(
                            "Interrupt " + interruptport.name +
                            " not connected in " +
                            interruptport.parent.parent.instancename +
                            "." + interruptport.parent.name, 0)
                    if len(connect) == 0:
                        raise PodError("Interrupt " + interruptport.name +
                                       " is not connected", 0)
                    elif len(connect) > 1:
                        DISPLAY.msg(
                            "More than one connection for interruption port " +
                            interruptport.name + ". " +
                            connect[0]["port_dest"] + " is used")
                    writeline = re.sub(r'\/\*\$interrupt_number\$\*\/',
                                       connect[0]["pin_dest"],
                                       writeline)
                out = out + writeline + "\n"
        return out

    def fill_template(self, template, destfile, component):
        """ fill template file """
        project = self.project
        state = "STANDARD"
        foreach_template = ""

        for line in template:
            if state == "STANDARD":
                begintag = re.match(r'^\/\*\$foreach\:instance\$\*\/', line)
                if begintag is not None:
                    state = "FOREACH_INSTANCE"
                    foreach_template = ""
                    continue
                # number_of_instances
                if re.search(r'\/\*\$number_of_instances\$\*\/',
                             line) is not None:
                    instances_list =\
                        project.get_instances_list_of_component(
                            component.name)
                    line = re.sub(r'\/\*\$number_of_instances\$\*\/',
                                  str(len(instances_list)),
                                  line)
                # main clock speed
                if re.search(r'\/\*\$main_clock\$\*\/', line) is not None:
                    frequency = project.platform.main_clock
                    line = re.sub(r'\/\*\$main_clock\$\*\/', frequency, line)
                destfile.write(line)
            elif state == "FOREACH_INSTANCE":
                endtag = re.match(r'^\/\*\$foreach\:instance\:end\$\*\/', line)
                if endtag is not None:
                    state = "STANDARD"
                    destfile.write(
                        self.fill_template_for_each_instance(foreach_template,
                                                             component))
                else:
                    foreach_template = foreach_template + line
            else:
                raise PodError("State error in toolchain driver\n", 0)

    def copy_bsp_drivers(self):
        """ delete all directories under POD dir, then copy
        drivers in."""
        bspdir = self.get_bsp_dir()
        if bspdir is None:
            raise PodError("Set directory before", 0)
        # deleting all directory in POD dir
        sy.del_all_dir(bspdir)
        for directory in \
                sy.list_dir(self.project.projectpath + DRIVERSPATH + "/"):
            sy.cp_dir(self.project.projectpath + DRIVERSPATH +
                      "/" + directory,
                      self.get_bsp_dir())

    def get_bsp_dir(self):
        """ return the directory where drivers files are copied """
        return self.bspdir

    def set_bsp_directory(self, directory):
        """ set the directory where drivers files must be copied """
        lastdir = directory.split("/")[-1]
        if lastdir != "POD":
            raise PodError("The directory must be named POD and not " +
                           lastdir, 0)
        if sy.dir_exist(directory):
            if self.get_node(nodename="bsp") is not None:
                self.get_node(nodename="bsp").set_attr("directory", directory)
            else:
                self.add_node(nodename="bsp",
                              attributename="directory",
                              value=directory)
            self.bspdir = directory
        else:
            raise PodError("Directory " + directory + " does not exist", 0)
