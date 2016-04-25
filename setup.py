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
from setuptools import find_packages
import os
import re
import sys
sys.path.append("periphondemand/bin/")
from version import VERSION

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append('../' + os.path.join(path, filename))
    return paths

setup(name='PeriphOnDemand',
      version=VERSION,
      url='https://sourceforge.net/projects/periphondemand',
      author='Fabien Marteau and Nicolas Colombain',
      author_email='<fabien.marteau@armadeus.com>,"' +
                   '<nicolas.colombain@armadeus.com>',
      maintainer='Fabien Marteau',
      maintainer_email='fabien.marteau@armadeus.com',
      packages=find_packages(),
      package_data = {
        '':['*.xml',
            'ghdlsimulationmakefile',
            '*.tpl',
            'busses/*/*',
            'templates/*',] +
          package_files("periphondemand/toolchains") +
          package_files("periphondemand/platforms") +
          package_files("periphondemand/library"),
      },
      zip_safe=False,
      scripts=['periphondemand/bin/pod'],
      license='GPL',
)
