#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     componentcli.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  29/04/2009
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
__versionTime__ = "29/04/2009"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import cmd,os
#import readline
import periphondemand.bin.define

from   periphondemand.bin.utils import wrapperxml,settings,error
from   periphondemand.bin.utils import basecli,wrappersystem
from   periphondemand.bin.utils import wrappersystem as sy
from   periphondemand.bin.utils.display  import Display

from   periphondemand.bin.code.vhdl.topvhdl      import TopVHDL

from   periphondemand.bin.commandline               import *

from   periphondemand.bin.utils.settings import Settings
from   periphondemand.bin.utils.basecli  import BaseCli
from   periphondemand.bin.utils.error    import Error

from   periphondemand.bin.core.project     import Project
from   periphondemand.bin.core.component   import Component
from   periphondemand.bin.core.platform    import Platform

from   periphondemand.bin.code.intercon      import Intercon
from   periphondemand.bin.code.vhdl.topvhdl  import TopVHDL

from   periphondemand.bin.toolchain.synthesis   import Synthesis
from   periphondemand.bin.toolchain.simulation  import Simulation
from   periphondemand.bin.toolchain.driver      import Driver

settings = Settings()
display  = Display()

class ComponentCli(BaseCli):
    """ Component management command line interface
    """
    def __init__(self,parent=None):
        BaseCli.__init__(self,parent)

    def do_create(self,arg):
        """\
Usage : create <componentname>.<versionname>
Create new component in current library
        """
        try:
            self.checkargs(arg,"<componentname>.<versionname>")
        except Error,e:
            print display
            print e
            return
        componentname = arg.split(".")[0].strip()
        versionname = arg.split(".")[1].strip()

        library = settings.active_library
        try:
            if not self.componentLoaded():
                settings.active_component = Component()
            settings.active_component.createComponent(componentname,
                                                      library.getLibName(),
                                                      versionname)
        except Error,e:
            print display
            print e
            return
        print display

    def complete_load(self,text,line,begidx,endidx):
        componentlist = []
        try:
            componentlist = self.completeargs(text,line,"<componentname>.[componentversion]")
        except Exception,e:
            print e
        return componentlist

    def do_load(self,arg):
        """\
Usage : load <componentname>.[version]
Load component from current library
        """
        library = settings.active_library
        try:
            if not self.componentLoaded():
                settings.active_component = Component()
            self.checkargs(arg,"<componentname>.[componentversion]")
            arglist = arg.split(".")
            componentname = arglist[0]
            if len(arglist) > 1:
                versionname = arglist[1]
            else:
                versionname = None
            settings.active_component.loadComponent(componentname,library.getLibName(),versionname)
        except Error,e:
            print display
            print e
            return
        print display

    def complete_addtophdlfile(self,text,line,begidx,endidx):
        path = line.split(" ")[1]
        if path.find("/") == -1: # sub
            path = ""
        elif text.split() == "": # sub/sub/
            path = "/".join(path)+"/"
        else: # sub/sub
            path = "/".join(path.split("/")[0:-1]) + "/"
        listdir = sy.listDirectory(path)
        listfile = sy.listFileType(path,"vhd")
        listfile.extend(listdir)
        return self.completelist(line,text,listfile)

    def do_addtophdlfile(self,arg):
        """\
Usage : addtophdlfile <hdlfilepath>
Add the top HDL file in component, the file will be copied in component directory.
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return
        try:
            self.checkargs(arg,"<hdlfilepath>.vhd")
            if not self.componentLoaded():
                raise Error("Load/Create a component before")
            settings.active_component.setHDLfile(arg,istop=1)
        except Error,e:
            print display
            print e
            return
        print display

    def complete_addhdlfile(self,text,line,begidx,endidx):
        return self.complete_addtophdlfile(text,line,begidx,endidx)

    def do_addhdlfile(self,arg):
        """\
Usage : addhdlfile <hdlfilepath>
Add an HDL file in component, the file will be copied in component directory.
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return
        try:
            self.checkargs(arg,"<hdlfilepath>.vhd")
            if not self.componentLoaded():
                raise Error("Load/Create a component before")
            settings.active_component.setHDLfile(arg)
        except Error,e:
            print display
            print e
            return
        print display

    def do_delhdlfile(self,arg):
        """\
Usage : delhdlfile <hdlfilename>
Suppress a HDL file from component
        """
        print "TODO"

    def do_save(self,arg):
        """\
Usage : save
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return

        try:
            settings.active_component.saveComponent()
        except Error,e:
            print display
            print e
            return
        print display

    def do_setdescription(self,arg):
        """\
Usage : setdescription description
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return

        try:
            settings.active_component.setDescription(arg)
        except Error,e:
            print display
            print e
            return
        print display

    def do_listinterfaces(self,arg):
        """\
Usage : listinterfaces
List interface in current component
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return

        try:
            interfacelist = settings.active_component.getInterfacesList()
        except Error,e:
            print display
            print e
            return
        print display
        return self.columnize([interface.getName() \
                            for interface in interfacelist])

    def do_addinterface(self,arg):
        """\
Usage : addinterface <interfacename>
Add an interface in component
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return

        try:
            self.checkargs(arg,"<interfacename>")
            settings.active_component.createInterface(arg)
        except Error,e:
            print e
            print display
            return
        print display

    def complete_setinterface(self,text,line,begidx,endidx):
        #TODO
        pass

    def do_setinterface(self,arg):
        """\
Usage : setinterface <interfacename> <attribute>=<value>
set interface attributes
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return

        #TODO
        pass

    def complete_delport(self,text,line,begidx,endidx):
        #TODO
        pass

    def do_delport(self,arg):
        """\
Usage : delport <portname> <interfacename>
Suppress port from interface
        """
        print "TODO"
        pass

    def complete_addport(self,text,line,begidx,endidx):
        #TODO
        pass

    def do_addport(self,arg):
        """\
Usage : addport <portname> <interfacename>
Add port in interface
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return

        try:
            self.checkargs(arg,"<portname> <interfacename>")
            arglist = (arg.split())
            portname = arglist[0].strip()
            interfacename = arglist[1].strip()
            settings.active_component.addPort(portname,interfacename)
        except Error,e:
            print display
            print e
            return
        print display

    def do_listports(self,arg):
        """\
Usage : listport
List port available in component
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return

        try:
            display_port = settings.active_component.getPortsList()
        except Error,e:
            print display
            print e
            return
        print display
        for key in display_port:
            print key+": ",
            for portname in display_port[key]:
                print portname+", ",
            print ""

    def complete_setinterface(self,text,line,begidx,endidx):
        #TODO
        pass

    def do_setinterface(self,arg):
        """\
Usage : setinterface <interface_name> <attribute_name>=<attribute_value>
Add or modify attribute value for a node
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return
        try:
            self.checkargs(arg,"<name> <attributename>=<attributevalue>")
            name = arg.split()[0]
            attr = arg.split()[1]
            attributename = attr.split("=")[0]
            attributevalue = attr.split("=")[1]
            settings.active_component.setInterface(name,attributename,attributevalue)
        except Error,e:
            print display
            print e
        print display

    def complete_setport(self,text,line,begidx,endidx):
        #TODO
        pass

    def do_setport(self,arg):
        """\
Usage : setport <interface_name>.<port_name> <attribute_name>=<attribute_value>
Add or modify attribute value for a port
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return
        try:
            self.checkargs(arg,"<interface_name>.<port_name> <attributename>=<attributevalue>")
            interface_name = arg.split()[0].split(".")[0]
            port_name = arg.split()[0].split(".")[1]
            attr = arg.split()[1]
            attribute_name = attr.split("=")[0]
            attribute_value = attr.split("=")[1]
            settings.active_component.setPort(interface_name,port_name,
                                                   attribute_name,attribute_value)
        except Error,e:
            print display
            print e
        print display

    def do_setregister(self,arg):
        """\
Usage : setregister <interface_name>.<register_name> <attribute_name>=<attribute_value>
Add or modify attribute value for a register
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return
        try:
            self.checkargs(arg,"<interface_name>.<port_name> <attributename>=<attributevalue>")
            interface_name = arg.split()[0].split(".")[0]
            register_name = arg.split()[0].split(".")[1]
            attr = arg.split()[1]
            attribute_name = attr.split("=")[0]
            attribute_value = attr.split("=")[1]
            settings.active_component.setRegister(interface_name,register_name,
                                                   attribute_name,attribute_value)
        except Error,e:
            print display
            print e
        print display

    def do_addregister(self,arg):
        """\
Usage : addregister <interface_name> <register_name>
Add register in interface, interface must be a bus slave
        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return
        try:
            self.checkargs(arg,"<interface_name> <register_name>")
            interface_name = arg.split()[0]
            register_name = arg.split()[1]
            settings.active_component.addRegister(interface_name,register_name)
        except Error,e:
            print display
            print e
        print display

    def complete_setgeneric(self,text,line,begidx,endidx):
        #TODO
        pass

    def do_setgeneric(self,arg):
        """\
Usage : addgeneric <generic_name> <attribute_name>=<attribute_value>

        """
        if not self.componentLoaded():
            print Error("No component loaded")
            return
        try:
            self.checkargs(arg,"<generic_name> <attribute_name>=<attribute_value>")
            generic_name = arg.split()[0]
            attribute_name = arg.split()[1].split("=")[0]
            attribute_value = arg.split()[1].split("=")[1]
            settings.active_component.setGeneric(generic_name,attribute_name,attribute_value)
        except Error,e:
            print display
            print e
        print display

    def componentLoaded(self):
        if settings.active_component == None:
            return None
        return 1

    def complete_printport(self,text,line,begidx,endidx):
        #TODO
        pass

    def do_printport(self,arg):
        """\
Usage : printport <interfacename>.<portname>
Print port informations
        """
        #TODO
        pass

    def complete_printinterface(self,text,line,begidx,endidx):
        #TODO
        pass

    def do_printinterface(self,arg):
        """\
Usage : printinterface <interfacename>
Print interface informations
        """
        #TODO
        pass

if __name__ == "__main__":
    print "componentcli class test\n"
    print componentcli.__doc__

