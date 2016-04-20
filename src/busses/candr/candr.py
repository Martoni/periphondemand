#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     candr.py
# Purpose:
# Authors:   Fabien Marteau <fabien.marteau@armadeus.com>
#            Gwenhael Goavec-Merou <gwenhael.goavec-merou@armadeus.com>
# Created:  29/04/2011
# ----------------------------------------------------------------------------
#  Copyright (2011)  Armadeus Systems
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
""" Manage Clock and Reset bus """

import datetime

from periphondemand.bin.define import ONETAB
from periphondemand.bin.define import TEMPLATESPATH
from periphondemand.bin.define import HEADERTPL
from periphondemand.bin.define import COMPONENTSPATH
from periphondemand.bin.define import HDLDIR
from periphondemand.bin.define import VHDLEXT

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils import wrappersystem as sy

from periphondemand.bin.core.hdl_file import HdlFile

SETTINGS = Settings()


def header(author, intercon):
    """ return vhdl header
    """
    header = open(SETTINGS.path + TEMPLATESPATH + "/" + HEADERTPL, "r").read()
    header = header.replace("$tpl:date$", str(datetime.date.today()))
    header = header.replace("$tpl:filename$", intercon.name + VHDLEXT)
    header = header.replace("$tpl:abstract$", intercon.description)
    return header


def entity(intercon):
    """ generate entity
    """
    entity = "Entity " + intercon.name + " is\n"
    entity = entity + ONETAB + "port\n" + ONETAB + "(\n"
    for interface in intercon.interfaces:
        entity = entity + "\n" + ONETAB * 2 + "-- " +\
            interface.name + " connection\n"
        for port in interface.ports:
            entity = entity + ONETAB * 2 + "%-40s" % port.name + " : " +\
                "%-5s" % port.direction
            if port.max_pin_num == port.min_pin_num:
                entity = entity + "std_logic;\n"
            else:
                entity = entity + "std_logic_vector(" + port.max_pin_num +\
                    " downto " + port.min_pin_num + ");\n"
    # Suppress the #!@ last semicolon
    entity = entity[:-2]
    entity = entity + "\n"

    entity = entity + ONETAB + ");\n" + "end entity;\n\n"
    return entity


def architectureHead(masterinterface, intercon):
    """ Generate the head architecture
    """
    archead = "architecture " + intercon.name + "_1 of " +\
        intercon.name + " is\n"
    archead = archead + "begin\n"
    return archead


def connectClockandReset(masterinterface, intercon):
    """ Connect clock and reset
    """
    bus = masterinterface.bus
    masterinstance = masterinterface.parent
    masterinstancename = masterinstance.instancename
    masterresetname = masterinstancename + "_" +\
        masterinterface.get_port_by_type(bus.sig_name("master",
                                                      "reset")).name
    masterclockname = masterinstancename + "_" +\
        masterinterface.get_port_by_type(bus.sig_name("master",
                                                      "clock")).name

    out = "\n" + ONETAB + "-- Clock and Reset connection\n"
    for slave in masterinterface.slaves:
        slaveinterface = slave.get_interface()
        slaveinstancename = slave.instancename
        slaveresetname = slaveinstancename + "_" +\
            slaveinterface.get_port_by_type(
                bus.sig_name("slave", "reset")).name
        slaveclockname = slaveinstancename + "_" +\
            slaveinterface.get_port_by_type(
                bus.sig_name("slave", "clock")).name
        out = out + "\n" + ONETAB + "-- for " + slaveinstancename + "\n"
        # reset
        out = out + ONETAB + slaveresetname + " <= " + masterresetname + ";\n"
        # clock
        out = out + ONETAB + slaveclockname + " <= " + masterclockname + ";\n"
    return out


def architectureFoot(intercon):
    """ Write foot architecture code """
    out = "\nend architecture " + intercon.name + "_1;\n"
    return out


def generate_intercon(masterinterface, intercon):
    """Generate intercon VHDL code for wishbone16 bus
    """
    masterinstance = masterinterface.parent
    project = masterinstance.parent

    # comment and header
    VHDLcode = header(SETTINGS.author, intercon)
    # entity
    VHDLcode = VHDLcode + entity(intercon)
    VHDLcode = VHDLcode + architectureHead(masterinterface, intercon)
    # Clock and Reset connection
    VHDLcode = VHDLcode + connectClockandReset(masterinterface, intercon)

    # Foot
    VHDLcode = VHDLcode + architectureFoot(intercon)

    # saving
    if not sy.dir_exist(SETTINGS.projectpath +
                        COMPONENTSPATH + "/" +
                        intercon.instancename + "/" + HDLDIR):
        sy.mkdir(SETTINGS.projectpath +
                 COMPONENTSPATH + "/" +
                 intercon.instancename + "/" + HDLDIR)
    afile = open(SETTINGS.projectpath + COMPONENTSPATH + "/" +
                 intercon.instancename +
                 "/" + HDLDIR + "/" + intercon.instancename + VHDLEXT,
                 "w")
    afile.write(VHDLcode)
    afile.close()
    # hdl file path
    hdl = HdlFile(intercon,
                  filename=intercon.instancename + VHDLEXT,
                  istop=1, scope="both")
    intercon.add_hdl_file(hdl)
    return VHDLcode
