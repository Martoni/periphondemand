#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     WrapperXml.py
# Purpose:
#
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
#
# Created:  23/04/2008
# Licence:  GPLv3 or newer
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

__doc__ = ""
__version__ = "1.0.0"
__versionTime__ = "23/04/2008"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import os
import xml.etree.cElementTree as ET
from periphondemand.bin.utils.error import Error
from periphondemand.bin.utils import wrappersystem as sy

def XMLBeautifier(xml_data):
    """
    This function make XML output looks better and more readable.
    Fabrice Mousset <fabrice.mousset@laposte.net>

    Can be done with "indent" function in ElementTree
    """
    xml_text = ""
    xml_ident = 0
    for xml_line in xml_data.split('<'):
        xml_line = xml_line.strip()
        if(len(xml_line) > 0):
            if xml_line.endswith("/>"):
                xml_text += ' '*xml_ident + "<" + xml_line + "\n"
            else:
                if(xml_line.startswith('/')):
                    xml_ident -= 4
                    xml_text += ' '*xml_ident + "<" + xml_line + "\n"
                else:
                    xml_text += ' '*xml_ident + "<" + xml_line + "\n"
                    xml_ident += 4
    return xml_text

class WrapperXml:
    """Simple class manage XML
        attributes:
            tree -- root tree xml component
    """

    def __init__(self,**args):
        """ init function,
            __init__(self,node)   # parameter is wrapperXml node
            __init__(self,etnode) # parameter is ElementTree node
            __init__(self,nodename)
            __init__(self,nodestring)
            __init__(self,file)
        """
        if "node" in args:
            self.__initnode(args["node"])
        elif "etnode" in args:
            self.__initetnode(args["etnode"])
        elif "nodename" in args:
            self.__initnodename(args["nodename"])
        elif "nodestring" in args:
            self.__initnodestring(args["nodestring"])
        elif "file" in args:
            self.__initfile(args["file"])
        else:
            raise Error("Keys unknown in WrapperXml",0)

    def __initfile(self,filename):
        try:
            self.openXml(filename)
        except IOError,e:
            raise Error(str(e),0)
    def __initnode(self,node):
        self.tree = node.tree
    def __initetnode(self,etnode):
        self.tree = etnode
    def __initnodename(self,nodename):
        self.tree = ET.Element(nodename)
    def __initnodestring(self,nodestring):
        try:
            self.tree = ET.fromstring(nodestring)
        except SyntaxError,e:
              raise Error("XML malformed :\n"+str(e),0)

    def __str__(self):
        return ('<?xml version="1.0" encoding="utf-8"?>\n' +\
                XMLBeautifier(ET.tostring(self.tree,"utf-8")))

    def getParent(self):
        return self.parent
    def setParent(self,parent):
        self.parent = parent

    def getSubNodeList(self,nodename,subnodename):
        """ Return a list of subnodes
        """
        nodelist = []
        for element in self.getNode(nodename).getNodeList(subnodename):
            nodelist.append(element)
        return nodelist

    def getNodeList(self,nodename):
        """ Return a list of nodes
        """
        nodelist =[]
        for node in self.tree.findall(nodename):
            tmp = WrapperXml(etnode=node)
            nodelist.append(tmp)
        return nodelist

    def getNode(self,nodename):
        """ return the first node found
        """
        try:
            return self.getNodeList(nodename)[0]
        except IndexError:
            return None

    def addSubNode(self,**keys):
        """ Add a subnode in the object tree
            addSubNode(self,nodename,subnode)
            addSubNode(self,nodename,subnodename,attributename,value)
            addSubNode(self,nodename,subnodename,attributedict)
        """
        if "nodename" in keys:
            node = self.getNode(nodename=keys["nodename"])
            if node==None:
                node = self.addNode(nodename=keys["nodename"])
            if "subnode" in keys:
                return node.addNode(node=keys["subnode"])
            elif "subnodename" in keys:
                subnodename = keys["subnodename"]
                if "attributename" in keys:
                    return node.addNode(nodename=subnodename,
                                        attributename=keys["attributename"],
                                        value=keys["value"])
                elif "attributedict" in keys:
                    return node.addNode(nodename=subnodename,
                                        attributedict=keys["attributedict"])
                else:
                    raise Error("Key not known in addSubNode "+str(keys),0)
            else:
                raise Error("Key not known in addSubNode"+str(keys),0)
        else:
            raise Error("Key not known in addSubNode"+str(keys),0)

    def addNode(self,**keys):
        """ Add a node in the tree,
            addNode(self,node)
            addNode(self,nodename)
            addNode(self,nodename,attributename,value)
            addNode(self,nodename,attributedict)
        """
        if "node" in keys:
            node = keys["node"]
        elif "nodename" in keys:
            node =WrapperXml(nodename=keys["nodename"])
            if "attributename" in keys:
                node.setAttribute(keys["attributename"],keys["value"])
            elif "attributedict" in keys:
                attributedict = keys["attributedict"]
                for key in attributedict:
                    node.setAttribute(key,attributedict[key])
        else:
            raise Error("Keys not known in addNode",0)

        try:
            self.tree.append(node.tree)
        except AttributeError: # if tree doesn't exits
            self.tree = node.tree
        return node

    def delNode(self, node, attribute=None, value=None):
        """ delete a node, attribute can be single or, if they're multiple
            attribute, attribute is a dictionnary
            delNode(self, node, attribute=None, value=None)
            delNode(self, node_name, {attribute1:value1, attribute1:value1, ...})
        """
        if type(node) == str:
            nodename = node
            for element in self.getNodeList(nodename):
                if(element.tree.tag == nodename):
                    if(attribute==None):
                        self.tree.remove(element.tree)
                    elif (type(attribute) == str) and (element.getAttribute(attribute) == value):
                        self.tree.remove(element.tree)
                    elif type(attribute) == dict:
                        match = 1
                        for key in attribute:
                            if element.getAttribute(key) != attribute[key]:
                                match = 0
                        if match==1:
                            self.tree.remove(element.tree)
        else:
            self.tree.remove(node.tree)

    def delSubNode(self,nodename,subnodename,attribute=None,value=None):
        node = self.getNode(nodename)
        node.delNode(subnodename,attribute,value)

    def getAttribute(self,key,subnodename=None):
        if subnodename == None:
            return self.tree.get(key)
        else:
            node = self.tree.find(subnodename)
            if node == None:
                raise Error("No tag named "+str(subnodename))
            return node.get(key)
        raise Error("No attribute named "+key+" for tag "+str(subnodename))

    def setAttribute(self,key,value,subname=None):
        if subname == None:
            self.tree.attrib[key] = value
            return value
        else:
            if self.tree.find(subname) == None:
                ET.SubElement(self.tree,subname)
            self.tree.find(subname).attrib[key] = value
            return value

    def getDescription(self):
        try:
            return self.tree.find("description").text
        except AttributeError:
            return ""

    def setDescription(self,description):
        if self.tree.find("description") is not None:
            self.tree.find("description").text = description
        else:
            desc = ET.SubElement(self.tree,"description")
            desc.text = description
        return description

    def getSize(self):
        return self.getAttribute("size")

    def setSize(self,size):
        self.setAttribute("size",str(size))
    def getName(self):
        return self.getAttribute("name")
    def setName(self,value):
        return self.setAttribute("name",value)
    def getVersion(self):
        return self.getAttribute("version")
    def setVersion(self,version):
        return self.setAttribute("version",version)

    def openXml(self,filename,string=None):
        """ open xml, parameters can be filename or xml string
        """
        if type(filename)==str and string!=None:
              try:
                  self.tree = ET.fromstring(filename)
              except SyntaxError,e:
                  raise Error("Xml malformed in "+filename+" : \n"+str(e),0)
        else:
           try:
                xmlfile = open(filename,'r')
           except IOError,e:
                raise Error(str(e),0)
           content = xmlfile.read().replace(r'<?xml version="1.0" encoding="utf-8"?>','')
           try:
               self.tree = ET.fromstring(content)
           except SyntaxError,e:
                raise Error("Xml malformed in "+filename+" :\n"+str(e),0)

    def createXml(self,tag):
        self.tree = ET.Element(tag)

    def saveXml(self,pathname):
        f = open(pathname,"w")
        f.write(str(self))
        f.close()

    def isVoid(self):
        return self.void

