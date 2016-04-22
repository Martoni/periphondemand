#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Generic.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  21/05/2008
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
""" Manage generic values """

import re
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.poderror import PodError

DESTINATION = ["fpga", "driver", "both"]
PUBLIC = ["true", "false"]


class Generic(WrapperXml):
    """ Manage generic instance value
    """

    def __init__(self, parent, **keys):
        """ init Generic,
            __init__(self,parent,node)
            __init__(self,parent,nodestring)
            __init__(self,parent,name)
        """
        self.parent = parent
        if "node" in keys:
            WrapperXml.__init__(self, node=keys["node"])
        elif "nodestring" in keys:
            WrapperXml.__init__(self, nodestring=keys["nodestring"])
        elif "name" in keys:
            WrapperXml.__init__(self, nodename="generic")
            self.name = keys["name"]
        else:
            raise PodError("Keys unknown in Generic init()", 0)

    @property
    def operator(self):
        """ return the operator """
        return self.get_attr_value("op")

    @operator.setter
    def operator(self, operator):
        """ set operator """
        self.set_attr("op", operator)

    @property
    def target(self):
        """ getting target attribute """
        return self.get_attr_value("target")

    @target.setter
    def target(self, target):
        """ setting target attribute """
        self.set_attr("target", target)

    def is_public(self):
        """ is this generic public ? """
        if self.get_attr_value("public") == "true":
            return True
        else:
            return False

    def set_public(self, public):
        """ Setting public or not """
        public = public.lower()
        if public not in PUBLIC:
            raise PodError("Public value " + str(public) + " wrong")
        self.set_attr("public", public)

    @property
    def generictype(self):
        """ get the generic type """
        the_type = self.get_attr_value("type")
        if the_type is None:
            raise PodError("Generic " + self.name +
                           " description malformed, type must be defined", 0)
        else:
            return the_type

    @generictype.setter
    def generictype(self, atype):
        """ set the generic type """
        self.set_attr("type", atype)

    @property
    def match(self):
        """ get the matching regexp """
        try:
            return self.get_attr_value("match").encode("utf-8")
        except AttributeError:
            return None

    @match.setter
    def match(self, match):
        """ set the matching regexp """
        self.set_attr("match", match)

    @property
    def value(self):
        """ return the generic value """
        component = self.parent
        if self.operator is None:
            return self.get_attr_value("value")
        else:
            target = self.target.split(".")
            if self.operator == "realsizeof":
                # return the number of connected pin
                return str(int(
                    component.get_interface(
                        target[0]).get_port(target[1]).max_pin_num) + 1)
            else:
                raise PodError("Operator unknown " + self.operator, 1)

    @value.setter
    def value(self, value):
        """ setting the value """
        if self.match is None:
            self.set_attr("value", value)
        elif re.compile(self.match.decode()).match(value):
            self.set_attr("value", value)
        else:
            raise PodError("Value doesn't match for attribute " + str(value))

    @property
    def destination(self):
        """ return the generic destination (fpga,driver or both) """
        return self.get_attr_value("destination")

    @destination.setter
    def destination(self, destination):
        """ setting destination """
        destination = destination.lower()
        if destination not in DESTINATION:
            raise PodError("Destination value " + str(destination) +
                           " unknown")
        self.set_attr("destination", destination)
