#! /usr/bin/python
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
sys.path.append("src/bin/")
from version import VERSION


def visit(libfile, dirname, names):
    """ function used for getLibraryTree to walk throw library tree"""
    for file in names:
        filepath = os.path.join(dirname, file)
        if not os.path.isdir(filepath):
            if not re.search(r".svn", filepath):
                # FIXME:
                # I can't find how to split with os.path !
                # will be used when package_data work
                #realpath = "/".join(filepath.split("/")[1:])
                #libfile.append(realpath)
                libfile.append(filepath)


def getTree(directory):
    """ return a tuple list of files """
    libfile = []
    os.path.walk(os.path.join("src", directory), visit, libfile)
    new_libfile = []
    for path_file in libfile:
        new_libfile.append('/'.join(path_file.split('/')[1:]))
    if (directory == "platforms"):
        print str(new_libfile)
    return new_libfile

# Package files
package_files_list = []
package_files_list.extend(getTree("library"))
package_files_list.extend(getTree("platforms"))
package_files_list.extend(getTree("templates"))
package_files_list.extend(getTree("busses"))
package_files_list.extend(getTree("toolchains"))
package_files_list.extend(getTree("tests"))

setup(name='PeriphOnDemand',
      version=VERSION,
      url='https://sourceforge.net/projects/periphondemand',
      author='Fabien Marteau and Nicolas Colombain',
      author_email='<fabien.marteau@armadeus.com>,"' +
                   '<nicolas.colombain@armadeus.com>',
      maintainer='Fabien Marteau',
      maintainer_email='fabien.marteau@armadeus.com',
      package_dir={"periphondemand": "src"},
      packages=['periphondemand',
                'periphondemand.bin',
                'periphondemand.bin.code',
                'periphondemand.bin.code.vhdl',
                'periphondemand.bin.commandline',
                'periphondemand.bin.core',
                'periphondemand.bin.toolchain',
                'periphondemand.bin.utils',
                'periphondemand.toolchains',
                ],
      package_data={'periphondemand': package_files_list},
      scripts=['src/bin/pod'],
      license='GPL',
)
