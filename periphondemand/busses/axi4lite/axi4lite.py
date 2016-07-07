#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     axi4lite.py
# Purpose:
# Author:   Gwenhael Goavec-Merou <gwenhael.goavec-merou@trabucayre.com>
# Created:  06/07/2016
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
""" Manage axi4lite data bus"""

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

from periphondemand.bin.core.hdl_file import HdlFile

SETTINGS = Settings()


def gen_slv_sig(slvname, slvif, bus, porttype):
    """ return slave signal name """
    return slvname + "_" + slvif.get_port_by_type(
        bus.sig_name("slave", porttype)).name


def gen_mst_sig(mstname, mstif, porttype):
    """ return master signal name """
    return mstname + "_" + mstif.get_port_by_type(
        mstif.bus.sig_name("master", porttype)).name


def header(author, intercon):
    """ return vhdl header
    """
    head = open(SETTINGS.path + TEMPLATESPATH + "/" + HEADERTPL, "r").read()
    head = head.replace("$tpl:author$", author)
    head = head.replace("$tpl:date$", str(datetime.date.today()))
    head = head.replace("$tpl:filename$", intercon.name + VHDLEXT)
    head = head.replace("$tpl:abstract$", intercon.description)
    return head


def entity(intercon):
    """ generate entity
    """
    ent = "Entity " + intercon.name + " is\n"
    ent += ONETAB + "port\n" + ONETAB + "(\n"
    for interface in intercon.interfaces:
        ent += "\n" + ONETAB * 2 + "-- " +\
            interface.name + " connection\n"
        for port in interface.ports:
            ent += ONETAB * 2 + "%-40s" % port.name + " : " +\
                "%-5s" % port.direction
            if port.max_pin_num == port.min_pin_num:
                ent += "std_logic;\n"
            else:
                ent += "std_logic_vector(" + port.max_pin_num +\
                    " downto " + port.min_pin_num + ");\n"
    # Suppress the #!@ last semicolon
    ent = ent[:-2]
    ent += "\n"

    ent += ONETAB + ");\n" + "end entity;\n\n"
    return ent


def get_list_slave_size(masterinterface, port_name=None):
    """ return list of slave interface size """
    bus = masterinterface.bus
    data_size = []
    for slave in masterinterface.slaves:
        for i in slave.get_instance().interfaces:
            if i.bus_name == "axi4lite":
                if port_name is not None:
                    try:
                        i.get_port_by_type(
                            bus.sig_name("slave", port_name))
                    except PodError:
                        continue
                data_size.append(int(i.data_size))
    return list(set(data_size))


def architecture_head(masterinterface, intercon):
    """ Generate the head architecture
    """
    data_size = get_list_slave_size(masterinterface, "wdata")
    bus = masterinterface.bus

    archead = "architecture " + intercon.name + "_1 of " +\
        intercon.name + " is\n"

    genaddr = lambda porttype, portname: ONETAB + "signal " + \
        "%-20s" % (portname) + " : std_logic_vector(" + \
        str(int(masterinterface.get_port_by_type(porttype).max_pin_num)) + \
        " downto 0);\n"
    # create signal arxxx
    archead += genaddr("ARADR", "araddr_s")
    archead += genaddr("AWADR", "awaddr_s")

    # create new data signal WDATA
    for size in data_size:
        # all writedata used with mux to adapt size
        archead += ONETAB + "signal " +\
            "%-20s" % ("writedata" + str(size) + "_s") + \
            " : std_logic_vector(" + str(size-1) + " downto 0);\n"

    data_size = int(masterinterface.data_size)-1
    fn_decl_sig = lambda cspref, slave: ONETAB + "signal " +\
        "%-20s" % (cspref + slave.instancename + "_" +
                   slave.interfacename + "_cs") +\
        " : std_logic := '0' ;\n"

    for slave in masterinterface.slaves:
        archead += fn_decl_sig("aw_", slave)
        archead += fn_decl_sig("ar_", slave)
        archead += fn_decl_sig("w_", slave)
        archead += fn_decl_sig("r_", slave)
        # slave readdata reconstruct to match master readdata
        try:
            slave.get_interface().get_port_by_type(
                bus.sig_name("slave", "dataout"))
            archead += ONETAB + "signal " +\
                "%-20s" % (slave.instancename + "_readdata_s") + \
                " : std_logic_vector(" + str(data_size) + " downto 0);\n"
        except PodError:
            pass

    archead += "begin\n"
    return archead


def gen_case_byte_enable(masterinterface):
    """ generate byte enable case part """
    out = ""

    byte_en = masterinterface.get_port_by_type("WSTRB")
    byte_en_name = masterinterface.parent.instancename + "_" + byte_en.name
    byte_en_size = int(byte_en.real_size)

    write_bus = masterinterface.get_port_by_type(
        masterinterface.bus.sig_name("master", "wdata"))
    write_bus_name = masterinterface.parent.instancename + "_" + \
        write_bus.name
    master_size = int(write_bus.real_size)

    aw_addr_inst = masterinterface.get_port_by_type(
        masterinterface.bus.sig_name("master", "awaddress"))
    ar_addr_inst = masterinterface.get_port_by_type(
        masterinterface.bus.sig_name("master", "araddress"))
    aw_addr_bus = masterinterface.parent.instancename + "_" + aw_addr_inst.name
    ar_addr_bus = masterinterface.parent.instancename + "_" + ar_addr_inst.name
    aw_addr_size = aw_addr_inst.max_pin_num
    ar_addr_size = ar_addr_inst.max_pin_num
    shift = int(math.log(master_size / 8, 2))

    masteraddressname = "addr_s"

    # writedata mux generation
    for size in get_list_slave_size(masterinterface, "wdata"):
        nb_byte = size / 8
        mask = pow(2, nb_byte)-1

        out += ONETAB + "writedata" + str(size) + "_s <= "

        if int(size) == int(master_size):
            out += write_bus_name
        else:
            bitsize = byte_en_size / nb_byte
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

    if len(data_size) == 0:
        return out

    if len(data_size) == 1 and data_size[0] == master_size:
        out += ONETAB + "ar" + masteraddressname + " <= " + \
            ar_addr_bus + ";\n"
        out += ONETAB + "aw" + masteraddressname + " <= " + \
            aw_addr_bus + ";\n"
    else:
        slave_addr = masteraddressname + "(" + str(shift-1) + " downto 0) <= "
        out += ONETAB + "ar" + masteraddressname + "(" + str(ar_addr_size) + \
            " downto " + str(shift) + ") <= " + ar_addr_bus + \
            "(" + str(ar_addr_size) + " downto " + str(shift) + ");\n"
        out += ONETAB + slave_addr
        for size in data_size:
            if not (int(size) == int(master_size)):
                nb_byte = size / 8
                mask = pow(2, nb_byte)-1
                for i in range(byte_en_size / nb_byte):
                    val = bin(int(mask * pow(2, nb_byte*i)))[2:]
                    out += ' "' + \
                        str(((bin(i*(size/8))[2:]).zfill(3))) + \
                        '" when ' + byte_en_name + ' = "' + \
                        val.zfill(byte_en_size) + '" else\n' + 2 * ONETAB

        out += "(others => '0');\n"
    return out


def connect_clock_and_reset(masterinterface):
    """ Connect clock and reset
    """

    bus = masterinterface.bus
    masterinstancename = masterinterface.parent.instancename
    masterresetname = gen_mst_sig(masterinstancename,
                                  masterinterface, "reset")
    masterclockname = gen_mst_sig(masterinstancename,
                                  masterinterface, "clock")
    out = "\n" + ONETAB + "-- Clock and Reset connection\n"

    for slave in masterinterface.slaves:
        slaveif = slave.get_interface()
        slvname = slave.instancename
        slaveresetname = gen_slv_sig(slvname, slaveif, bus, "reset")
        slaveclockname = gen_slv_sig(slvname, slaveif, bus, "clock")
        # reset
        out += ONETAB + slaveresetname + " <= " + masterresetname + ";\n"
        # clock
        out += ONETAB + slaveclockname + " <= " + masterclockname + ";\n"
    return out


def addressdecoding(masterif, masterinstance):
    """ generate VHDL for address decoding
    """
    bus = masterif.bus
    mastername = masterinstance.instancename
    rst_name = gen_mst_sig(mastername, masterif, "reset")
    clk_name = gen_mst_sig(mastername, masterif, "clock")
    masteraddressname_r = "araddr_s"
    masteraddressname_w = "awaddr_s"

    masterstrobename_aw = gen_mst_sig(mastername, masterif,
                                      "awvalid")
    masterstrobename_w = gen_mst_sig(mastername, masterif,
                                     "wvalid")
    masterstrobename_ar = gen_mst_sig(mastername, masterif,
                                      "arvalid")
    masterstrobename_r = gen_mst_sig(mastername, masterif,
                                     "rready")

    mstsizeaddr = masterif.addr_size

    out = ONETAB + "-----------------------\n"
    out += "\n" + ONETAB + "-- Address decoding  --\n"
    out += ONETAB + "-----------------------\n"

    for slave in masterif.slaves:
        slaveinstance = slave.get_instance()
        slaveif = slave.get_interface()
        slavesizeaddr = slaveif.addr_size
        slavebase_address = slaveif.base_addr
        slavebase_size = int(math.log(int(slaveif.data_size) / 8, 2))

        if slavesizeaddr > 0:
            slavename_araddr = gen_slv_sig(slaveinstance.instancename,
                                           slaveif, bus, "araddress")
            slavename_awaddr = gen_slv_sig(slaveinstance.instancename,
                                           slaveif, bus, "awaddress")

            if slavesizeaddr == 1:
                out += ONETAB + slavename_araddr +\
                    " <= " + masteraddressname_r + "(1);\n"
                out += ONETAB + slavename_awaddr +\
                    " <= " + masteraddressname_w + "(1);\n"
            elif slavesizeaddr > 1:
                out += ONETAB + slavename_araddr + " <= " + \
                    masteraddressname_r + \
                    "(" + str(slavesizeaddr+slavebase_size-1) + " downto " + \
                    str(slavebase_size) + ");\n"
                out += ONETAB + slavename_awaddr + " <= " + \
                    masteraddressname_w +\
                    "(" + str(slavesizeaddr+slavebase_size-1) + " downto " + \
                    str(slavebase_size) + ");\n"
    out += "\n"

    out += ONETAB + "decodeproc : process(" + clk_name + ", " + \
        rst_name + ")\n"
    out += ONETAB + "begin\n"

    # initialize
    out += ONETAB*2 + "if " + rst_name + "='1' then\n"
    for slave in masterif.slaves:
        slaveinstance = slave.get_instance()
        slaveif = slave.get_interface()
        csname = slaveinstance.instancename + "_" + \
            slaveif.name + "_cs"
        out += ONETAB*3 + "aw_" + csname + " <= '0';\n"
        out += ONETAB*3 + "w_" + csname + " <= '0';\n"
        out += ONETAB*3 + "ar_" + csname + " <= '0';\n"
        out += ONETAB*3 + "r_" + csname + " <= '0';\n"
    out += ONETAB*2 + "elsif rising_edge(" + clk_name + ") then\n"

    gen_cond = lambda cond, mststrb, csname: cond + mststrb + \
        "='1' then\n" + \
        ONETAB * 4 + csname + " <= '1';\n" + \
        ONETAB * 3 + "else\n" + \
        ONETAB * 4 + csname + " <= '0';\n" + \
        ONETAB * 3 + "end if;\n"

    for slave in masterif.slaves:
        slaveinstance = slave.get_instance()
        slaveif = slave.get_interface()
        csname = slaveinstance.instancename + "_" +\
            slaveif.name + "_cs"
        slavesizeaddr = slave.get_interface().addr_size
        slavebase_address = slaveif.base_addr
        slavebase_size = int(math.log(int(slaveif.data_size) / 8, 2))

        out += "\n"
        condw = ONETAB*3 + "if " + masteraddressname_w + "(" + \
            str(int(mstsizeaddr-1)) + " downto " + \
            str(slavesizeaddr + slavebase_size) + ')="' + \
            sy.inttobin(slavebase_address,
                        int(mstsizeaddr))[:-(slavesizeaddr + slavebase_size)] +\
            '"' + " and "
        condr = ONETAB*3 + "if " + masteraddressname_r + "(" + \
            str(int(mstsizeaddr-1)) + " downto " + \
            str(slavesizeaddr + slavebase_size) + ')="' + \
            sy.inttobin(slavebase_address,
                        int(mstsizeaddr))[:-(slavesizeaddr + slavebase_size)] +\
            '"' + " and "
        out += gen_cond(condw, masterstrobename_aw, "aw_" + csname)
        out += gen_cond(condw, masterstrobename_w, "w_" + csname)
        out += gen_cond(condr, masterstrobename_ar, "ar_" + csname)
        out += gen_cond(condr, masterstrobename_r, "r_" + csname)
    out += "\n" + ONETAB * 2 + "end if;\n" +\
        ONETAB + "end process decodeproc;\n\n"

    return out


def controlslave(masterif):
    """ Connect controls signals for slaves
    """

    bus = masterif.bus
    masterinstance = masterif.parent
    mastername = masterinstance.instancename

    out = ONETAB + "-----------------------------\n"
    out += ONETAB + "-- Control signals to slave\n"
    out += ONETAB + "-----------------------------\n"

    mstawvalid = gen_mst_sig(mastername, masterif, "awvalid")
    mstawprot = gen_mst_sig(mastername, masterif, "awprot")
    mstwrvalid = gen_mst_sig(mastername, masterif, "wvalid")
    mstwrstrobe = gen_mst_sig(mastername, masterif, "wstrb")
    mstarvalid = gen_mst_sig(mastername, masterif, "arvalid")
    mstarprot = gen_mst_sig(mastername, masterif, "arprot")
    # mstrvalid = gen_mst_sig(mastername, masterif, "rvalid")
    mstrready = gen_mst_sig(mastername, masterif, "rready")
    mstbready = gen_mst_sig(mastername, masterif, "bready")

    controlslvsig = lambda slvname, mstsig, csname: ONETAB + \
        slvname + " <= (" + mstsig + " and " + csname + " );\n"

    for slave in masterif.slaves:
        slaveif = slave.get_interface()
        slaveinstancename = slave.instancename

        # TODO : adprot awready wready wstrobe
        csname = slaveinstancename + "_" + slaveif.name + "_cs"

        out += "\n" + ONETAB + "-- for " + slaveinstancename + "\n"

        try:
            datainname = gen_slv_sig(slaveinstancename, slaveif, bus,
                                     "wdata")
        except PodError:
            datainname = None
        try:
            dataoutname = gen_slv_sig(slaveinstancename, slaveif, bus,
                                      "rdata")
        except PodError:
            dataoutname = None

        if datainname:
            slvawvalidname = gen_slv_sig(slaveinstancename,
                                         slaveif, bus, "awvalid")
            slvwvalidname = gen_slv_sig(slaveinstancename,
                                        slaveif, bus, "wvalid")
            slvbreadyname = gen_slv_sig(slaveinstancename,
                                        slaveif, bus, "bready")
            # write
            out += ONETAB + \
                gen_slv_sig(slaveinstancename, slaveif, bus,
                            "awprot") + " <= " + mstawprot + \
                " when (" + mstawvalid + " and aw_" + \
                csname + " ) = '1' else (others => '0');\n"
            out += controlslvsig(slvawvalidname, mstawvalid,
                                 "aw_" + csname)
            out += controlslvsig(slvwvalidname, mstwrvalid,
                                 "w_" + csname)
            out += controlslvsig(slvbreadyname, mstbready,
                                 "w_" + csname)

            out += ONETAB + datainname + " <= writedata" + \
                slaveif.data_size + "_s when (" + mstwrvalid + \
                " and w_" + csname + \
                " ) = '1' else (others => '0');" + "\n"
            out += ONETAB + \
                gen_slv_sig(slaveinstancename, slaveif, bus,
                            "wstrb") + " <= " + mstwrstrobe + \
                " when (" + mstwrvalid + " and w_" + \
                csname + " ) = '1' else (others => '0');\n"

        if dataoutname:
            slvarvalidname = gen_slv_sig(slaveinstancename,
                                         slaveif, bus, "arvalid")
            slvrreadyname = gen_slv_sig(slaveinstancename,
                                        slaveif, bus, "rready")
            out += ONETAB + \
                gen_slv_sig(slaveinstancename, slaveif, bus,
                            "arprot") + " <= " + mstarprot + \
                " when (" + mstarvalid + " and ar_" + \
                csname + " ) = '1' else (others => '0');\n"
            out += controlslvsig(slvarvalidname, mstarvalid,
                                 "ar_" + csname)
            out += controlslvsig(slvrreadyname, mstrready,
                                 "r_" + csname)

    return out


def controlmaster(masterif):
    """ generate signal for master """

    mstname = masterif.parent.instancename

    out = "\n\n" + ONETAB + "-------------------------------\n"
    out += ONETAB + "-- Control signal for master --\n"
    out += ONETAB + "-------------------------------\n"
    sigdict = {"rdata": "r_", "rresp": "r_", "bresp": "w_",
               "bvalid": "w_", "awready": "aw_", "wready": "w_",
               "arready": "ar_", "rvalid": "r_"}
    typeif = {"rdata": "slv", "rresp": "slv", "bresp": "slv",
              "bvalid": "sl",
              "awready": "sl", "wready": "sl",
              "arready": "sl", "rvalid": "sl"}
    plop = {}
    count = {}
    for key in sigdict:
        plop[key] = ONETAB + gen_mst_sig(mstname, masterif, key) + \
            " <= "
        if len(masterif.slaves) == 0:
            if typeif[key] == "sl":
                plop[key] += "'0'"
        count[key] = 0

    for slave in masterif.slaves:
        slaveif = slave.get_interface()
        slavename = slave.instancename
        for key in sigdict:
            try:
                dataoutname = gen_slv_sig(slavename, slaveif,
                                          masterif.bus, key)
                csname = sigdict[key] + slavename + "_" + slaveif.name + "_cs"
                if (typeif[key] == "slv"):
                    plop[key] = plop[key] + " " + dataoutname + \
                        " when " + csname + \
                        "='1' else\n" + ONETAB * 9 + "  "
                else:
                    if count[key] == 0:
                        count[key] = 1
                    else:
                        plop[key] = plop[key] + " or \n" + ONETAB * 8
                    plop[key] = plop[key] + "(" + dataoutname + \
                        " and " + csname + ")"
            except PodError:
                pass
    for key in sigdict:
        out += plop[key]
        if typeif[key] == "slv":
            out += " (others => '0')"
        out += ";\n"
    return out


def architecture_foot(intercon):
    """ Write foot architecture code
    """
    out = "\nend architecture " + intercon.name + "_1;\n"
    return out


def generate_intercon(masterinterface, intercon):
    """Generate intercon VHDL code for axi4lite bus
    """
    masterinstance = masterinterface.parent

    # comment and header
    vhdl_code = header(SETTINGS.author, intercon)
    # entity
    vhdl_code += entity(intercon)
    vhdl_code += architecture_head(masterinterface, intercon)
    vhdl_code += gen_case_byte_enable(masterinterface)

    listslave = masterinterface.slaves
    listinterfacesyscon = []
    for slaveinstance in [slave.get_instance() for slave in listslave]:
        listinterfacesyscon.append(slaveinstance.get_one_syscon())
    listinterfacesyscon.append(masterinstance.get_one_syscon())
    # Clock and Reset connection
    vhdl_code += connect_clock_and_reset(masterinterface)
    # address decoding
    vhdl_code += addressdecoding(masterinterface, masterinstance)
    # controls slaves
    vhdl_code += controlslave(masterinterface)
    # controls master
    vhdl_code += controlmaster(masterinterface)
    # Foot
    vhdl_code += architecture_foot(intercon)
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
    afile.write(vhdl_code)
    afile.close()
    # hdl file path
    hdl = HdlFile(intercon,
                  filename=intercon.instancename + VHDLEXT,
                  istop=1, scope="both")
    intercon.add_hdl_file(hdl)
    return vhdl_code
