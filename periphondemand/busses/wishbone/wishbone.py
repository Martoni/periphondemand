#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     wishbone16.py
# Purpose:
# Author:   Gwenhael Goavec-Merou <gwenhael.goavec-merou@trabucayre.com>
#           Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  22/07/2015
# ----------------------------------------------------------------------------
#  Copyright (2015)  Armadeus Systems
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
""" Manage wishbone data bus"""

import time
import datetime
import math

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


def get_list_slave_size(masterinterface, port_name=None):
    bus = masterinterface.bus
    data_size = []
    for slave in masterinterface.slaves:
        for i in slave.get_instance().interfaces:
            if i.bus_name == "wishbone":
                if port_name is not None:
                    try:
                        i.get_port_by_type(
                            bus.sig_name("slave", port_name))
                    except PodError:
                        continue
                data_size.append(int(i.data_size))
    return list(set(data_size))


def architectureHead(masterinterface, intercon):
    """ Generate the head architecture
    """
    addr_size = masterinterface.get_port_by_type("ADR").max_pin_num
    data_size = get_list_slave_size(masterinterface, "datain")
    bus = masterinterface.bus
    masterinstance = masterinterface.parent
    masterinstancename = masterinstance.instancename

    archead = "architecture " + intercon.name + "_1 of " +\
        intercon.name + " is\n"

    # create new data signal
    for size in data_size:
        # all writedata used with mux to adapt size
        archead = archead + ONETAB + "signal " +\
            "%-20s" % ("writedata" + str(size) + "_s") + \
            " : std_logic_vector(" + str(size-1) + " downto 0);\n"
    # local readdata with LSB added
    archead = archead + ONETAB + "signal " + \
        "%-20s" % ("wbm_address_s") + \
        " : std_logic_vector(" + addr_size + " downto 0);\n"

    data_size = int(masterinterface.data_size)-1
    for slave in masterinterface.slaves:
        archead = archead + ONETAB + "signal " +\
            "%-20s" % (slave.instancename + "_" +
                       slave.interfacename + "_cs") +\
            " : std_logic := '0' ;\n"
        # slave readdata reconstruct to match master readdata
        slaveit = slave.get_interface()
        try:
            slaveit.get_port_by_type(
                bus.sig_name("slave", "dataout"))
            archead = archead + ONETAB + "signal " +\
                "%-20s" % (slave.instancename + "_readdata_s") + \
                " : std_logic_vector(" + str(data_size) + " downto 0);\n"
        except PodError:
            pass

    # byte_en slave
    for size in get_list_slave_size(masterinterface, "byteen"):
        slavesize = int(masterinterface.data_size) / size
        archead = archead + ONETAB + "signal " + \
            "%-20s" % ("byte_enable" + str(size) + "_s") + \
            " : std_logic_vector(" + str(slavesize-1) + " downto 0);\n"
    archead = archead + "begin\n"
    return archead


def genCaseByteEnable(masterinterface):
    out = ""
    bus = masterinterface.bus

    byte_en = masterinterface.get_port_by_type("BYE")
    byte_en_name = masterinterface.parent.instancename + "_" + byte_en.name
    byte_en_size = byte_en.real_size
    write_bus = masterinterface.get_port_by_type(
        masterinterface.bus.sig_name("master", "dataout"))
    write_bus_name = masterinterface.parent.instancename + "_" + \
        write_bus.name
    master_size = write_bus.real_size
    addr_inst = masterinterface.get_port_by_type(
        masterinterface.bus.sig_name("master", "address"))
    addr_bus = masterinterface.parent.instancename + "_" + addr_inst.name
    addr_size = addr_inst.max_pin_num
    shift = int(math.log(int(master_size) / 8, 2))

    masteraddressname = "wbm_address_s"

    # writedata mux generation
    data_size = get_list_slave_size(masterinterface, "datain")
    for size in data_size:
        nb_byte = size / 8
        mask = pow(2, nb_byte)-1

        out += ONETAB + "writedata" + str(size) + "_s <= "

        if int(size) == int(master_size):
            out += write_bus_name
        else:
            bitsize = int(byte_en_size / nb_byte)
            for i in range(bitsize):
                val = bin(int(mask * pow(2, nb_byte*i)))[2:]
                out += write_bus_name + "(" + \
                    str(((i+1) * size)-1) + " downto " + str(i * size) + ")"
                if i < bitsize-1:
                    out += ' when ' + byte_en_name + ' = "' + \
                        val.zfill(byte_en_size) + '" else \n' + 2 * ONETAB
        out += ";\n\n"

    # addr reconstruct
    data_size = get_list_slave_size(masterinterface)

    if len(data_size) == 1 and data_size[0] == master_size:
        out += ONETAB + masteraddressname + " <= " + addr_bus + ";\n"
    else:
        slave_addr = masteraddressname + "(" + str(shift-1) + " downto 0) <= "
        out += ONETAB + masteraddressname + "(" + str(addr_size) + \
            " downto " + str(shift) + ") <= " + \
            addr_bus + "(" + str(addr_size) + " downto " + str(shift) + ");\n"
        out += ONETAB + slave_addr
        for size in data_size:
            if not (int(size) == int(master_size)):
                nb_byte = size / 8
                mask = pow(2, nb_byte)-1
                for i in range(int(byte_en_size / nb_byte)):
                    val = bin(int(mask * pow(2, nb_byte*i)))[2:]
                    out += ' "' + \
                        str(((bin(i*(int(size / 8)))[2:]).zfill(3))) + \
                        '" when ' + byte_en_name + ' = "' + \
                        val.zfill(byte_en_size) + '" else\n' + 2 * ONETAB

        out += "(others => '0');\n"

    return out


def gen_byte_enable(masterinterface):
    out = ""
    bus = masterinterface.bus
    try:
        master_bye = masterinterface.get_port_by_type(
            masterinterface.bus.sig_name("master", "byteen"))
    except PodError:
        return out
    master_bye_size = master_bye.real_size
    master_bye_name = master_bye.name

    out += "\n" + ONETAB + \
        "-- Byte enable muxing --\n" + \
        ONETAB + "------------------------"
    for slave_size in get_list_slave_size(masterinterface, "byteen"):
        nb_byte = slave_size / 8
        nb_iter = master_bye_size / nb_byte
        out += "\n" + ONETAB + "byte_enable" + \
            str(slave_size) + "_s <= "
        for i in range(nb_iter):
            out += master_bye_name + \
                "(" + str((nb_byte * i) + nb_byte - 1) + \
                " downto " + str(i * nb_byte) + ")"
            if i < nb_iter - 1:
                out += " or\n" + 2 * ONETAB
        out += ";\n"

    out += "\n"
    for slave in masterinterface.slaves:
        slave_it = slave.get_interface()
        try:
            slave_bye = slave_it.get_port_by_type(
                bus.sig_name("slave", "byteen"))
            out += ONETAB + \
                slave.instancename + "_" + slave_bye.name + \
                " <= byte_enable" + str(slave_it.data_size) + \
                "_s;\n"
        except PodError:
            continue
    return out


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
        out += ONETAB + slaveresetname + " <= " + masterresetname + ";\n"
        # clock
        out += ONETAB + slaveclockname + " <= " + masterclockname + ";\n"
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
    masteraddressname = "wbm_address_s"
    masterstrobename = masterinstancename + "_" +\
        masterinterface.get_port_by_type(
            bus.sig_name("master", "strobe")).name
    mastersizeaddr = masterinterface.addr_port_size

    out = ONETAB + "-----------------------\n"
    out += "\n" + ONETAB + "-- Address decoding  --\n"
    out += ONETAB + "-----------------------\n"
    for slave in masterinterface.slaves:
        slaveinstance = slave.get_instance()
        slaveinterface = slave.get_interface()
        slavesizeaddr = slave.get_interface().addr_port_size
        slavebase_address = slaveinterface.base_addr
        slavebase_size = int(math.log(int(slaveinterface.data_size) / 8, 2))

        if slavesizeaddr > 0:
            slaveaddressport = slave.get_interface().get_port_by_type(
                bus.sig_name("slave", "address"))
            slavename_addr = slaveinstance.instancename + "_" +\
                slaveaddressport.name
        if slavesizeaddr == 1:
            out += ONETAB + slavename_addr +\
                " <= " + masteraddressname + "(1);\n"
        elif slavesizeaddr > 1:
            out += ONETAB + slavename_addr + " <= " + masteraddressname +\
                "(" + str(slavesizeaddr+slavebase_size-1) + " downto " + \
                str(slavebase_size) + ");\n"
    out += "\n"
    out += ONETAB + "decodeproc : process(" + clk_name + ", " + rst_name +\
        ", " + masteraddressname + ")\n"
    out += ONETAB + "begin\n"

    # initialize
    out += ONETAB*2 + "if " + rst_name + "='1' then\n"
    for slave in masterinterface.slaves:
        slaveinstance = slave.get_instance()
        slaveinterface = slave.get_interface()
        chipselectname = slaveinstance.instancename + "_" +\
            slaveinterface.name + "_cs"
        out += ONETAB*3 + chipselectname + " <= '0';\n"
    out += ONETAB*2 + "elsif rising_edge(" + clk_name + ") then\n"

    for slave in masterinterface.slaves:
        slaveinstance = slave.get_instance()
        slaveinterface = slave.get_interface()
        chipselectname = slaveinstance.instancename + "_" +\
            slaveinterface.name + "_cs"
        slavesizeaddr = slave.get_interface().addr_port_size
        slavebase_address = slaveinterface.base_addr
        slavebase_size = int(math.log(int(slaveinterface.data_size) / 8, 2))
        if slavesizeaddr > 0:
            slaveaddressport = slave.get_interface().get_port_by_type(
                bus.sig_name("slave", "address"))
            slavename_addr = slaveinstance.instancename + "_" +\
                slaveaddressport.name

        out += "\n"
        out += ONETAB*3 + "if " + masteraddressname + "(" + \
            str(int(mastersizeaddr-1)) + " downto " + \
            str(slavesizeaddr + slavebase_size) + ')="' + \
            sy.inttobin(slavebase_address,
                        int(mastersizeaddr))[:-(slavesizeaddr + slavebase_size)] +\
            '"' + " and " + masterstrobename + "='1' then\n"

        out += ONETAB * 4 + chipselectname + " <= '1';\n"
        out += ONETAB * 3 + "else\n"
        out += ONETAB * 4 + chipselectname + " <= '0';\n"
        out += ONETAB * 3 + "end if;\n"

    out += "\n" + ONETAB * 2 + "end if;\n" +\
        ONETAB + "end process decodeproc;\n\n"
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
    out += ONETAB + "-- Control signals to slave\n"
    out += ONETAB + "-----------------------------\n"

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

        out += "\n" + ONETAB + "-- for " + slaveinstancename + "\n"
        # strobe
        out += ONETAB + slavestrobename + " <= (" +\
            masterstrobename + " and " + chipselectname + " );\n"
        # cycle
        out += ONETAB + slavecyclename + " <= (" +\
            mastercyclename + " and " + chipselectname + " );\n"

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
            out += ONETAB +\
                slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "write")).name +\
                " <= (" + masterinstancename + "_" + \
                masterinterface.get_port_by_type(
                    bus.sig_name("master", "write")).name + \
                " and " + chipselectname + " );\n"
        elif datainname:
            # write
            out += ONETAB +\
                slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "write")).name +\
                " <= '1';\n"
        elif dataoutname:
            # write
            out += ONETAB +\
                slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "write")).name +\
                " <= '0';\n"
        if datainname:
                out += ONETAB + slaveinstancename + "_" +\
                    slaveinterface.get_port_by_type(
                        bus.sig_name("slave", "datain")).name + \
                    " <= writedata" + slaveinterface.data_size + \
                    "_s when (" + masterinstancename + "_" +\
                    masterinterface.get_port_by_type(
                        bus.sig_name("master", "write")).name +\
                    " and " + chipselectname +\
                    " ) = '1' else (others => '0');" + "\n"
    return out


def controlmaster(masterinterface, intercon):
    bus = masterinterface.bus
    masterinstance = masterinterface.parent
    masterinstancename = masterinstance.instancename
    masterinterfacename = masterinterface.name

    out = "\n\n" + ONETAB + "-------------------------------\n"
    out += ONETAB + "-- Control signal for master --\n"
    out += ONETAB + "-------------------------------\n"

    out += ONETAB + masterinstance.instancename + "_"
    out += masterinterface.get_port_by_type(
        bus.sig_name("master", "datain")).name
    out += " <= "
    # READDATA
    for slave in masterinterface.slaves:
        slaveinstance = slave.get_instance()
        slaveinterface = slave.get_interface()
        slaveinterfacename = slaveinterface.name
        slaveinstancename = slave.instancename
        try:
            slaveinterface.get_port_by_type(
                bus.sig_name("slave", "dataout"))
            dataoutname = slaveinstancename + "_readdata_s"
            out += " " + dataoutname
            out += " when " + slaveinstancename + "_" +\
                slaveinterfacename + "_cs='1' else\n"
            out += ONETAB * 9 + "  "
        except PodError as error:
            pass
    out += " (others => '0');\n"

    # ACK
    out += ONETAB + masterinstance.instancename + "_"
    out += masterinterface.get_port_by_type(
        bus.sig_name("master", "ack")).name
    out += " <= "
    count = 0
    if masterinterface.slaves:
        for slave in masterinterface.slaves:
            slaveinstance = slave.get_instance()
            slaveinterface = slave.get_interface()
            slaveinterfacename = slaveinterface.name
            slaveinstancename = slave.instancename
            if count == 0:
                out += " "
                count = 1
            else:
                out += "\n" + ONETAB * 9 + "or \n"
                out += ONETAB * 8
            out += "(" + slaveinstancename + "_" +\
                slaveinterface.get_port_by_type(
                    bus.sig_name("slave", "ack")).name +\
                " and " + slaveinstancename + "_" + slaveinterfacename + "_cs)"
    else:
        out += "'0'"
    out += ";\n"
    return out


def selectWrite(masterinterface, intercon):
    master_size = int(masterinterface.data_size)
    bus = masterinterface.bus
    byte_en = masterinterface.get_port_by_type("BYE")
    byte_en_name = masterinterface.parent.instancename + "_" + byte_en.name
    byte_en_size = byte_en.real_size
    out = ""

    for slave in masterinterface.slaves:
        interface = slave.get_interface()
        try:
            slave_bus_name = slave.get_instance().instancename + "_" + \
                interface.get_port_by_type(
                    bus.sig_name("slave", "dataout")).name
        except PodError:
            continue

        data_size = int(interface.data_size)
        out += ONETAB + slave.instancename + "_readdata_s <= "
        if int(data_size) == int(master_size):
            out += slave_bus_name
        else:
            nb_byte = data_size / 8
            mask = pow(2, nb_byte)-1
            bitsize = int(master_size / data_size)
            for i in range(bitsize):
                min_pos = i * data_size
                val = bin(int(mask * pow(2, nb_byte*i)))[2:]
                if i < bitsize - 1:
                    out += "(" + str(master_size-1) + \
                        " downto " + str(min_pos + data_size) + " => '0') & "
                out += slave_bus_name + " "
                if i != 0:
                    out += "& (" + str(min_pos-1) + " downto 0 => '0')"
                if i < bitsize - 1:
                    out += " when " + byte_en_name + ' = "' + \
                        val.zfill(byte_en_size) + '" else\n' + 2 * ONETAB
        out += ";\n\n"

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
    VHDLcode = VHDLcode + genCaseByteEnable(masterinterface)
    VHDLcode = VHDLcode + gen_byte_enable(masterinterface)
    listslave = masterinterface.slaves
    listinterfacesyscon = []
    for slaveinstance in [slave.get_instance() for slave in listslave]:
        listinterfacesyscon.append(slaveinstance.get_one_syscon())
    listinterfacesyscon.append(masterinstance.get_one_syscon())

    # Clock and Reset connection
    VHDLcode = VHDLcode + connectClockandReset(masterinterface,
                                               intercon)

    # address decoding
    VHDLcode = VHDLcode + addressdecoding(masterinterface,
                                          masterinstance, intercon)

    # controls slaves
    VHDLcode = VHDLcode + controlslave(masterinterface, intercon)
    # controls master
    VHDLcode = VHDLcode + controlmaster(masterinterface, intercon)
    # readdata mux
    VHDLcode = VHDLcode + selectWrite(masterinterface, intercon)
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
