#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Driver.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  16/07/2008
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

__doc__ = ""
__version__ = "1.0.0"
__versionTime__ = "16/07/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import re
from periphondemand.bin.define import *
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.error import Error
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.display import Display

settings = Settings()
display = Display()


class Driver(WrapperXml):
    """
    """

    def __init__(self, project):
        self.project = project
        filepath = settings.projectpath + "/" +\
                   DRIVERSPATH + "/drivers" + XMLEXT
        if not sy.fileExist(filepath):
            raise Error("No driver project found", 3)
        WrapperXml.__init__(self, file=filepath)
        self.bspdir = None

    def generateProject(self):
        """ copy template drivers files """
        project = self.project
        os = self.getName()
        if os is None:
            raise Error("Operating system must be selected", 0)
        for component in project.instances:
            if component.getNum() == "0":
                driverT = component.getDriver_Template(os)
                if driverT is not None:
                    if sy.dirExist(settings.projectpath + DRIVERSPATH +
                                    "/" + component.getName()):
                        display.msg("Driver directory for " +
                                    component.getName() +
                                    " allready exist. suppressing it")
                        sy.delDirectory(settings.projectpath + DRIVERSPATH +
                                        "/" + component.getName())
                    display.msg("Create directory for " +
                                component.getName() + " driver")
                    # create component directory
                    sy.makeDirectory(settings.projectpath +
                                     DRIVERSPATH + "/" +
                                     component.getName())
                else:
                    display.msg("No driver for " + component.getName())

    def fillAllTemplates(self):
        """ fill template """
        project = self.project
        os = self.getName()
        if os is None:
            raise Error("Operating system must be selected", 0)
        for component in project.instances:
            if component.getNum() == "0":
                driverT = component.getDriver_Template(os)
                if driverT is not None:
                    display.msg("Copy and fill template for " +
                                component.getName())
                    for templatefile in driverT.getTemplatesList():
                        try:
                            template = open(
                                    settings.projectpath + COMPONENTSPATH +
                                    "/" + component.getInstanceName() + "/" +
                                    DRIVERS_TEMPLATES_PATH + "/" + os + "/" +
                                    templatefile, "r")
                            destfile = open(
                                    settings.projectpath + DRIVERSPATH + "/" +
                                    component.getName() + "/" + templatefile,
                                    "w")
                        except IOError, error:
                            raise Error(str(error), 0)
                        self.fillTemplate(template, destfile, component)
                        template.close()
                        destfile.close()

    def fillTemplateForEachInstance(self, template, component):
        """ fill template for each instance of component """
        project = self.project
        out = ""
        for instance in \
                project.get_instances_list_of_component(component.getName()):
            for writeline in template.split("\n"):
                # instance_name
                writeline = re.sub(r'\/\*\$instance_name\$\*\/',
                            instance.getInstanceName().upper(),
                            writeline)
                # instance_num
                writeline = re.sub(r'\/\*\$instance_num\$\*\/',
                                   instance.getNum(),
                                   writeline)
                # generic:generic_name
                exp = re.compile(r'\/\*\$generic\:(.*?)\$\*\/')
                iterator = exp.finditer(writeline)
                for generic in iterator:
                    writeline = re.sub(r'\/\*\$generic:' +
                                       generic.group(1) + r'\$\*\/',
                              instance.getGeneric(generic.group(1)).getValue(),
                              writeline)
                # register_base_address:interface_name
                exp = re.compile(r'\/\*\$registers_base_address:(.*?)\$\*\/')
                iterator = exp.finditer(writeline)
                for interface in iterator:
                    writeline = re.sub(r'\/\*\$registers_base_address:' +
                                       interface.group(1) + '\$\*\/',
                                        instance.getInterface(
                                            interface.group(1)).getBase(),
                                            writeline)
                # register:interfacename:registername:attribute
                exp = re.compile(r'\/\*\$register:(.*?):(.*?):(.*?)\$\*\/')
                iterator = exp.finditer(writeline)
                for match in iterator:
                    attributevalue = instance.getInterface(
                            match.group(1)).getRegister(
                                    match.group(2)).getAttributeValue(
                                            match.group(3))
                    if not attributevalue:
                        raise Error(
                                "Wrong register value -> " +
                                match.group(1) + ":" + match.group(2) +
                                ":" + match.group(3) + "\n", 0)
                    writeline = re.sub(
                            r'\/\*\$register:' + match.group(1) +
                            ':' + match.group(2) + ':' +
                            match.group(3) + '\$\*\/',
                            attributevalue, writeline)
                # interrupt_number
                if re.search(r'\/\*\$interrupt_number\$\*\/',
                             writeline) is not None:
                    interruptlist = instance.getInterruptList()
                    if len(interruptlist) == 0:
                        raise Error("No interruption port in " +
                                    instance.getInstanceName(), 0)
                    elif len(interruptlist) > 1:
                        display.msg("More than one interrupt port in " +
                                instance.getInstanceName() +
                                ". " + interruptlist[0].getName() + " is used")
                    interruptport = interruptlist[0]

                    try:
                        connect = interruptport.getPin(0).getConnections()
                    except Error, error:
                        raise Error(
                     "Interrupt " + interruptport.getName() +
                     " not connected in " +
                     interruptport.getParent().getParent().getInstanceName() +
                     "." + interruptport.getParent().getName(), 0)
                    if len(connect) == 0:
                        raise Error("Interrupt " + interruptport.getName() +
                                    " is not connected", 0)
                    elif len(connect) > 1:
                        display.msg(
                        "More than one connection for interruption port " +
                        interruptport.getName() + ". " +
                        connect[0]["port_dest"] + " is used")
                    writeline = re.sub(r'\/\*\$interrupt_number\$\*\/',
                                connect[0]["pin_dest"],
                                writeline)
                out = out + writeline + "\n"
        return out

    def fillTemplate(self, template, destfile, component):
        """ fill template file """
        project = self.project
        state = "STANDARD"
        foreach_template = ""

        for line in template:
            if state == "STANDARD":
                begintag = re.match('^\/\*\$foreach\:instance\$\*\/', line)
                if begintag is not None:
                    state = "FOREACH_INSTANCE"
                    foreach_template = ""
                    continue
                # number_of_instances
                if re.search(r'\/\*\$number_of_instances\$\*\/',
                             line) is not None:
                    listOfInstances = \
                            project.get_instances_list_of_component(
                                    component.getName())
                    line = re.sub(r'\/\*\$number_of_instances\$\*\/',
                                        str(len(listOfInstances)),
                                        line)
                # main clock speed
                if re.search(r'\/\*\$main_clock\$\*\/', line) is not None:
                    frequency = project.platform.getMainClock()
                    line = re.sub('\/\*\$main_clock\$\*\/', frequency, line)
                destfile.write(line)
            elif state == "FOREACH_INSTANCE":
                endtag = re.match('^\/\*\$foreach\:instance\:end\$\*\/', line)
                if endtag is not None:
                    state = "STANDARD"
                    destfile.write(
                            self.fillTemplateForEachInstance(
                                foreach_template,
                                component))
                else:
                    foreach_template = foreach_template + line
            else:
                raise Error("State error in toolchain driver\n", 0)

    def copyBSPDrivers(self):
        """ delete all directories under POD dir, then copy
        drivers in."""
        bspdir = self.getBSPDirectory()
        if bspdir is None:
            raise Error("Set directory before", 0)
        # deleting all directory in POD dir
        sy.deleteAllDir(bspdir)
        for directory in \
                sy.listDirectory(settings.projectpath + DRIVERSPATH + "/"):
            sy.copyDirectory(settings.projectpath + DRIVERSPATH +
                             "/" + directory,
                             self.getBSPDirectory())

    def setProjectTree(self, tree):
        """ set the directory where driver will be copied"""
        self.setBSPDirectory(tree)

    def setOperatingSystem(self, os):
        """ select operating system  """
        self.setBSPOperatingSystem(os)

    def getBSPDirectory(self):
        """ return the directory where drivers files are copied """
        return self.bspdir

    def setBSPDirectory(self, directory):
        """ set the directory where drivers files must be copied """
        lastdir = directory.split("/")[-1]
        if lastdir != "POD":
            raise Error("The directory must be named POD and not " +
                        lastdir, 0)
        if sy.dirExist(directory):
            if self.getNode(nodename="bsp") is not None:
                self.getNode(nodename="bsp").setAttribute("directory",
                                                          directory)
            else:
                self.addNode(nodename="bsp",
                             attributename="directory",
                             value=directory)
            self.bspdir = directory
        else:
            raise Error("Directory " + directory + " does not exist", 0)

    def setBSPOperatingSystem(self, operatingsystem):
        """ set the operating system for driver generation """
        if self.getNode(nodename="bsp") is not None:
            self.getNode(nodename="bsp").setAttribute("os",
                                                      operatingsystem)
        else:
            self.addNode(nodename="bsp",
                         attributename="os",
                         value=operatingsystem)
        self.bspos = operatingsystem
