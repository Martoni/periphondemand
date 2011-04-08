#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     vhdlentityparser.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com> and
#           Fabrice Mousset <fabrice.mousset@laposte.net>
# Created:  06/05/2009
#-----------------------------------------------------------------------------
#
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
__versionTime__ = "06/05/2009"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com> and "+\
             "Fabrice Mousset <fabrice.mousset@laposte.net>"

import os,re
from pyparsing import *

from periphondemand.bin.define import *

from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings   import Settings
from periphondemand.bin.utils.error      import Error

settings = Settings()

from pyparsing import *

# VHDL Entity cleaners. Used in parsing, but doesn't clutter up results
SEMI = Literal(";").suppress()
LPAR = Literal("(").suppress()
RPAR = Literal(")").suppress()
COLON = Literal(":").suppress()
EQUAL = Literal(":=").suppress()

# VHDL Entity data extractors.
identifier = Word(alphas, alphanums + "_").setParseAction(downcaseTokens)
integer = Word(nums).setParseAction(lambda t:int(t[0]))
hexaValue = Combine('X"' + Word(hexnums) + '""')
vectorValue = Combine('"' + Word("01X") + '"')
bitValue = Combine("'" + Word("01X", max=1) + "'")
arithOp = Word("+-*/", max=1)
entityIdent = identifier.setResultsName("identifier")
mode = oneOf("IN OUT INOUT BUFFER LINKAGE", caseless=True)

# VHDL comments extractor.
comment = Literal("--").suppress() + Optional(restOfLine)

# Nested operation parser
expression = Forward()
parenthical = Literal("(") + Group(expression) + Literal(")")
operand = Word(nums) | identifier  | parenthical
expression << operand + ZeroOrMore(arithOp + operand)

staticExpression = (integer | identifier | hexaValue | vectorValue | bitValue)

# Type information parser
subtypeIndication = Group(identifier +
                          Optional(LPAR + Combine(expression) +
                                   oneOf("TO DOWNTO", caseless=True) +
                                   Combine(expression) + RPAR
                                   )
                          )

# Port declaration parser
portDecl = Group(identifier + COLON + mode + subtypeIndication)
portList = delimitedList(portDecl, delim=";").setResultsName("ports")

# Generic declaration parser
genericDecl = Group(identifier + COLON + subtypeIndication +
                    Optional(EQUAL + staticExpression)
                    )
genericList = delimitedList(genericDecl, delim=";").setResultsName("generics")

# VHDL Entity declaration decoder
entityHeader = (CaselessLiteral("ENTITY").suppress() + entityIdent +
    CaselessLiteral("IS").suppress()
    )

# Full VHDL Entity decoder
entityDecl = (SkipTo(entityHeader) + entityHeader +
              Optional(CaselessLiteral("GENERIC").suppress() + LPAR +
                       genericList + RPAR + SEMI
                       ) +
              Optional(CaselessLiteral("PORT").suppress() + LPAR +
                       portList + RPAR + SEMI
                       ) +
              CaselessLiteral("END").suppress() +
              Optional(CaselessLiteral("ENTITY").suppress()) +
              Optional(matchPreviousLiteral(entityIdent).suppress()) + SEMI
              ).ignore(comment) + SkipTo(StringEnd()).suppress()

class VHDLEntityParser:
    """
    """

    def __init__(self,filepath):
        hdl_file = open(filepath,'r')
        self.filestring = hdl_file.read()
        hdl_file.close()
        self.parsed_entity = entityDecl.parseString(self.filestring)

    def parseGeneric(self):
        parsed_generic_list = []
        for generic in self.parsed_entity.generics:
            parsed_generic = {}
            parsed_generic["name"] = generic[0].lower()
            parsed_generic["type"] = generic[1][0].lower()
            parsed_generic["defautvalue"] = str(generic[2]).lower()
            parsed_generic["description"] = "" # TODO: manage description from VHDL comment
            parsed_generic_list.append(parsed_generic)
        return parsed_generic_list

    def getGenericValue(self,generic_name):
        generic_list = self.parseGeneric()
        for generic in generic_list:
            if generic["name"] == generic_name:
                return generic["defautvalue"]
        raise Error("No "+generic_name+" in HDL file")

    def __evaluate(self,expression):
        """ evaluate expression """
        # find operation like "wb_size-1"
        m = re.match("([a-zA-Z0-9_]+)([\-\+])(\d+)",expression)
        #n = re.match("([a-zA-Z0-9_]+)([\-\+])(\d+)",expression)
        if m:
            first = int(self.getGenericValue(m.group(1)))
            second = int(m.group(3))
            if m.group(2): # if - soustract, else add
                return first-second
            else:
                return first+second
        else: # if not matched it's a digit
            return int(expression)

    def parsePort(self):
        parsed_port_list = []
        for port in self.parsed_entity.ports:
            parsed_port = {}
            parsed_port["name"] = port[0].lower()
            parsed_port["direction"] = port[1].lower()
            parsed_port["description"] = "" # TODO: match comment -- in VHDL for descripton
            if len(port[2]) == 1: # no vector
                parsed_port["type"] = port[2][0].lower()
                parsed_port["size"] = "1"
            elif len(port[2]) == 4: # type( max to min)
                first = port[2][1].lower()
                second = port[2][3].lower()
                direction = port[2][2].lower()
                parsed_port["type"] = port[2][0].lower()
                if direction == "to":
                    parsed_port["size"] = str(self.__evaluate(second)-self.__evaluate(first)+1)
                elif direction == "downto":
                    parsed_port["size"] = str(self.__evaluate(first)-self.__evaluate(second)+1)
                else:
                    raise Error("Direction unknown "+str(direction))
            else:
                raise Error("Parsing port")
            parsed_port_list.append(parsed_port)
        return parsed_port_list

    def getEntityName(self):
        return self.parsed_entity.identifier

if __name__ == "__main__":
    print "vhdlentityparser class test\n"
    parser = VHDLEntityParser("/home/fabien/periphondemand/periphondemand/tests/industrial_serial_input.vhd")
    print "entity name : "+parser.getEntityName()
    print "parsed generic:\n"+str(parser.parseGeneric())
    print "parsed port :\n"+str(parser.parsePort())
