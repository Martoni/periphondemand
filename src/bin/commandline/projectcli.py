#!/usr/bin/python
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
from periphondemand.bin.utils.error import Error

from periphondemand.bin.core.project import Project
from periphondemand.bin.core.library import Library

from periphondemand.bin.code.vhdl.topvhdl import TopVHDL

SETTINGS = Settings()
DISPLAY = Display()


class ProjectCli(BaseCli):
    """ Project command line interface
    """
    def __init__(self, parent=None):
        BaseCli.__init__(self, parent)
        SETTINGS.active_project = Project("void", void=1)
        if SETTINGS.active_project is None:
            SETTINGS.active_project = Project("", void=1)
        if SETTINGS.active_library is None:
            SETTINGS.active_library = Library()

    def do_synthesis(self, arg):
        """\
Usage : synthesis
synthesis commands
        """
        try:
            self.isProjectOpen()
            self.isPlatformSelected()
        except Error, error:
            print(str(error))
            return

        cli = SynthesisCli(self)
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
            self.isProjectOpen()
            self.isPlatformSelected()
        except Error, error:
            print(str(error))
            return

        # test if only one toolchain for simulation in library
        cli = SimulationCli(self)
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
            self.isProjectOpen()
            self.isPlatformSelected()
        except Error, error:
            print(str(error))
            return

        # test if only one toolchain for simulation in library
        cli = DriverCli(self)
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
        except Error, error:
            print(str(error))
            return
        try:
            sy.check_name(line)
        except Error, error:
            print(str(error))
            return 0
        dirname = os.path.abspath(line)
        if sy.dirExist(dirname):
            print("Project " + line + " already exists")
            return 0
        else:
            try:
                SETTINGS.active_project = Project(dirname, void=0)
            except Error, error:
                print(str(error))
                return

        self.setPrompt("POD", SETTINGS.active_project.getName())
        print("Project " + SETTINGS.active_project.getName() + " created")

    def complete_load(self, text, line, begidx, endidx):
        """ complete load command with files under directory """
        path = line.split(" ")[1]
        if path.find("/") == -1:  # sub
            path = ""
        elif text.split() == "":  # sub/sub/
            path = "/".join(path) + "/"
        else:  # sub/sub
            path = "/".join(path.split("/")[0:-1]) + "/"
        listdir = sy.listDirectory(path)
        listfile = sy.listFileType(path, XMLEXT[1:])
        listfile.extend(listdir)
        return self.completelist(line, text, listfile)

    def do_load(self, line):
        """\
Usage : projectload <projectfilename>.xml
Load a project
        """
        try:
            self.checkargs(line, "<projectfilename>.xml")
        except Error, error:
            print(str(error))
            return
        if sy.dirExist(line):
            head, projectname = os.path.split(line)
            line = os.path.join(head, projectname, projectname + ".xml")
        if not sy.fileExist(line):
            print Error("File doesn't exists")
            return
        try:
            SETTINGS.active_project = Project(line)
        except Error, error:
            print(str(error))
            return
        except IOError, error:
            print(str(error))
            return
        self.setPrompt("POD:" + SETTINGS.active_project.getName())
        print(str(DISPLAY))

    def complete_setspeedgrade(self, text, line, begidx, endidx):
        """ TOOD """
        pass

    def do_setspeedgrade(self, line):
        """
Usage : setspeedgrade <speedgrade>
Setting speedgrade of FPGA
        """
        try:
            self.isProjectOpen()
            self.checkargs(line, "<speedgrade>")
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        try:
            SETTINGS.active_project.fpga_speed_grade = line
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print(str(DISPLAY))

    def complete_getspeedgrade(self, text, line, begidx, endidx):
        """ TODO """
        pass

    @classmethod
    def do_getspeedgrade(cls):
        """\
Usage : getspeedgrade
Print FPGA speed grade information
        """
        try:
            speedgrade = SETTINGS.active_project.fpga_speed_grade
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print "FPGA speed grade : " + speedgrade

    def complete_setfpgadevice(self, text, line, begidx, endidx):
        """ TODO """
        pass

    def do_setfpgadevice(self, line):
        """\
Usage : setfpgadevice
Setting FPGA device
        """
        try:
            self.isProjectOpen()
            self.checkargs(line, "<fpgatype>")
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        try:
            SETTINGS.active_project.fpga_device = line
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print(str(DISPLAY))

    def complete_getfpgadevice(self, text, line, begidx, endidx):
        """ TODO """
        pass

    def complete_selectvhdlversion(self, text, line, begidx, endidx):
        """ TODO """
        pass

    def do_selectvhdlversion(self, line):
        """\
Usage : selectvhdlversion
Select VHDL version
        """
        try:
            self.isProjectOpen()
            self.checkargs(line, "<vhdlversion>")
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        try:
            SETTINGS.active_project.vhdl_version = line
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print DISPLAY

    def do_getfpgadevice(self):
        """\
Usage : getfpgadevice
Print FPGA device information
        """
        try:
            fpgadevice = SETTINGS.active_project.fpga_device
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
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
            self.isProjectOpen()
            self.checkargs(line, "<componentslibpath>")
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        try:
            SETTINGS.active_project.add_component_lib(line)
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print(str(DISPLAY))

    def complete_addplatformslib(self, text, line, begidx, endidx):
        """ TOOD """
        pass

    def do_addplatformslib(self, line):
        """\
Usage : addplatformslib <platformslibpath>
Adding platforms library
        """
        try:
            self.isProjectOpen()
            self.checkargs(line, "<platformslibpath>")
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        try:
            SETTINGS.active_project.add_platforms_lib(line)
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print(str(DISPLAY))

    def complete_addinstance(self, text, line, begidx, endidx):
        """ Complete addinstance """
        componentlist = []
        try:
            componentlist = self.completeargs(
                    text, line,
                    "<libraryname>.<componentname>.[componentversion] " +
                    "[newinstancename]")
        except Exception, error:
            print(str(error))
        return componentlist

    def do_addinstance(self, line):
        """\
Usage : addinstance \\
        <libraryname>.<componentname>.[componentversion] \\
        [newinstancename]
Add component in project
        """
        try:
            self.isProjectOpen()
            self.isPlatformSelected()
            self.checkargs(
                    line,
                    "<libraryname>.<componentname>.[componentversion] " +
                    "[newinstancename]")
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
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
                SETTINGS.active_project.add_instance(
                        componentname=subarg[1],
                        libraryname=subarg[0])
            elif (instancename is not None) and (componentversion is None):
                SETTINGS.active_project.add_instance(
                        componentname=subarg[1],
                        libraryname=subarg[0],
                        instancename=instancename)
            elif (instancename is None) and (componentversion is not None):
                SETTINGS.active_project.add_instance(
                        componentname=subarg[1],
                        libraryname=subarg[0],
                        componentversion=componentversion)
            else:
                SETTINGS.active_project.add_instance(
                        componentname=subarg[1],
                        libraryname=subarg[0],
                        componentversion=componentversion,
                        instancename=instancename)
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print DISPLAY

    def complete_listcomponents(self, text, line, begidx, endidx):
        """ Complete listcomponents """
        componentlist = []
        try:
            componentlist = self.completeargs(text, line, "[libraryname]")
        except Exception:
            pass
        return componentlist

    def do_listcomponents(self, line):
        """\
Usage : listcomponents [libraryname]
List components available in the library
        """
        if line.strip() == "":
            return self.columnize(SETTINGS.active_library.listLibraries())
        else:
            return self.columnize(
                    SETTINGS.active_library.listComponents(line))

    def listinstances(self):
        """ List instances in project completion"""
        try:
            self.isProjectOpen()
            return [comp.getInstanceName()
                    for comp in SETTINGS.active_project.instances]
        except Error, error:
            print(str(error))
            return

    def do_listinstances(self, line):
        """\
Usage : listinstances
List all project instances
        """
        try:
            self.isProjectOpen()
        except Error, error:
            print(str(error))
            return
        return self.columnize(self.listinstances())

    def complete_selectplatform(self, text, line, begidx, endidx):
        platformlist = []
        try:
            platformlist = self.completeargs(text, line,
                                             "<platformlib>.<platformname>")
        except Exception, error:
            print(str(error))
        return platformlist

    def do_selectplatform(self, line):
        """\
Usage : selectplatform <platformname>
Select the platform to use
        """
        try:
            self.isProjectOpen()
            self.checkargs(line, "<platformlib>.<platformname>")
        except Error, error:
            print(str(error))
            return
        try:
            args = line.strip().split(".")
            SETTINGS.active_project.select_platform(args[1], args[0])
            SETTINGS.active_project.save()
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print DISPLAY

    def do_listplatforms(self, line):
        """\
Usage : listplatforms
List platform available
        """
        try:
            self.isProjectOpen()
        except Error, error:
            print(str(error))
            return
        try:
            return self.columnize(
                    SETTINGS.active_project.availables_platforms)
        except AttributeError, error:
            print(str(error))

    def complete_listinterfaces(self, text, line, begidx, endidx):
        pinlist = []
        try:
            pinlist = self.completeargs(text, line,
                                        "<instancename>")
        except Exception, error:
            print(str(error))
        return pinlist

    def do_listinterfaces(self, line=None):
        """\
Usage : listinterfaces
List instance interface
        """
        try:
            self.checkargs(line, "<instancename>")
            self.isProjectOpen()
            interfacelist = [interface.getName()
              for interface in
                 SETTINGS.active_project.get_instance(line).getInterfacesList()]
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print(str(DISPLAY))
        return self.columnize(interfacelist)

    def complete_connectpin(self, text, line, begidx, endidx):
        pinlist = []
        try:
            pinlist = self.completeargs(
                    text, line,
                    "<instancename>.<interfacename>.<portname>.<pinnum> " +
                    "<instancename>.<interfacename>.<portname>.<pinnum>")
        except Exception, error:
            print(str(error))
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
            self.isProjectOpen()
            self.checkargs(line,
                    "<instancename>.<interfacename>.<portname>.[pinnum] " +
                    "<instancename>.<interfacename>.<portname>.[pinnum]")
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        dest = arg[-1].split('.')
        if len(source) == 3:
            source.append(0)
        if len(dest) == 3:
            dest.append(0)
        try:
            SETTINGS.active_project.connectPin_cmd(
                    SETTINGS.active_project.get_instance(
                        source[0]).getInterface(
                            source[1]).getPort(
                                source[2]).getPin(source[3]),
                    SETTINGS.active_project.get_instance(
                        dest[0]).getInterface(
                            dest[1]).getPort(dest[2]).getPin(dest[3]))
        except Error, error:
            print(str(DISPLAY))
            print(str(error))
            return
        print DISPLAY

    def complete_setunconnectedvalue(self, text, line, begidx, endidx):
        portlist = []
        try:
            portlist = self.completeargs(text, line,
                 "<instancename>.<interfacename>.<portname> <uvalue>")
        except Exception, error:
            print(str(error))
        return portlist

    def do_setunconnectedvalue(self, line):
        """
Usage : setunconnectedvalue <instancename>.<interfacename>.<portname> <uvalue>
Force input port unconnected value
        """
        try:
            self.isProjectOpen()
            self.checkargs(line,
                    "<instancename>.<interfacename>.<portname> <uvalue>")
        except Exception, error:
            print DISPLAY
            print(str(e))
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        if len(arg) != 2:
            print "arguments error"
            return
        uvalue = arg[1].strip()

        if len(source) != 3:
            print("source arguments error")
            return
        try:
            SETTINGS.active_project.set_unconnected_value(source[0], source[1],
                                                          source[2], uvalue)
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        print DISPLAY

    def complete_connectport(self, text, line, begidx, endidx):
        portlist = []
        try:
            portlist = self.completeargs(text, line,
                           "<instancename>.<interfacename>.<portname> " +
                           "<instancename>.<interfacename>.<portname>")
        except Exception, error:
            print(str(error))
        return portlist

    def do_connectport(self, line):
        """
Usage : connectport \\
        <instancename>.<interfacename>.<portname> \\
        <instancename>.<interfacename>.<portname>
Connect all pins of two same size ports.
        """
        try:
            self.isProjectOpen()
            self.checkargs(line,
                    "<instancename>.<interfacename>.<portname> " +
                    "<instancename>.<interfacename>.<portname>")
        except Exception, error:
            print DISPLAY
            print(str(error))
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
            SETTINGS.active_project.connectPort(source[0],
                                                source[1],
                                                source[2],
                                                dest[0],
                                                dest[1],
                                                dest[2])
        except Error, e:
            print DISPLAY
            print e
            return
        print DISPLAY

    def complete_connectinterface(self, text, line, begidx, endix):
        buslist = []
        try:
            buslist = self.completeargs(text, line,
                                        "<instancename>.<interfacename> " +
                                        "<instancename>.<interfacename>")
        except Exception, error:
            print(str(error))
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
            self.isProjectOpen()
            self.checkargs(line,
               "<instancename>.<interfacename> <instancename>.<interfacename>")
        except Exception, error:
            print DISPLAY
            print(str(error))
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        dest = arg[-1].split('.')
        if (len(source) != 2) or (len(dest) != 2):
            print("Argument error")
            return
        try:
            SETTINGS.active_project.connectInterface(source[0],
                                                     source[1],
                                                     dest[0],
                                                     dest[1])
        except Error, error:
            print("<<interface " + source[1] +
                  " and interface " + dest[1] + " are not compatible>>")
            print DISPLAY
            print(str(error))
            return
        print DISPLAY

    def complete_delbusconnection(self, text, line, begidx, endidx):
        connectlist = []
        try:
            connectlist = \
                    self.completeargs(text, line,
                        "<masterinstancename>.<masterinterfacename> " +
                        "<slaveinstancename>.<slaveinterfacename>")
        except Exception, error:
            print(str(error))
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
            self.isProjectOpen()
            self.checkargs(line,
                    "<masterinstancename>.<masterinterfacename> " +
                    "<slaveinstancename>.<slaveinterfacename>")
        except Exception, error:
            print DISPLAY
            print(str(error))
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        dest = arg[-1].split('.')
        if (len(source) != 2) or (len(dest) != 2):
            print("Argument error")
            return
        try:
            SETTINGS.active_project.deleteBus(source[0],
                                              dest[0],
                                              source[1],
                                              dest[1])
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        print DISPLAY

    def complete_connectbus(self, text, line, begidx, endidx):
        buslist = []
        try:
            buslist = self.completeargs(text, line,
                                "<masterinstancename>.<masterinterfacename> " +
                                "<slaveinstancename>.<slaveinterfacename>")
        except Exception, error:
            print(str(error))
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
            self.isProjectOpen()
            self.checkargs(line,
                "<masterinstancename>.<masterinterfacename> " +
                "<slaveinstancename>.<slaveinterfacename>")
        except Exception, error:
            print DISPLAY
            print(str(error))
            return
        arg = line.split(' ')
        source = arg[0].split('.')
        dest = arg[-1].split('.')
        if (len(source) != 2) or (len(dest) != 2):
            print("Argument error")
            return
        try:
            SETTINGS.active_project.connectBus(source[0],
                                               source[1],
                                               dest[0],
                                               dest[1])
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        print DISPLAY

    def do_autoconnectbus(self, line):
        """\
Usage : autoconnectbus
Autoconnect bus if only one master in project
        """
        try:
            self.isProjectOpen()
            SETTINGS.active_project.autoConnectBus()
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        print DISPLAY

    def complete_delpinconnection(self, text, line, begidx, endidx):
        connectlist = []
        try:
            connectlist = \
                self.completeargs(text, line,
                        "<instancename>.<interfacename>.<portname>.<pinnum> " +
                        "<instancename>.<interfacename>.<portname>.<pinnum>")
        except Exception, error:
            print(str(error))
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
            self.isProjectOpen()
            self.checkargs(line,
                    "<instancename>.<interfacename>.<portname>.[pinnum] " +
                    "[instancename].[interfacename].[portname].[pinnum]")
        except Error, error:
            print DISPLAY
            print(str(error))
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
            SETTINGS.active_project.deletePinConnection_cmd(
                    source[0], source[1],
                    source[2], source[3],
                    dest[0], dest[1],
                    dest[2], dest[3])
        except Error, e:
            print DISPLAY
            print e
            return
        print DISPLAY
        print "Connection deleted"

    def complete_delinstance(self, text, line, begidx, endidx):
        componentlist = []
        try:
            componentlist = self.completeargs(text, line, "<instancename>")
        except Exception, error:
            print(str(error))
        return componentlist

    def do_delinstance(self, line):
        """\
Usage : delinstance <instancename>
Suppress a component from project
        """
        try:
            self.isProjectOpen()
            self.checkargs(line, "<instancename>")
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        try:
            SETTINGS.active_project.del_instance(line)
        except Error, error:
            print DISPLAY
            print error
            return
        print DISPLAY

    def do_check(self, line):
        """\
Usage : check
Check the project before code generation
        """
        try:
            self.isProjectOpen()
            SETTINGS.active_project.check()
        except Error, error:
            print DISPLAY
            print(str(error))
        print DISPLAY

    def complete_setaddr(self, text, line, begidx, endidx):
        addrlist = []
        try:
            addrlist = \
                    self.completeargs(text, line,
                                  "<slaveinstancename>.<slaveinterfacename> " +
                                  "<addressinhexa>")
        except Exception, error:
            print(str(error))
        return addrlist

    def do_setaddr(self, line):
        """\
Usage : setaddr <slaveinstancename>.<slaveinterfacename> <addressinhexa>
Set the base address of slave interface
        """
        try:
            self.isProjectOpen()
            self.checkargs(line,
                    "<slaveinstancename>.<slaveinterfacename> <addressinhexa>")
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        arg = line.split(' ')
        names = arg[0].split('.')
        if len(names) < 2:
            masterinterface = \
                    SETTINGS.active_project.get_instance(
                            names[0]).getSlaveInterfaceList()
            if len(masterinterface) != 1:
                print DISPLAY
                print("Error, need a slave interface name")
                return
            names.append(masterinterface[0].getName())

        try:
            interfaceslave = \
                    SETTINGS.active_project.get_instance(
                            names[0]).getInterface(names[1])
            interfacemaster = interfaceslave.getMaster()
            interfacemaster.allocMem.setAddressSlave(interfaceslave, arg[1])
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        print DISPLAY
        print("Base address " + arg[1] + " set")

    def do_listmasters(self, line):
        """\
Usage : listmaster
List master interface
        """
        try:
            self.isProjectOpen()
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        for master in SETTINGS.active_project.interfaces_master:
            print(master.parent.getInstanceName() + "." + master.getName())
        print DISPLAY

    def complete_getmapping(self, text, line, begidx, endidx):
        mappinglist = []
        try:
            mappinglist = \
                self.completeargs(text, line,
                                  "<masterinstancename>.<masterinterfacename>")
        except Exception, error:
            print(str(error))
        return mappinglist

    def do_getmapping(self, line=None):
        """\
Usage : getmapping <masterinstancename>.<masterinterfacename>
Return mapping for a master interface
        """
        try:
            self.isProjectOpen()
            self.checkargs(line, "<masterinstancename>.<masterinterfacename>")
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        arg = line.split(' ')
        names = arg[0].split('.')
        try:
            masterinterface = \
                    SETTINGS.active_project.get_instance(
                            names[0]).getInterface(names[1])
            print masterinterface.allocMem
        except Error, error:
            print DISPLAY
            print(str(error))
        print DISPLAY

    def complete_printxml(self, text, line, begidx, endidx):
        printlist = []
        try:
            printlist = self.completeargs(text, line, "<instancename>")
        except Exception, error:
            print(str(error))
        return printlist

    def do_printxml(self, line=None):
        """\
Usage : printxml <instancename>
Print instance in XML format
        """
        try:
            self.isProjectOpen()
            self.checkargs(line, "<instancename>")
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        print SETTINGS.active_project.get_instance(line)
        print DISPLAY

    def complete_info(self, text, line, begidx, endidx):
        infolist = []
        try:
            infolist = self.completeargs(text, line, "<instancename>")
        except Exception, error:
            print(str(error))
        return infolist

    def do_info(self, line=None):
        """\
Usage : info <instancename>
Print instance information
        """
        try:
            self.isProjectOpen()
            self.checkargs(line, "<instancename>")
            instance = SETTINGS.active_project.get_instance(line)
        except Error, error:
            print DISPLAY
            print error
            return
        print("Instance name :" + instance.getInstanceName())
        print("Component  name :" + instance.getName())
        print("description : " + instance.getDescription().strip())
        print("->Generics")
        for generic in instance.getGenericsList():
            print("%15s : " % generic.getName() + generic.getValue())
        print("->Interfaces")
        for interface in instance.getInterfacesList():
            if interface.getBusName() is not None:
                if interface.getClass() == "slave":
                    print("%-15s " % interface.getName() +
                          " Base address:" + hex(interface.getBaseInt()))
                elif interface.getClass() == "master":
                    print("%-15s :" % interface.getName())
                    for slave in interface.getSlavesList():
                        print(" " * 10 + "slave -> " +
                              slave.getInstanceName() + "." +
                              slave.getInterfaceName())
            else:
                print("%-15s :" % interface.getName())

            for port in interface.ports:
                print(" " * 5 + "%-15s" % port.getName() +
                      " s" + port.getSize())
                for pin in port.getPinsList():
                    print(" " * 8 + "pin"),
                    if pin.getNum() is not None:
                        print(pin.getNum() + ":"),
                    elif pin.isAll():
                        print "all",
                    first = True
                    for connection in pin.getConnections():
                        if first is not True:
                            print(" " * 8 + "|" + " " * 5),
                        first = False
                        print("-> " +
                              connection["instance_dest"] + "." +
                              connection["interface_dest"] + "." +
                              connection["port_dest"] + "." +
                              connection["pin_dest"])

    def complete_setgeneric(self, text, line, begidx, endidx):
        genericlist = []
        try:
            genericlist = \
              self.completeargs(text, line,
                                "<instancename>.<genericname> <genericvalue>")
        except Exception, error:
            print(str(error))
        return genericlist

    def do_setgeneric(self, line=None):
        """\
Usage : setgeneric <instancename>.<genericname> <genericvalue>
Set generic parameter
        """
        try:
            self.isProjectOpen()
            self.checkargs(line,
                           "<instancename>.<genericname> <genericvalue>")
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        args = line.split(" ")
        names = args[0].split(".")
        try:
            instance = SETTINGS.active_project.get_instance(names[0])
            generic = instance.getGeneric(names[1])
            if generic.isPublic() == "true":
                generic.setValue(args[1])
            else:
                raise Error("this generic can't be modified by user", 0)
        except Error, error:
            print DISPLAY
            print error
            return
        print DISPLAY
        print "Done"

    def do_description(self, line):
        """\
Usage : description <some word for description>
set the project description
        """
        SETTINGS.active_project.setDescription(line)
        print DISPLAY
        print("Description set : " + line)
        return

    def do_closeproject(self, line):
        """\
Usage : closeproject
Close the project
        """
        try:
            self.isProjectOpen()
        except Error, error:
            print DISPLAY
            print(str(error))
            return
        SETTINGS.active_project = None
        print DISPLAY
        print "Project closed"

    # Generate CODE
    def complete_generateintercon(self, text, line, begidx, endidx):
        interconlist = []
        try:
            interconlist = \
               self.completeargs(text, line,
                                 "<masterinstancename>.<masterinterfacename>")
        except Exception, error:
            print error
        return interconlist

    def do_generateintercon(self, line=None):
        """\
Usage : generateintercon <masterinstancename>.<masterinterfacename>
Generate intercon for master given in argument
        """
        try:
            self.isProjectOpen()
            self.checkargs(line, "<instancename>.<masterinterfacename>")
        except Error, error:
            print error
            return
        arg = line.split(' ')
        names = arg[0].split('.')
        if len(names) != 2:
            print "Arguments error"
            return
        try:
            SETTINGS.active_project.generateIntercon(names[0], names[1])
        except Error, error:
            print error
            return
        print DISPLAY

    def do_generatetop(self, line):
        """\
Usage : generatetop
Generate top component
        """
        try:
            self.isProjectOpen()
            SETTINGS.active_project.check()
            top = TopVHDL(SETTINGS.active_project)
            top.generate()
        except Error, error:
            print(str(error))
            return
        print DISPLAY
        print("Top generated with name : top_" +
                SETTINGS.active_project.getName() + ".vhd")

    def do_report(self, line):
        """\
Usage : report
Generate a report of the project
        """
        try:
            self.isProjectOpen()
            text = SETTINGS.active_project.generateReport()
        except Error, error:
            print DISPLAY
            print error
            return
        print DISPLAY
        print "report : "
        print text

    def isProjectOpen(self):
        """ check if project is open, raise error if not
        """
        if SETTINGS.active_project.isVoid():
            raise Error("No project open", 0)

    def do_listforce(self, line):
        """\
Usage : listforce
List all force configured for this project
        """
        try:
            for port in SETTINGS.active_project.getForcesList():
                print("port " + str(port.getName()) +
                      " is forced to " + port.force)
        except Error, error:
            print DISPLAY
            print error
            return

    def complete_setforce(self, text, line, begidx, endidx):
        pinlist = []
        try:
            pinlist = self.completeargs(text, line, "<forcename> <forcestate>")
        except Exception, error:
            print error
        return pinlist

    def do_setforce(self, line):
        """\
Usage : setpin <pinname> <state>
Set fpga pin state in 'gnd', 'vcc'. To unset use 'undef' value
        """

        try:
            self.isProjectOpen()
            self.checkargs(line, "<forcename> <forcestate>")
        except Error, error:
            print DISPLAY
            print error
            return

        arg = line.split(' ')
        portname = arg[-2]
        state = arg[-1]

        try:
            SETTINGS.active_project.set_force(portname, state)
        except Error, error:
            print DISPLAY
            print error
            return

    def do_setcolor(self, line):
        """\
Usage: setcolor [0/1]
Set 1 if you want color output, 0 else
        """
        arg = line.split(' ')
        value = arg[-1].strip()

        try:
            SETTINGS.setColor(value)
        except Error, error:
            print DISPLAY
            print error
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
        listdir = sy.listDirectory(path)
        listfile = sy.listFileType(path, PODSCRIPTEXT[1:])
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
        except IOError, error:
            try:
                self.stdin = open('%s.%s' % (fname,
                                             self.default_extension), 'r')
            except IOError:
                print 'Problem opening file %s: \n%s' % (fname, error)
                keepstate.restore()
                return
        self.use_rawinput = False
        self.prompt = self.continuation_prompt = ''
        SETTINGS.setScript(1)
        self.cmdloop()
        SETTINGS.setScript(0)
        self.stdin.close()
        keepstate.restore()
        self.lastcmd = ''
        return

    def do_version(self, line):
        """\
Usage : version
Print the version of POD
        """
        print "Peripherals On Demand version " + SETTINGS.version
