#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     setup.py
# Purpose:  
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  16/02/2009
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

from distutils.core import setup
import os,re

REVISION = "$Revision$"
URL = "$HeadURL$"


def getVersion():
    if re.search(r"trunk",URL):
        dir="trunk"
        return "HEAD "+str(getRevision())
    elif re.search(r"tags",URL):
        dir="tags"
        m = re.match(r".*tags\/(.*?)\/.*",url)
        name=m.group(1)
        return name
    elif re.search(r"branches",URL):
        dir="branches"
        m = re.match(r".*branches\/(.*?)\/.*",url)
        name=m.group(1)
        return name+"-"+str(getRevision())

def getRevision():
    m = re.match(r"\$Revision:(.*?)\$",REVISION)
    return m.group(1)


def getTestFilesList():
    """ return the list of testfile under tests/ directory """
    dirlist = os.listdir("periphondemand/tests/")
    testlist = ["periphondemand/tests/"+test for test in dirlist if re.match("\d\d*",test)]
    return testlist

libfile=[]
def visit(arg,dirname,name):
    """ function used for getLibraryTree to walk throw library tree"""
    print "visiting "+dirname
    for file in name:
        if not os.path.isdir(dirname+"/"+file):
            libfile.append((dirname,[dirname+"/"+file]))

def getTree(directory):
    """ return a tuple list of files """
    os.path.walk("periphondemand/"+directory+"/",visit,None)
    return libfile

datafiles=[
    ('/usr/bin',['periphondemand/bin/pod']),
    ('periphondemand/tests',getTestFilesList()),
    ('periphondemand/',['VERSION'])
]

datafiles.extend(getTree("library"))
datafiles.extend(getTree("platforms"))
datafiles.extend(getTree("templates"))
datafiles.extend(getTree("busses"))
datafiles.extend(getTree("toolchains"))

setup(  name='PeriphOnDemand',
        version=getVersion(),
        url='https://sourceforge.net/projects/periphondemand',
        author='Fabien Marteau and Nicolas Colombain',
        author_email='<fabien.marteau@armadeus.com>,<nicolas.colombain@armadeus.com>,',
        maintainer='Fabien Marteau',
        maintainer_email='fabien.marteau@armadeus.com',
        packages=['periphondemand',
                  'periphondemand.bin',
                  'periphondemand.bin.code',
                  'periphondemand.bin.code.vhdl',
                  'periphondemand.bin.commandline',
                  'periphondemand.bin.core',
                  'periphondemand.bin.toolchain',
                  'periphondemand.bin.utils',
                  ],
        data_files=datafiles,
        license='GPL',
)
