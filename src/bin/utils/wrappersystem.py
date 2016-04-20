#! /usr/bin/python3
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
import shutil
from os.path import join
from os.path import split
from os.path import exists
import glob
from periphondemand.bin.utils.poderror import PodError


def inttobin(num, size):
    """ convert a number num, in binary string with length size
    """
    if num < 0:
        raise PodError("Must be positive number", 1)
    snum = ''
    while num != 0:
        if num % 2 == 0:
            bit = '0'
        else:
            bit = '1'
        snum = bit + snum
        num >>= 1
    if len(snum) < size:
        return '0' * (size - len(snum)) + snum
    elif len(snum) > size:
        return snum[len(snum)-size:]
    else:
        return snum


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


def launch_as_shell(shell_name, commands_file_name):
    """ launch a shell named shell_name, with a
    command script named commands_file_name
    """
    return os.popen("" + shell_name + " " + commands_file_name)


def dir_exist(dirname):
    """ Return True if directory exists"""
    dirname = os.path.expanduser(dirname)
    return os.path.isdir(dirname)


def file_exist(filename):
    """ test if file exist """
    filename = os.path.expanduser(filename)
    return os.path.exists(filename)


def cmd_exist(commandname):
    """ test if a command exist in system """
    ret = os.popen("which " + commandname).read()
    ret.split()
    if ret == "":
        return 0
    else:
        return 1


def rename_file(oldfilepath, newfilepath):
    """ rename file
    """
    try:
        return os.rename(oldfilepath, newfilepath)
    except OSError as error:
        raise PodError(str(error) + "\nrenaming " +
                       str(oldfilepath) + " in " + str(newfilepath))


def rename_dir(olddir, newdir):
    """ Rename directory """
    olddir = os.path.expanduser(olddir)
    newdir = os.path.expanduser(newdir)
    if(os.path.exists(newdir)):
        raise PodError("Directory " + newdir + " exists", 0)
    else:
        return rename_file(olddir, newdir)


def mkdir(name):
    """ make directory """
    try:
        return os.makedirs(name)
    except OSError as error:
        raise PodError("can't make directory " + name + " :\n" + str(error))


def cp_dir(source, target):
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
        for afile in files:
            from_ = join(root, afile)
            to_ = from_.replace(source, target, 1)
            to_directory = split(to_)[0]
            if not exists(to_directory):
                os.makedirs(to_directory)
            shutil.copyfile(from_, to_)


def copy_all_files(source, target):
    """ Copy all file in directory to another directory
    """
    source = os.path.expanduser(source)
    target = os.path.expanduser(target)
    for name in glob.glob(source + "/" + r'*'):
        cp_file(name, target)


def cp_file(filepath, dirpath):
    """ Copy file from filepath to dirpath
    """
    filepath = os.path.expanduser(filepath)
    dirpath = os.path.expanduser(dirpath)
    return shutil.copy(filepath, dirpath + "/")


def rm_dir(dirpath):
    """ delete a directory
    """
    dirpath = os.path.expanduser(dirpath)
    if os.path.exists(dirpath):
        return shutil.rmtree(dirpath)
    else:
        raise PodError("Directory " + dirpath +
                       " doesn't exists can't be deleted", 1)


def rm_file(filepath):
    """ Delete a file """
    filepath = os.path.expanduser(filepath)
    try:
        return os.remove(filepath)
    except OSError:
        return None


def list_files(dirpath):
    """ list file in directory """
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


def list_file_type(dirpath, ext):
    """ list file of certain extension """
    listfile = list_files(dirpath)
    listfile = [filename for filename in listfile if filename.find(".") != -1]
    return [filename for filename in
            listfile if filename.split(".")[-1] == ext]


def list_dir(dirpath):
    """ list directory in directory, ignore hiding dir (.something)
    """
    if(dirpath.strip() == ""):
        dirpath = "."
    else:
        dirpath = os.path.expanduser(dirpath)
    thelist = list_files(dirpath)
    returnlist = []
    # Suppressing files, keep only directory
    for thefile in thelist:
        if os.path.isdir(dirpath + "/" + thefile):
            returnlist.append(thefile)
    return returnlist


def del_all(dirpath):
    """ delete all files and directory in dirpath """
    dirpath = os.path.expanduser(dirpath)
    del_all_dir(dirpath)
    del_all_files(dirpath)


def del_all_dir(dirpath):
    """ Delete all directories under path """
    dirpath = os.path.expanduser(dirpath)
    try:
        for thedir in list_dir(dirpath):
            rm_dir(dirpath + "/" + thedir)
    except IOError as error:
        raise PodError(str(error), 0)


def del_all_files(dirpath):
    """ Delete all files under path """
    dirpath = os.path.expanduser(dirpath)
    try:
        for thefile in list_files(dirpath):
            os.remove(dirpath + "/" + thefile)
    except IOError as error:
        raise PodError(str(error), 0)


def shell_ls(dirpath):
    """ use the operating system command to list file"""
    os.system("ls --color " + dirpath)


def pwd():
    """ return current dir
    """
    return os.getcwd()


def chdir(path):
    """ Change current directory """
    os.chdir(path)
