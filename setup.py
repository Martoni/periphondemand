#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     setup.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  16/02/2009
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
# Revision list :
#
# Date       By        Changes
#
# ----------------------------------------------------------------------------

from setuptools import setup
import os
import re
import sys
sys.path.append("periphondemand/bin/")
from version import VERSION

setup(name='PeriphOnDemand',
      version=VERSION,
      url='https://sourceforge.net/projects/periphondemand',
      author='Fabien Marteau and Nicolas Colombain',
      author_email='<fabien.marteau@armadeus.com>,"' +
                   '<nicolas.colombain@armadeus.com>',
      maintainer='Fabien Marteau',
      maintainer_email='fabien.marteau@armadeus.com',
      package_dir={"periphondemand": "periphondemand"},
      packages=['periphondemand',
                'periphondemand.bin',
                'periphondemand.bin.code',
                'periphondemand.bin.code.vhdl',
                'periphondemand.bin.commandline',
                'periphondemand.bin.core',
                'periphondemand.bin.toolchain',
                'periphondemand.bin.utils',
                'periphondemand.toolchains',
                'periphondemand.templates',
                ],
      scripts=['periphondemand/bin/pod'],
      license='GPL',
)
