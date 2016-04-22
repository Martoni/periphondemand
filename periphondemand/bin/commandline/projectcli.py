#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     ProjectCli.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  23/05/2008
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
#
# pylint: disable=W0613
""" Command line for project management """

import os

from periphondemand.bin.define import XMLEXT
from periphondemand.bin.define import PODSCRIPTEXT

from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.display import Display

from periphondemand.bin.commandline.synthesiscli import SynthesisCli
from periphondemand.bin.commandline.simulationcli import SimulationCli
from periphondemand.bin.commandline.drivercli import DriverCli

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.basecli import Statekeeper
from periphondemand.bin.utils.basecli import BaseCli
from periphondemand.bin.utils.poderror import PodError

from periphondemand.bin.core.project import Project

from periphondemand.bin.code.vhdl.topvhdl import TopVHDL

SETTINGS = Settings()
DISPLAY = Display()


class ProjectCli(BaseCli):
    """ Project command line interface
    """
    def __init__(self, parent=None):
        BaseCli.__init__(self, parent)
        self._project = None

    def do_synthesis(self, arg):
        """\
Usage : synthesis
synthesis commands
        """
        try:
            self.is_project_open()
            self.isPlatformSelected()
        except PodError as error:
            print(error)
            return

        cli = SynthesisCli(self, self._project)
        cli.setPrompt("synthesis")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")

    def do_simulation(self, line):
        """\
Usage : simulation
Simulation generation environment
        """
        try:
            self.is_project_open()
            self.isPlatformSelected()
        except PodError as error:
            print(error)
            return

        # test if only one toolchain for simulation in library
        cli = SimulationCli(self, self._project)
        cli.setPrompt("simulation")
        line = str(line)
        if len(line) > 0:
            line = cli.precmd(line)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")

    def do_driver(self, line):
        """\
Usage : driver
Driver generation environment
        """
        try:
            self.is_project_open()
            self.isPlatformSelected()
        except PodError as error:
            print(error)
            return

        # test if only one toolchain for simulation in library
        cli = DriverCli(self, self._project)
        cli.setPrompt("driver")
        line = str(line)
        if len(line) > 0:
            line = cli.precmd(line)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")

    def do_create(self, line):
        """\
Usage : create <projectname>
create new project
        """
        try:
            self.checkargs(line, "<projectname>")
        except PodError as error:
            print(error)
            return
        try:
            sy.check_name(line)
        except PodError as error:
            print(error)
            return 0
        dirname = os.path.abspath(line)
        if sy.dir_exist(dirname):
            print("Project " + line + " already exists")
            return 0
        else:
            try:
                self._project = Project(dirname, void=0)
            except PodError as error:
                print(error)
                return

        self.setPrompt("POD", self._project.name)
        print("Project " + self._project.name + " created")

    def complete_load(self, text, line, begidx, endidx):
        """ complete load command with files under directory """
        path = line.split(" ")[1]
        if path.find("/") == -1:  # sub
            path = ""
        elif text.split() == "":  # sub/sub/
            path = "/".join(path) + "/"
        else:  # sub/sub
            path = "/".join(path.split("/")[0:-1]) + "/"
        listdir = sy.list_dir(path)
        listfile = sy.list_file_type(path, XMLEXT[1:])
        listfile.extend(listdir)
        return self.completelist(line, text, listfile)

    def do_load(self, line):
        """\
Usage : projectload <projectfilename>.xml
Load a project
        """
        try:
            self.checkargs(line, "<projectfilename>.xml")
        except PodError as error:
            print(error)
            return
        if sy.dir_exist(line):
            head, projectname = os.path.split(line)
            line = os.path.join(head, projectname, projectname + ".xml")
        if not sy.file_exist(line):
            print(PodError("File doesn't exists"))
            return
        try:
            self._project = Project(line)
        except PodError as error:
            print(error)
            return
        except IOError as error:
            print(error)
            return
        self.setPrompt("POD:" + self._project.name)
        print(DISPLAY)

    def complete_setspeedgrade(self, text, line, begidx, endidx):
        """ TOOD """
        pass

    def do_setspeedgrade(self, line):
        """
Usage : setspeedgrade <speedgrade>
Setting speedgrade of FPGA
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<speedgrade>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        try:
            self._project.fpga_speed_grade = line
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_getspeedgrade(self, text, line, begidx, endidx):
        """ TODO """
        pass

    def do_getspeedgrade(self):
        """\
Usage : getspeedgrade
Print FPGA speed grade information
        """
        try:
            speedgrade = self._project.fpga_speed_grade
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print("FPGA speed grade : " + speedgrade)

    def complete_setfpgadevice(self, text, line, begidx, endidx):
        """ TODO """
        pass

    def do_setfpgadevice(self, line):
        """\
Usage : setfpgadevice
Setting FPGA device
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<fpgatype>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        try:
            self._project.fpga_device = line
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_selectvhdlversion(self, text, line, begidx, endidx):
        """ TODO """
        pass

    def do_selectvhdlversion(self, line):
        """\
Usage : selectvhdlversion
Select VHDL version
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<vhdlversion>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        try:
            self._project.vhdl_version = line
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_getfpgadevice(self, text, line, begidx, endidx):
        """ TODO """
        pass

    def do_getfpgadevice(self):
        """\
Usage : getfpgadevice
Print FPGA device information
        """
        try:
            fpgadevice = self._project.fpga_device
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print("FPGA model : " + fpgadevice)

    def complete_addcomponentslib(self, text, line, begidx, endidx):
        """ TOOD """
        pass

    def do_addcomponentslib(self, line):
        """\
Usage : addcomponentslib <componentslibpath>
Adding components library
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<componentslibpath>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        try:
            self._project.add_component_lib(line)
        except PodError as error:
            print(DISPLAY)
            print((error))
            return
        print(DISPLAY)

    def complete_addplatformslib(self, text, line, begidx, endidx):
        """ TOOD """
        pass

    def do_addplatformslib(self, line):
        """\
Usage : addplatformslib <platformslibpath>
Adding platforms library
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<platformslibpath>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        try:
            self._project.add_platforms_lib(line)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_addinstance(self, text, line, begidx, endidx):
        """ Complete addinstance """
        componentlist = []
        try:
            componentlist =\
                self.completeargs(
                    text, line,
                    "<libraryname>.<componentname>.[componentversion] " +
                    "[newinstancename]")
        except PodError as error:
            print(error)
        return componentlist

    def do_addinstance(self, line):
        """\
Usage : addinstance \\
        <libraryname>.<componentname>.[componentversion] \\
        [newinstancename]
Add component in project
        """
        try:
            self.is_project_open()
            self.isPlatformSelected()
            self.checkargs(
                line,
                "<libraryname>.<componentname>.[componentversion] " +
                "[newinstancename]")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        arg = line.split(' ')
        subarg = arg[0].split(".")
        try:
            instancename = arg[1]
        except IndexError:
            instancename = None
        try:
            componentversion = subarg[2]
        except IndexError:
            componentversion = None
        try:
            if (instancename is not None):
                sy.check_name(instancename)
            if (instancename is None) and (componentversion is None):
                self._project.add_instance(
                    componentname=subarg[1],
                    libraryname=subarg[0])
            elif (instancename is not None) and (componentversion is None):
                self._project.add_instance(
                    componentname=subarg[1],
                    libraryname=subarg[0],
                    instancename=instancename)
            elif (instancename is None) and (componentversion is not None):
                self._project.add_instance(
                    componentname=subarg[1],
                    libraryname=subarg[0],
                    componentversion=componentversion)
            else:
                self._project.add_instance(
                    componentname=subarg[1],
                    libraryname=subarg[0],
                    componentversion=componentversion,
                    instancename=instancename)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_listcomponents(self, text, line, begidx, endidx):
        """ Complete listcomponents """
        componentlist = []
        try:
            componentlist = self.completeargs(text, line, "[libraryname]")
        except PodError:
            pass
        return componentlist

    def do_listcomponents(self, line):
        """\
Usage : listcomponents [libraryname]
List components available in the library
        """
        if line.strip() == "":
            return self.columnize(self._project.library.libraries)
        else:
            return self.columnize(
                self._project.library.list_components(line))

    def listinstances(self):
        """ List instances in project completion"""
        try:
            self.is_project_open()
            return [comp.instancename
                    for comp in self._project.instances]
        except PodError as error:
            print(error)
            return

    def do_listinstances(self, line):
        """\
Usage : listinstances
List all project instances
        """
        try:
            self.is_project_open()
        except PodError as error:
            print(error)
            return
        return self.columnize(self.listinstances())

    def complete_selectplatform(self, text, line, begidx, endidx):
        """ selectplatform command completion """
        platformlist = []
        try:
            platformlist = self.completeargs(text, line,
                                             "<platformlib>.<platformname>")
        except PodError as error:
            print(error)
        return platformlist

    def do_selectplatform(self, line):
        """\
Usage : selectplatform <platformname>
Select the platform to use
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<platformlib>.<platformname>")
        except PodError as error:
            print(error)
            return
        try:
            args = line.strip().split(".")
            self._project.select_platform(args[1], args[0])
            self._project.save()
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def do_listplatforms(self, line):
        """\
Usage : listplatforms
List platform available
        """
        try:
            self.is_project_open()
        except PodError as error:
            print(error)
            return
        try:
            return self.columnize(
                self._project.availables_plat())
        except AttributeError as error:
            print(error)

    def complete_listinterfaces(self, text, line, begidx, endidx):
        """ complete listinterfaces command """
        pinlist = []
        try:
            pinlist = self.completeargs(text, line,
                                        "<instancename>")
        except PodError as error:
            print(error)
        return pinlist

    def do_listinterfaces(self, line=None):
        """\
Usage : listinterfaces
List instance interface
        """
        try:
            self.checkargs(line, "<instancename>")
            self.is_project_open()
            interfacelist =\
                [interface.name for interface in
                    self._project.get_instance(
                        line).interfaces]
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)
        return self.columnize(interfacelist)

    def complete_connectpin(self, text, line, begidx, endidx):
        """ connectpin command completion """
        pinlist = []
        try:
            pinlist = self.completeargs(
                text, line,
                "<instancename>.<interfacename>.<portname>.<pinnum> " +
                "<instancename>.<interfacename>.<portname>.<pinnum>")
        except PodError as error:
            print(error)
        return pinlist

    def do_connectpin(self, line):
        """\
Usage :
connectpin \\
    <instancename>.<interfacename>.<portname>.[pinnum] \\
    <instancename>.<interfacename>.<portname>.[pinnum]
Connect pin between instances
        """
        try:
            self.is_project_open()
            self.checkargs(
                line,
                "<instancename>.<interfacename>.<portname>.[pinnum] " +
                "<instancename>.<interfacename>.<portname>.[pinnum]")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        dest = arg[-1].split('.')
        if len(source) == 3:
            source.append(0)
        if len(dest) == 3:
            dest.append(0)
        try:
            self._project.connect_pin_cmd(
                self._project.get_instance(
                    source[0]).get_interface(
                        source[1]).get_port(
                            source[2]).get_pin(source[3]),
                self._project.get_instance(
                    dest[0]).get_interface(
                        dest[1]).get_port(dest[2]).get_pin(dest[3]))
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_setunconnectedvalue(self, text, line, begidx, endidx):
        """ setunconnectedvalue command completion """
        portlist = []
        try:
            portlist =\
                self.completeargs(
                    text, line,
                    "<instancename>.<interfacename>.<portname> <uvalue>")
        except PodError as error:
            print(error)
        return portlist

    def do_setunconnectedvalue(self, line):
        """
Usage : setunconnectedvalue <instancename>.<interfacename>.<portname> <uvalue>
Force input port unconnected value
        """
        try:
            self.is_project_open()
            self.checkargs(
                line,
                "<instancename>.<interfacename>.<portname> <uvalue>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        if len(arg) != 2:
            print("arguments error")
            return
        uvalue = arg[1].strip()

        if len(source) != 3:
            print("source arguments error")
            return
        try:
            portdict = {"instance": source[0],
                        "interface": source[1],
                        "port": source[2]}
            self._project.set_unconnected_value(portdict, uvalue)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_connectport(self, text, line, begidx, endidx):
        """ connectport command completion """
        portlist = []
        try:
            portlist = self.completeargs(
                text, line,
                "<instancename>.<interfacename>.<portname> " +
                "<instancename>.<interfacename>.<portname>")
        except PodError as error:
            print(error)
        return portlist

    def do_connectport(self, line):
        """
Usage : connectport \\
        <instancename>.<interfacename>.<portname> \\
        <instancename>.<interfacename>.<portname>
Connect all pins of two same size ports.
        """
        try:
            self.is_project_open()
            self.checkargs(
                line,
                "<instancename>.<interfacename>.<portname> " +
                "<instancename>.<interfacename>.<portname>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        dest = arg[-1].split('.')

        if len(source) != 3:
            print("source arguments error")
            return
        if len(dest) != 3:
            print("Argument error")
            return
        try:
            self._project.connect_port(
                {"instance": source[0], "interface": source[1],
                 "port": source[2]},
                {"instance": dest[0], "interface": dest[1],
                 "port": dest[2]})
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_connectinterface(self, text, line, begidx, endix):
        """ complete connectinterface command """
        buslist = []
        try:
            buslist = self.completeargs(text, line,
                                        "<instancename>.<interfacename> " +
                                        "<instancename>.<interfacename>")
        except PodError as error:
            print(error)
        return buslist

    def do_connectinterface(self, line):
        """\
Usage :
connectinterface \\
        <instancename>.<interfacename> \\
        <instancename>.<interfacename>
Connect interface between two components
        """
        try:
            self.is_project_open()
            self.checkargs(line,
                           "<instancename>.<interfacename> " +
                           "<instancename>.<interfacename>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        dest = arg[-1].split('.')
        if (len(source) != 2) or (len(dest) != 2):
            print("Argument error")
            return
        try:
            sourcedict = {"instance": source[0], "interface": source[1]}
            destdict = {"instance": dest[0], "interface": dest[1]}
            self._project.connect_interface(sourcedict, destdict)
        except PodError as error:
            print("<<interface " + source[1] +
                  " and interface " + dest[1] + " are not compatible>>")
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_delbusconnection(self, text, line, begidx, endidx):
        """ delbusconnection command completion """
        connectlist = []
        try:
            connectlist =\
                self.completeargs(
                    text, line,
                    "<masterinstancename>.<masterinterfacename> " +
                    "<slaveinstancename>.<slaveinterfacename>")
        except PodError as error:
            print(error)
        return connectlist

    def do_delbusconnection(self, line):
        """\
Usage :
delbusconnection \\
        <masterinstancename>.<masterinterfacename> \\
        <slaveinstancename>.<slaveinterfacename>
Suppress a pin connection
        """
        try:
            self.is_project_open()
            self.checkargs(
                line,
                "<masterinstancename>.<masterinterfacename> " +
                "<slaveinstancename>.<slaveinterfacename>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        dest = arg[-1].split('.')
        if (len(source) != 2) or (len(dest) != 2):
            print("Argument error")
            return
        try:
            masterdict = {"instance": source[0], "interface": source[1]}
            slavedict = {"instance": dest[0], "interface": dest[1]}
            self._project.del_bus(masterdict, slavedict)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_connectbus(self, text, line, begidx, endidx):
        """ connectbus command completion """
        buslist = []
        try:
            buslist = self.completeargs(
                text, line,
                "<masterinstancename>.<masterinterfacename> " +
                "<slaveinstancename>.<slaveinterfacename>")
        except PodError as error:
            print(error)
        return buslist

    def do_connectbus(self, line):
        """\
Usage :
connectbus \\
        <masterinstancename>.<masterinterfacename> \\
        <slaveinstancename>.<slaveinterfacename>
Connect slave to master bus
        """
        try:
            self.is_project_open()
            self.checkargs(
                line,
                "<masterinstancename>.<masterinterfacename> " +
                "<slaveinstancename>.<slaveinterfacename>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        dest = arg[-1].split('.')
        if (len(source) != 2) or (len(dest) != 2):
            print("Argument error")
            return
        try:
            masterdict = {"instance": source[0], "interface": source[1]}
            slavedict = {"instance": dest[0], "interface": dest[1]}
            self._project.connect_bus(masterdict, slavedict)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def do_autoconnectbus(self, line):
        """\
Usage : autoconnectbus
Autoconnect bus if only one master in project
        """
        try:
            self.is_project_open()
            self._project.auto_connect_busses()
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def complete_delpinconnection(self, text, line, begidx, endidx):
        """ delpinconnection command completion """
        connectlist = []
        try:
            connectlist = \
                self.completeargs(
                    text, line,
                    "<instancename>.<interfacename>.<portname>.<pinnum> " +
                    "<instancename>.<interfacename>.<portname>.<pinnum>")
        except PodError as error:
            print(error)
        return connectlist

    def do_delpinconnection(self, line):
        """\
Usage :
delpinconnection \\
<instancename>.<interfacename>.<portname>.[pinnum] \\
[instancename].[interfacename].[portname].[pinnum]

Suppress a pin connection
        """
        try:
            self.is_project_open()
            self.checkargs(
                line,
                "<instancename>.<interfacename>.<portname>.[pinnum] " +
                "[instancename].[interfacename].[portname].[pinnum]")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        # get arguments
        arg = line.split(' ')
        # make source and destination tabular
        source = arg[0].split('.')
        dest = arg[-1].split('.')
        # check if dest "instance.interface.port.pin" present,
        # if not set it to [None] tabular
        try:
            dest = arg[1].split('.')
        except IndexError:
            dest = [None, None, None, None]
        # check if pin num present, if not set it None
        if len(source) == 3:  # instead of 4
            source.append(None)
        if len(dest) == 3:
            dest.append(None)
        try:
            self._project.delete_pin_connection_cmd(
                {"instance": source[0], "interface": source[1],
                 "port": source[2], "num": source[3]},
                {"instance": dest[0], "interface": dest[1],
                 "port": dest[2], "num": dest[3]})
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)
        print("Connection deleted")

    def complete_delinstance(self, text, line, begidx, endidx):
        """ complete delinstance command """
        componentlist = []
        try:
            componentlist = self.completeargs(text, line, "<instancename>")
        except PodError as error:
            print(error)
        return componentlist

    def do_delinstance(self, line):
        """\
Usage : delinstance <instancename>
Suppress a component from project
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<instancename>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        try:
            self._project.del_instance(line)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)

    def do_check(self, line):
        """\
Usage : check
Check the project before code generation
        """
        try:
            self.is_project_open()
            self._project.check()
        except PodError as error:
            print(DISPLAY)
            print(error)
        print(DISPLAY)

    def complete_setaddr(self, text, line, begidx, endidx):
        """ setaddr command completion """
        addrlist = []
        try:
            addrlist = \
                self.completeargs(
                    text, line,
                    "<slaveinstancename>.<slaveinterfacename> " +
                    "<addressinhexa>")
        except PodError as error:
            print(error)
        return addrlist

    def do_setaddr(self, line):
        """\
Usage : setaddr <slaveinstancename>.<slaveinterfacename> <addressinhexa>
Set the base address of slave interface
        """
        try:
            self.is_project_open()
            self.checkargs(
                line,
                "<slaveinstancename>.<slaveinterfacename> <addressinhexa>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        arg = line.split(' ')
        names = arg[0].split('.')
        if len(names) < 2:
            masterinterface =\
                self._project.get_instance(names[0]).slave_interfaces
            if len(masterinterface) != 1:
                print(DISPLAY)
                print("PodError, need a slave interface name")
                return
            names.append(masterinterface[0].name)

        try:
            interfaceslave =\
                self._project.get_instance(
                    names[0]).get_interface(names[1])
            interfacemaster = interfaceslave.master
            interfacemaster.alloc_mem.set_slave_addr(interfaceslave, arg[1])
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)
        print("Base address " + arg[1] + " set")

    def do_listmasters(self, line):
        """\
Usage : listmaster
List master interface
        """
        try:
            self.is_project_open()
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        for master in self._project.interfaces_master:
            print(master.parent.instancename + "." + master.name)
        print(DISPLAY)

    def complete_getmapping(self, text, line, begidx, endidx):
        """ getmapping command completion """
        mappinglist = []
        try:
            mappinglist = \
                self.completeargs(text, line,
                                  "<masterinstancename>.<masterinterfacename>")
        except PodError as error:
            print(error)
        return mappinglist

    def do_getmapping(self, line=None):
        """\
Usage : getmapping <masterinstancename>.<masterinterfacename>
Return mapping for a master interface
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<masterinstancename>.<masterinterfacename>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        arg = line.split(' ')
        names = arg[0].split('.')
        try:
            masterinterface =\
                self._project.get_instance(
                    names[0]).get_interface(names[1])
            print(str(masterinterface.alloc_mem))
        except PodError as error:
            print(DISPLAY)
            print(error)
        print(DISPLAY)

    def complete_printxml(self, text, line, begidx, endidx):
        """ printxml command completion """
        printlist = []
        try:
            printlist = self.completeargs(text, line, "<instancename>")
        except PodError as error:
            print(error)
        return printlist

    def do_printxml(self, line=None):
        """\
Usage : printxml <instancename>
Print instance in XML format
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<instancename>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(self._project.get_instance(line))
        print(DISPLAY)

    def complete_info(self, text, line, begidx, endidx):
        """ info command completion """
        infolist = []
        try:
            infolist = self.completeargs(text, line, "<instancename>")
        except PodError as error:
            print(error)
        return infolist

    def do_info(self, line=None):
        """\
Usage : info <instancename>
Print instance information
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<instancename>")
            instance = self._project.get_instance(line)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print("Instance name :" + instance.instancename)
        print("Component  name :" + instance.name)
        print("description : " + instance.description.strip())
        print("->Generics")
        for generic in instance.generics:
            print("%15s : " % generic.name + generic.value)
        print("->Interfaces")
        for interface in instance.interfaces:
            if interface.bus_name is not None:
                if interface.interface_class == "slave":
                    print("%-15s " % interface.name +
                          " Base address:" + hex(interface.base_addr))
                elif interface.interface_class == "master":
                    print("%-15s :" % interface.name)
                    for slave in interface.slaves:
                        print(" " * 10 + "slave -> " +
                              slave.instancename + "." +
                              slave.interfacename)
            else:
                print("%-15s :" % interface.name)

            for port in interface.ports:
                print(" " * 5 + "%-15s" % port.name +
                      " s" + port.size)
                for pin in port.pins:
                    print(" " * 8 + "pin"),
                    if pin.num is not None:
                        print(pin.num + ":"),
                    first = True
                    for connection in pin.connections:
                        if first is not True:
                            print(" " * 8 + "|" + " " * 5),
                        first = False
                        print("-> " +
                              connection["instance_dest"] + "." +
                              connection["interface_dest"] + "." +
                              connection["port_dest"] + "." +
                              connection["pin_dest"])

    def complete_setgeneric(self, text, line, begidx, endidx):
        """ setgeneric command completion """
        genericlist = []
        try:
            genericlist =\
                self.completeargs(
                    text, line,
                    "<instancename>.<genericname> <genericvalue>")
        except PodError as error:
            print(error)
        return genericlist

    def do_setgeneric(self, line=None):
        """\
Usage : setgeneric <instancename>.<genericname> <genericvalue>
Set generic parameter
        """
        try:
            self.is_project_open()
            self.checkargs(line,
                           "<instancename>.<genericname> <genericvalue>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        args = line.split(" ")
        names = args[0].split(".")
        try:
            instance = self._project.get_instance(names[0])
            generic = instance.get_generic(names[1])
            if generic.is_public() is True:
                generic.value = args[1]
            else:
                raise PodError("this generic can't be modified by user", 0)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)
        print("Done")

    def do_description(self, line):
        """\
Usage : description <some word for description>
set the project description
        """
        self._project.description = line
        print(DISPLAY)
        print("Description set : " + line)
        return

    def do_closeproject(self, line):
        """\
Usage : closeproject
Close the project
        """
        try:
            self.is_project_open()
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        self._project = None
        print(DISPLAY)
        print("Project closed")

    # Generate CODE
    def complete_generateintercon(self, text, line, begidx, endidx):
        """ generateintercon command completion """
        interconlist = []
        try:
            interconlist =\
                self.completeargs(
                    text, line,
                    "<masterinstancename>.<masterinterfacename>")
        except PodError as error:
            print(error)
        return interconlist

    def do_generateintercon(self, line=None):
        """\
Usage : generateintercon <masterinstancename>.<masterinterfacename>
Generate intercon for master given in argument
        """
        try:
            self.is_project_open()
            self.checkargs(line, "<instancename>.<masterinterfacename>")
        except PodError as error:
            print(error)
            return
        arg = line.split(' ')
        names = arg[0].split('.')
        if len(names) != 2:
            print("Arguments error")
            return
        try:
            interfacedict = {"instance": names[0], "interface": names[1]}
            self._project.generate_intercon(interfacedict)
        except PodError as error:
            print(error)
            return
        print(DISPLAY)

    def do_generatetop(self, line):
        """\
Usage : generatetop
Generate top component
        """
        try:
            self.is_project_open()
            self._project.check()
            top = TopVHDL(self._project)
            top.generate()
        except PodError as error:
            print(error)
            return
        print(DISPLAY)
        print("Top generated with name : top_" +
              self._project.name + ".vhd")

    def do_report(self, line):
        """\
Usage : report
Generate a report of the project
        """
        try:
            self.is_project_open()
            text = self._project.generate_report()
        except PodError as error:
            print(DISPLAY)
            print(error)
            return
        print(DISPLAY)
        print("report : ")
        print(text)

    def is_project_open(self):
        """ check if project is open, raise error if not
        """
        if self._project is None or self._project.void:
            raise PodError("No project open", 0)

    def do_listforce(self, line):
        """\
Usage : listforce
List all force configured for this project
        """
        try:
            for port in self._project.forced_ports:
                print("port " + str(port.name) +
                      " is forced to " + port.force)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return

    def complete_setforce(self, text, line, begidx, endidx):
        """ setforce command completion """
        pinlist = []
        try:
            pinlist = self.completeargs(text, line, "<forcename> <forcestate>")
        except PodError as error:
            print(error)
        return pinlist

    def do_setforce(self, line):
        """\
Usage : setpin <pinname> <state>
Set fpga pin state in 'gnd', 'vcc'. To unset use 'undef' value
        """

        try:
            self.is_project_open()
            self.checkargs(line, "<forcename> <forcestate>")
        except PodError as error:
            print(DISPLAY)
            print(error)
            return

        arg = line.split(' ')
        portname = arg[-2]
        state = arg[-1]

        try:
            self._project.set_force(portname, state)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return

    @classmethod
    def do_setcolor(cls, line):
        """\
Usage: setcolor [0/1]
Set 1 if you want color output, 0 else
        """
        arg = line.split(' ')
        value = arg[-1].strip()

        try:
            SETTINGS.set_color(value)
        except PodError as error:
            print(DISPLAY)
            print(error)
            return

    def complete_source(self, text, line, begidx, endidx):
        """ complete load command with files under directory """
        path = line.split(" ")[1]
        if path.find("/") == -1:  # sub
            path = ""
        elif text.split() == "":  # sub/sub/
            path = "/".join(path) + "/"
        else:  # sub/sub
            path = "/".join(path.split("/")[0:-1]) + "/"
        listdir = sy.list_dir(path)
        listfile = sy.list_file_type(path, PODSCRIPTEXT[1:])
        listfile.extend(listdir)
        return self.completelist(line, text, listfile)

    def do_source(self, fname=None):
        """\
Usage : source <filename>
use <filename> as standard input execute commands stored in.
Runs command(s) from a file.
        """
        keepstate = Statekeeper(self,
                                ('stdin', 'use_rawinput', ))
        try:
            self.stdin = open(fname, 'r')
        except IOError as error:
            try:
                self.stdin = open('%s.%s' % (fname,
                                             self.default_extension), 'r')
            except IOError:
                print('Problem opening file %s: \n%s' % (fname, error))
                keepstate.restore()
                return
        self.use_rawinput = False
        self.prompt = self.continuation_prompt = ''
        SETTINGS.set_script(1)
        self.cmdloop()
        SETTINGS.set_script(0)
        self.stdin.close()
        keepstate.restore()
        self.lastcmd = ''
        return

    @classmethod
    def do_version(cls, line):
        """\
Usage : version
Print the version of POD
        """
        print("Peripherals On Demand version " + SETTINGS.version)
