#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     TopGen.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  15/05/2008
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
""" Generate top component """

from periphondemand.bin.define import SYNTHESISPATH
from periphondemand.bin.define import VHDLEXT

from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.settings import Settings

SETTINGS = Settings()


class TopGen(object):
    """ Generate Top component from a project
    """

    def __init__(self, project):
        self.project = project

    def header(self):
        """ return header
        """
        raise NotImplementedError("method must be implemented", 0)

    def entity(self, entityname, portlist):
        """ return code for Top entity
        """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def architecture_head(cls, entityname):
        """ return head of architecture
        """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def architecture_foot(cls, entityname):
        """ return architecture footer
        """
        raise NotImplementedError("method must be implemented", 0)

    def declare_components(self):
        """ return components declaration
        """
        raise NotImplementedError("method must be implemented", 0)

    def declare_signals(self, componentslist, incomplete_external_ports_list):
        """ return signals declaration
        """
        raise NotImplementedError("method must be implemented", 0)

    def declare_instance(self):
        """ return instance declaration
        """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def connect_forces(cls, portlist):
        """ return connections forced
        """
        raise NotImplementedError("method must be implemented", 0)

    def connect_instance(self, incomplete_external_ports_list):
        """ return instances connections
        """
        raise NotImplementedError("method must be implemented", 0)

    @classmethod
    def architecture_begin(cls):
        """ return architecture begin
        """
        raise NotImplementedError("method must be implemented", 0)

    def generate(self):
        """ generate code for top component
        """
        # checking if all intercons are done
        for masterinterface in self.project.interfaces_master:
            try:
                self.project.get_instance(
                    masterinterface.parent.instancename +
                    "_" +
                    masterinterface.name +
                    "_intercon")
            except PodError as error:
                raise PodError("Intercon missing, all intercon must be" +
                               "generated before generate top.\n" + str(error))

        # header
        out = self.header()
        # entity
        entityname = "top_" + self.project.name
        portlist = self.project.platform.connect_ports
        out = out + self.entity(entityname, portlist)
        # architecture head
        out = out + self.architecture_head(entityname)
        # declare components
        out = out + self.declare_components()
        # declare signals
        platform = self.project.platform
        incompleteportslist = platform.incomplete_ext_ports
        out = out + self.declare_signals(self.project.instances,
                                         incompleteportslist)
        # begin
        out = out + self.architecture_begin()
        # Connect forces
        out = out + self.connect_forces(portlist)
        # declare Instance
        out = out + self.declare_instance()
        # instance connection
        out = out + self.connect_instance(incompleteportslist)
        # architecture foot
        out = out + self.architecture_foot(entityname)

        # save file
        try:
            top_file = open(self.project.projectpath + SYNTHESISPATH +
                            "/top_" + self.project.name + VHDLEXT, "w")
        except IOError as error:
            raise error
        top_file.write(out)
        top_file.close()
        return out
