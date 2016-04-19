#! /usr/bin/python3
# - * - coding: utf-8 - * -
# ----------------------------------------------------------------------------
# Name:     wishbone8.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  13/05/2008
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
""" Manage wishbone 8bits data bus """

import time
import datetime

from periphondemand.bin.define import TEMPLATESPATH
from periphondemand.bin.define import HEADERTPL
from periphondemand.bin.define import VHDLEXT
from periphondemand.bin.define import ONETAB
from periphondemand.bin.define import COMPONENTSPATH
from periphondemand.bin.define import HDLDIR

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils import wrappersystem as sy

from periphondemand.bin.core.component import Component
from periphondemand.bin.core.port import Port
from periphondemand.bin.core.interface import Interface
from periphondemand.bin.core.hdl_file import HdlFile

SETTINGS = Settings()


def header(author, intercon):
    """ return vhdl header
    """
    header = open(SETTINGS.path + TEMPLATESPATH + "/" + HEADERTPL, "r").read()
    header = header.replace("$tpl:author$", author)
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
            entity = entity + ONETAB * 2 + "%-40s" % port.name +\
                " : " + "%-5s" % port.direction
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
    for slave in masterinterface.slaves:
        archead = archead + ONETAB + "signal " +\
            "%-40s" % (slave.instancename + "_" +
                       slave.interfacename + "_cs") +\
            " : std_logic : = '0' ;\n"
    archead = archead + "begin\n"
    return archead


def connectClockandReset(masterinterface, intercon):
    """ Connect clock and reset
    """

    bus = masterinterface.bus
    masterinstance = masterinterface.parent
    masterinstancename = masterinstance.instancename
    masterinterfacename = masterinterface.name
    masterresetname = masterinstancename + "_" +\
        masterinterface.get_port_by_type(
            bus.sig_name("master", "reset")).name
    masterclockname = masterinstancename + "_" +\
        masterinterface.get_port_by_type(
            bus.sig_name("master", "clock")).name
    out = "\n" + ONETAB + "-- Clock and Reset connection\n"

    for slave in masterinterface.slaves:
        slaveinstance = slave.get_instance()
        slaveinterface = slave.get_interface()
        slaveinstancename = slave.instancename
        slaveresetname = slaveinstancename + "_" +\
            slaveinterface.get_port_by_type(
                bus.sig_name("slave", "reset")).name
        slaveclockname = slaveinstancename + "_" +\
            slaveinterface.get_port_by_type(
                bus.sig_name("slave", "clock")).name
        # reset
        out = out + ONETAB + slaveresetname + " < = " + masterresetname + ";\n"
        # clock
        out = out + ONETAB + slaveclockname + " < = " + masterclockname + ";\n"

    return out


def addressdecoding(masterinterface, masterinstancename, intercon):
    """ generate VHDL for address decoding
    """
    bus = masterinterface.bus
    masterinstance = masterinterface.parent
    masterinstancename = masterinstance.instancename
    rst_name = masterinstancename + "_" +\
        masterinterface.get_port_by_type(
            bus.sig_name("master", "reset")).name
    clk_name = masterinstancename + "_" +\
        masterinterface.get_port_by_type(
            bus.sig_name("master", "clock")).name
    masteraddressname = masterinstance.instancename + "_" +\
        masterinterface.get_port_by_type(
            bus.sig_name("master", "address")).name
    masterstrobename = masterinstancename + "_" +\
        masterinterface.get_port_by_type(
            bus.sig_name("master", "strobe")).name
    mastersizeaddr = masterinterface.addr_port_size

    out = ONETAB + "-----------------------\n"
    out = out + ONETAB + "-- Address decoding  --\n"
    out = out + ONETAB + "-----------------------\n"
    for slave in masterinterface.slaves:
        slaveinstance = slave.get_instance()
        slaveinterface = slave.get_interface()
        slavesizeaddr = slave.get_interface().addr_port_size
        slavebase_address = slaveinterface.base_addr
        if slavesizeaddr > 0:
            slaveaddressport = slave.get_interface().get_port_by_type(
                bus.sig_name("slave", "address"))
            slavename_addr = slaveinstance.instancename +\
                "_" + slaveaddressport.name
        if slavesizeaddr == 1:
            out = out + ONETAB + slavename_addr + " < = " + masteraddressname +\
                "(0);\n"
        elif slavesizeaddr > 1:
            out = out + ONETAB + slavename_addr + " < = " + masteraddressname +\
                "(" + str(slavesizeaddr-1) + " downto 0);\n"
    out = out + "\n"

    out = out + ONETAB + "decodeproc : process(" + clk_name +\
        ", " + rst_name + ", " + masteraddressname + ")\n"
    out = out + ONETAB + "begin\n"

    # initialize
    out = out + ONETAB * 2 + "if " + rst_name + " = '1' then\n"
    for slave in masterinterface.slaves:
        slaveinstance = slave.get_instance()
        slaveinterface = slave.get_interface()
        chipselectname = slaveinstance.instancename +\
            "_" + slaveinterface.name + "_cs"
        out = out + ONETAB * 3 + chipselectname + " < = '0';\n"
    out = out + ONETAB * 2 + "elsif rising_edge(" + clk_name + ") then\n"

    for slave in masterinterface.slaves:
        slaveinstance = slave.get_instance()
        slaveinterface = slave.get_interface()
        chipselectname = slaveinstance.instancename +\
            "_" + slaveinterface.name + "_cs"
        slavesizeaddr = slave.get_interface().addr_port_size
        slavebase_address = slaveinterface.base_addr
        if slavesizeaddr > 0:
            slaveaddressport = slave.get_interface().get_port_by_type(
                bus.sig_name("slave", "address"))
            slavename_addr = slaveinstance.instancename +\
                "_" + slaveaddressport.name

        out = out + "\n"
        out = out + ONETAB * 3 + "if " + masteraddressname + "(" +\
            str(int(mastersizeaddr-1)) + " downto " + str(slavesizeaddr) +\
            ') = "' +\
            sy.inttobin(slavebase_address, int(mastersizeaddr))[:-(slavesizeaddr)] +\
            '"' + " and " + masterstrobename + " = '1' then\n"

        out = out + ONETAB * 4 + chipselectname + " < = '1';\n"
        out = out + ONETAB * 3 + "else\n"
        out = out + ONETAB * 4 + chipselectname + " < = '0';\n"
        out = out + ONETAB * 3 + "end if;\n"

    out = out + "\n" + ONETAB * 2 + "end if;\n" + ONETAB +\
        "end process decodeproc;\n\n"
    return out


def controlslave(masterinterface, intercon):
    """ Connect controls signals for slaves
    """

    bus = masterinterface.bus
    masterinstance = masterinterface.parent
    masterinstancename = masterinstance.instancename
    masterinterfacename = masterinterface.name
    masterstrobename = masterinstancename + "_" +\
        masterinterface.get_port_by_type(
            bus.sig_name("master", "strobe")).name
    mastercyclename = masterinstancename + "_" +\
        masterinterface.get_port_by_type(
            bus.sig_name("master", "cycle")).name

    out = ONETAB + "-----------------------------\n"
    out = out + ONETAB + "-- Control signals to slave\n"
    out = out + ONETAB + "-----------------------------\n"

    for slave in masterinterface.slaves:
        slaveinstance = slave.get_instance()
        slaveinterface = slave.get_interface()
        slaveinstancename = slave.instancename
        slavestrobename = slaveinstancename + "_" +\
            slaveinterface.get_port_by_type(
                bus.sig_name("slave", "strobe")).name
        slavecyclename = slaveinstancename + "_" +\
            slaveinterface.get_port_by_type(
                bus.sig_name("slave", "cycle")).name

        chipselectname = slaveinstancename + "_" +\
            slaveinterface.name + "_cs"

        out = out + "\n" + ONETAB + "-- for " + slaveinstancename + "\n"
        # strobe
        out = out + ONETAB + slavestrobename + " < = (" + masterstrobename +\
            " and " + chipselectname + " );\n"
        # cycle
        out = out + ONETAB + slavecyclename + " < = (" + mastercyclename +\
            " and " + chipselectname + " );\n"

        # write connection if read/write, read or write
        try:
            datainname = slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "datain")).name
        except PodError:
            datainname = None

        try:
            dataoutname = slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "dataout")).name
        except PodError:
            dataoutname = None

        if datainname and dataoutname:
            # write
            out = out + ONETAB + slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "write")).name +\
                " < = (" + masterinstancename + "_" +\
                masterinterface.get_port_by_type(
                    bus.sig_name("master", "write")).name +\
                " and " + chipselectname + " );" + "\n"
        elif datainname:
            # write
            out = out + ONETAB +\
                slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "write")).name +\
                " < = '1';\n"
        elif dataoutname:
            # write
            out = out + ONETAB +\
                slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "write")).name +\
                " < = '0';\n"
        if datainname:
            out = out + ONETAB +\
                slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "datain")).name +\
                " < = " +\
                masterinstancename + "_" +\
                masterinterface.get_port_by_type(
                    bus.sig_name("master", "dataout")).name +\
                " when (" +\
                masterinstancename + "_" +\
                masterinterface.get_port_by_type(
                    bus.sig_name("master", "write")).name +\
                " and " + chipselectname +\
                " ) = '1' else (others = > '0');" + "\n"
    return out


def controlmaster(masterinterface, intercon):
    bus = masterinterface.bus
    masterinstance = masterinterface.parent
    masterinstancename = masterinstance.instancename
    masterinterfacename = masterinterface.name

    out = "\n\n" + ONETAB + "-------------------------------\n"
    out = out + ONETAB + "-- Control signal for master --\n"
    out = out + ONETAB + "-------------------------------\n"

    out = out + ONETAB + masterinstance.instancename + "_"
    out = out + masterinterface.get_port_by_type(
        bus.sig_name("master", "datain")).name
    out = out + " < = "
    # READDATA
    for slave in masterinterface.slaves:
        slaveinstance = slave.get_instance()
        slaveinterface = slave.get_interface()
        slaveinterfacename = slaveinterface.name
        slaveinstancename = slave.instancename
        try:
            dataoutname = slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "dataout")).name
            out = out + " " + dataoutname
            out = out + " when " + slaveinstancename + "_" +\
                slaveinterfacename + "_cs = '1' else\n"
            out = out + ONETAB * 9 + "  "
        except PodError, e:
            pass
    out = out + " (others = > '0');\n"

    # ACK
    out = out + ONETAB + masterinstance.instancename + "_"
    out = out + masterinterface.get_port_by_type(
        bus.sig_name("master", "ack")).name
    out = out + " < = "
    count = 0
    if masterinterface.slaves:
        for slave in masterinterface.slaves:
            slaveinstance = slave.get_instance()
            slaveinterface = slave.get_interface()
            slaveinterfacename = slaveinterface.name
            slaveinstancename = slave.instancename
            if count == 0:
                out = out + " "
                count = 1
            else:
                out = out + "\n" + ONETAB * 9 + "or \n"
                out = out + ONETAB * 8
            out = out + "(" + slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "ack")).name +\
                " and " + slaveinstancename + "_" + slaveinterfacename + "_cs)"
    else:
        out = out + "'0'"
    out = out + ";\n"
    return out


def architectureFoot(intercon):
    """ Write foot architecture code
    """
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

    listslave = masterinterface.slaves
    listinterfacesyscon = []
    for slaveinstance in [slave.get_instance() for slave in listslave]:
        listinterfacesyscon.append(slaveinstance.get_one_syscon())
    listinterfacesyscon.append(masterinstance.get_one_syscon())

    # Clock and Reset connection
    VHDLcode = VHDLcode +\
        connectClockandReset(masterinterface, intercon)

    # address decoding
    VHDLcode = VHDLcode +\
        addressdecoding(masterinterface, masterinstance, intercon)

    # controls slaves
    VHDLcode = VHDLcode + controlslave(masterinterface, intercon)
    # controls master
    VHDLcode = VHDLcode + controlmaster(masterinterface, intercon)
    # Foot
    VHDLcode = VHDLcode + architectureFoot(intercon)

    # saving
    if not sy.dir_exist(SETTINGS.projectpath + COMPONENTSPATH + "/" +
                        intercon.instancename + "/" + HDLDIR):
        sy.mkdir(SETTINGS.projectpath + COMPONENTSPATH + "/" +
                 intercon.instancename + "/" + HDLDIR)
    afile = open(SETTINGS.projectpath + COMPONENTSPATH + "/" +
                 intercon.instancename + "/" + HDLDIR + "/" +
                 intercon.instancename + VHDLEXT, "w")
    afile.write(VHDLcode)
    afile.close()
    # hdl file path
    hdl = HdlFile(intercon,
                  filename=intercon.instancename + VHDLEXT,
                  istop=1, scope="both")
    intercon.add_hdl_file(hdl)
    return VHDLcode
