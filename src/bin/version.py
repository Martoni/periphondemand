#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     version.py
# Purpose:  
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  15/05/2009
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

import re

REVISION = "$Revision: 59 $"
URL = "$HeadURL: https://periphondemand.svn.sourceforge.net/svnroot/periphondemand/trunk/setup.py $"

def getVersion():
    if re.search(r"trunk",URL):
        dir="trunk"
        return "HEAD-"+str(getRevision())
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
    return m.group(1).strip()



