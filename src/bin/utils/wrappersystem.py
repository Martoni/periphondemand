#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     WrapperSystem.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  25/04/2008
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
""" Manage Operating system commands """


import os  # rename, copyfile, ...
import re  # regexp
import sys
import shutil
from os.path import join, splitext, split, exists
import glob
from periphondemand.bin.utils.error import PodError
from periphondemand.bin.define import COLOR_DEBUG
from periphondemand.bin.define import COLOR_END


def inttobin(n, size):
    """ convert a number n, in binary string with length size
    """
    if n < 0:
        raise PodError("Must be positive number", 1)
    s = ''
    while n != 0:
        if n % 2 == 0:
            bit = '0'
        else:
            bit = '1'
        s = bit + s
        n >>= 1
    if len(s) < size:
        return '0' * (size - len(s)) + s
    elif len(s) > size:
        return s[len(s)-size:]
    else:
        return s


def check_name(name):
    """ This function check if name contain only authorized characters
    authorized characters : [a-z],[0-9],'_'
    """
    if re.match('[0-9]', name[0]):
        raise PodError("Digit forbiden in beginning of name")
    for car in name:
        if re.match('[a-z]', car):
            continue
        if re.match('[0-9]', car):
            continue
        if car == '_':
            continue
        raise PodError("Character " + car +
                    " forbiden, must be included in [a-z],[0-9],_", 0)

    if re.search(r'__', name):
        raise PodError(" Double '_' forbiden", 0)
    if re.match('^_', name):
        raise PodError(" '_' at the begining forbiden", 0)
    if re.search(r'_$', name):
        raise PodError(" '_' at the end forbiden", 0)


def launchAShell(shell_name, commands_file_name):
    """ launch a shell named shell_name, with a
    command script named commands_file_name
    """
    return os.popen("" + shell_name + " " + commands_file_name)


def dirExist(dirname):
    dirname = os.path.expanduser(dirname)
    return os.path.isdir(dirname)


def fileExist(filename):
    """ test if file exist """
    filename = os.path.expanduser(filename)
    return os.path.exists(filename)


def commandExist(commandname):
    """ test if a command exist in system """
    ret = os.popen("which " + commandname).read()
    ret.split()
    if ret == "":
        return 0
    else:
        return 1


def renameFile(oldfilepath, newfilepath):
    """ rename file
    """
    try:
        return os.rename(oldfilepath, newfilepath)
    except OSError, error:
        raise PodError(str(error) + "\nrenaming " +
                    str(oldfilepath) + " in " + str(newfilepath))


def renameDirectory(olddir, newdir):
    olddir = os.path.expanduser(olddir)
    newdir = os.path.expanduser(newdir)
    if(os.path.exists(newdir)):
        raise PodError("Directory " + newdir + " exists", 0)
    else:
        return renameFile(olddir, newdir)


def makeDirectory(name):
    """ make dir
    """
    try:
        return os.makedirs(name)
    except OSError, error:
        raise PodError("can't make directory " + name + " :\n"+str(error))


def copyDirectory(source, target):
    """ Copy directory
    """
    source = os.path.expanduser(source)
    target = os.path.expanduser(target)
    target = target + "/" + source.split("/")[-1] + "/"
    # code from http://
    # tarekziade.wordpress.com/2008/07/08/shutilcopytree-small-improvement/
    if not os.path.exists(target):
        os.mkdir(target)
    for root, dirs, files in os.walk(source):
        if '.svn' in dirs:
            dirs.remove('.svn')  # don't visit .svn directories
        for file in files:
            from_ = join(root, file)
            to_ = from_.replace(source, target, 1)
            to_directory = split(to_)[0]
            if not exists(to_directory):
                os.makedirs(to_directory)
            shutil.copyfile(from_, to_)


def copyAllFile(source, target):
    """ Copy all file in directory to another directory
    """
    source = os.path.expanduser(source)
    target = os.path.expanduser(target)
    for name in glob.glob(source + "/" + r'*'):
        copyFile(name, target)


def copyFile(filepath, dirpath):
    """ Copy file from filepath to dirpath
    """
    filepath = os.path.expanduser(filepath)
    dirpath = os.path.expanduser(dirpath)
    namefile = filepath.split("/")[-1]
    return shutil.copy(filepath, dirpath + "/")


def delDirectory(dirpath):
    """ delete a directory
    """
    dirpath = os.path.expanduser(dirpath)
    if os.path.exists(dirpath):
        return shutil.rmtree(dirpath)
    else:
        raise PodError("Directory " + dirpath +
                    " doesn't exists can't be deleted", 1)


def delFile(dirpath):
    dirpath = os.path.expanduser(dirpath)
    try:
        return os.remove(dirpath)
    except OSError:
        return None


def listFiles(dirpath):
    """ list file in directory
    """
    if(dirpath.strip() == ""):
        dirpath = "."
    else:
        dirpath = os.path.expanduser(dirpath)
    thelist = os.listdir(dirpath)
    # suppressing hiding files
    listout = []
    for filename in thelist:
        if not re.match(r'^\.', filename):
            listout.append(filename)
    return listout


def listFileType(dirpath, ext):
    """ list file of certain extension """
    listfile = listFiles(dirpath)
    listfile = [filename for filename in listfile if filename.find(".") != -1]
    return [filename for filename in
            listfile if filename.split(".")[-1] == ext]


def listDirectory(dirpath):
    """ list directory in directory, ignore hiding dir (.something)
    """
    if(dirpath.strip() == ""):
        dirpath = "."
    else:
        dirpath = os.path.expanduser(dirpath)
    thelist = listFiles(dirpath)
    returnlist = []
    # Suppressing files, keep only directory
    for thefile in thelist:
        if os.path.isdir(dirpath + "/" + thefile):
            returnlist.append(thefile)
    return returnlist


def deleteAll(dirpath):
    """ delete all files and directory in dirpath """
    dirpath = os.path.expanduser(dirpath)
    deleteAllDir(dirpath)
    deleteAllFiles(dirpath)


def deleteAllDir(dirpath):
    dirpath = os.path.expanduser(dirpath)
    try:
        for thedir in listDirectory(dirpath):
            delDirectory(dirpath + "/" + thedir)
    except IOError, error:
        raise PodError(str(error), 0)


def deleteAllFiles(dirpath):
    dirpath = os.path.expanduser(dirpath)
    try:
        for thefile in listFiles(dirpath):
            os.remove(dirpath + "/" + thefile)
    except IOError, error:
        raise PodError(str(error), 0)


def ls(dirpath):
    """ use the operating system command to list file"""
    os.system("ls --color " + dirpath)


def pwd():
    """ return current dir
    """
    return os.getcwd()


def chdir(path):
    os.chdir(path)


def printDebug(message):
    """ print debug message with color if settings.color is set """
    try:
        from periphondemand.utils.settings import Settings
    except ImportError:
        print "Warning: cannot import settings"
        print "DEBUG: " + message
        return
    settings = Settings()

    if settings.color() == 1:
        print COLOR_DEBUG + message + COLOR_END
    else:
        print "DEBUG: " + message

if __name__ == "__main__":
    print listDirectory("/home/fabien/podmylib")
    print commandExist("xtclsh")
    sys.exit(0)
    # test
    try:
        check_name("plop0")
        check_name("plop_plop8")
        check_name("plop*plop0")
    except PodError, error:
        print error
    try:
        check_name("plop-plop")
    except PodError, error:
        print error

    try:
        check_name("_plop")
    except PodError, error:
        print error
    try:
        check_name("plop_")
    except PodError, error:
        print error
    try:
        check_name("plop__plop")
    except PodError, error:
        print error
