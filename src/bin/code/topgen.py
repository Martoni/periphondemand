#! /usr/bin/python
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
            except PodError, error:
                raise PodError("Intercon missing, all intercon must be" +
                               "generated before generate top.\n" + str(error))

        # header
        out = self.header()
        # entity
        entityname = "top_" + self.project.name
        portlist = self.project.platform.connect_ports
        out = out + self.entity(entityname, portlist)
        # architecture head
        out = out + self.architectureHead(entityname)
        # declare components
        out = out + self.declareComponents()
        # declare signals
        platform = self.project.platform
        incompleteportslist = platform.incomplete_ext_ports
        out = out + self.declareSignals(self.project.instances,
                                        incompleteportslist)
        # begin
        out = out + self.architectureBegin()
        # Connect forces
        out = out + self.connectForces(portlist)
        # declare Instance
        out = out + self.declareInstance()
        # instance connection
        out = out + self.connectInstance(incompleteportslist)
        # architecture foot
        out = out + self.architectureFoot(entityname)

        # save file
        try:
            file = open(self.project.projectpath + SYNTHESISPATH +
                        "/top_" + self.project.name + VHDLEXT, "w")
        except IOError, error:
            raise error
        file.write(out)
        file.close()
        return out
