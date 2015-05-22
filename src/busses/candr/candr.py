#! /usr/bin/python
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

from periphondemand.bin.core.hdl_file import Hdl_file

SETTINGS = Settings()


def header(author, intercon):
    """ return vhdl header
    """
    header = open(SETTINGS.path + TEMPLATESPATH + "/" + HEADERTPL, "r").read()
    header = header.replace("$tpl:date$", str(datetime.date.today()))
    header = header.replace("$tpl:filename$", intercon.getName() + VHDLEXT)
    header = header.replace("$tpl:abstract$", intercon.getDescription())
    return header


def entity(intercon):
    """ generate entity
    """
    entity = "Entity " + intercon.getName() + " is\n"
    entity = entity + ONETAB + "port\n" + ONETAB + "(\n"
    for interface in intercon.getInterfacesList():
        entity = entity + "\n" + ONETAB * 2 + "-- " +\
            interface.getName() + " connection\n"
        for port in interface.ports:
            entity = entity + ONETAB * 2 + "%-40s" % port.getName() + " : " +\
                "%-5s" % port.direction
            if port.size == "1":
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
    archead = "architecture " + intercon.getName() + "_1 of " +\
        intercon.getName() + " is\n"
    archead = archead + "begin\n"
    return archead


def connectClockandReset(masterinterface, intercon):
    """ Connect clock and reset
    """
    bus = masterinterface.getBus()
    masterinstance = masterinterface.parent
    masterinstancename = masterinstance.getInstanceName()
    masterresetname = masterinstancename + "_" +\
        masterinterface.getPortByType(bus.getSignalName("master",
                                                        "reset")).getName()
    masterclockname = masterinstancename + "_" +\
        masterinterface.getPortByType(bus.getSignalName("master",
                                                        "clock")).getName()

    out = "\n" + ONETAB + "-- Clock and Reset connection\n"
    for slave in masterinterface.getSlavesList():
        slaveinterface = slave.getInterface()
        slaveinstancename = slave.getInstanceName()
        slaveresetname = slaveinstancename + "_" +\
            slaveinterface.getPortByType(
                bus.getSignalName("slave", "reset")).getName()
        slaveclockname = slaveinstancename + "_" +\
            slaveinterface.getPortByType(
                bus.getSignalName("slave", "clock")).getName()
        out = out + "\n" + ONETAB + "-- for " + slaveinstancename + "\n"
        # reset
        out = out + ONETAB + slaveresetname + " <= " + masterresetname + ";\n"
        # clock
        out = out + ONETAB + slaveclockname + " <= " + masterclockname + ";\n"
    return out


def architectureFoot(intercon):
    """ Write foot architecture code """
    out = "\nend architecture " + intercon.getName() + "_1;\n"
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
    if not sy.dirExist(SETTINGS.projectpath +
                       COMPONENTSPATH + "/" +
                       intercon.getInstanceName() + "/" + HDLDIR):
        sy.makeDirectory(SETTINGS.projectpath +
                         COMPONENTSPATH + "/" +
                         intercon.getInstanceName() + "/" + HDLDIR)
    afile = open(SETTINGS.projectpath + COMPONENTSPATH + "/" +
                 intercon.getInstanceName() +
                 "/" + HDLDIR + "/" + intercon.getInstanceName() + VHDLEXT,
                 "w")
    afile.write(VHDLcode)
    afile.close()
    # hdl file path
    hdl = Hdl_file(intercon,
                   filename=intercon.getInstanceName() + VHDLEXT,
                   istop=1, scope="both")
    intercon.addHdl_file(hdl)
    return VHDLcode
