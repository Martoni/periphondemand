#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     WrapperXml.py
# Purpose:
#
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
#
# Created:  23/04/2008
# Licence:  GPLv3 or newer
# ----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
# ----------------------------------------------------------------------------
""" main xml object """

import xml.etree.cElementTree as ET

from periphondemand.bin.utils.poderror import PodError


class WrapperXml(object):
    """Simple class manage XML
        attributes:
            tree -- root tree xml component
    """

    def __init__(self, **args):
        """ init function,
            __init__(self,node)   # parameter is wrapperXml node
            __init__(self,etnode) # parameter is ElementTree node
            __init__(self,nodename)
            __init__(self,nodestring)
            __init__(self,file)
        """

        if not hasattr(self, 'parent'):
            self.parent = None
        if not hasattr(self, 'tree'):
            self.tree = None

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
            raise PodError("Keys unknown in WrapperXml", 0)

    def __initfile(self, filename):
        """ initialize with filename"""
        try:
            self.openXml(filename)
        except IOError, error:
            raise PodError(str(error), 0)

    def __initnode(self, node):
        """ initilize with node """
        self.tree = node.tree

    def __initetnode(self, etnode):
        """ initialize with etnode """
        self.tree = etnode

    def __initnodename(self, nodename):
        """ initialize with nodename """
        self.tree = ET.Element(nodename)

    def __initnodestring(self, nodestring):
        """ initialize with nodestring """
        try:
            self.tree = ET.fromstring(nodestring)
        except SyntaxError, error:
            raise PodError("XML malformed :\n" + str(error), 0)

    def __str__(self):
        return ('<?xml version="1.0" encoding="utf-8"?>\n' +
                ET.tostring(self.tree, "utf-8"))

    def getSubNodeList(self, nodename, subnodename):
        """ Return a list of subnodes
        """
        nodelist = []
        try:
            for element in self.getNode(nodename).getNodeList(subnodename):
                nodelist.append(element)
            return nodelist
        except AttributeError:
            return []

    def getNodeList(self, nodename):
        """ Return a list of nodes
        """
        nodelist = []
        for node in self.tree.findall(nodename):
            tmp = WrapperXml(etnode=node)
            nodelist.append(tmp)
        return nodelist

    def getNode(self, nodename):
        """ return the first node found
        """
        try:
            return self.getNodeList(nodename)[0]
        except IndexError:
            return None

    def addSubNode(self, **keys):
        """ Add a subnode in the object tree
            addSubNode(self,nodename,subnode)
            addSubNode(self,nodename,subnodename,attributename,value)
            addSubNode(self,nodename,subnodename,attributedict)
        """
        if "nodename" in keys:
            node = self.getNode(nodename=keys["nodename"])
            if node is None:
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
                    raise PodError("Key not known in addSubNode " + str(keys))
            else:
                raise PodError("Key not known in addSubNode" + str(keys))
        else:
            raise PodError("Key not known in addSubNode" + str(keys))

    def addNode(self, **keys):
        """ Add a node in the tree,
            addNode(self,node)
            addNode(self,nodename)
            addNode(self,nodename,attributename,value)
            addNode(self,nodename,attributedict)
        """
        if "node" in keys:
            node = keys["node"]
        elif "nodename" in keys:
            node = WrapperXml(nodename=keys["nodename"])
            if "attributename" in keys:
                node.setAttribute(keys["attributename"], keys["value"])
            elif "attributedict" in keys:
                attributedict = keys["attributedict"]
                for key in attributedict:
                    node.setAttribute(key, attributedict[key])
        else:
            raise PodError("Keys not known in addNode", 0)

        try:
            self.tree.append(node.tree)
        except AttributeError:  # if tree doesn't exits
            self.tree = node.tree
        return node

    def delNode(self, node, attribute=None, value=None):
        """ delete a node, attribute can be single or, if they're multiple
            attribute, attribute is a dictionnary
            delNode(self, node, attribute=None, value=None)
            delNode(self, node_name, {attribute1:value1, attribute1:value1,..})
        """
        if type(node) == str:
            nodename = node
            for element in self.getNodeList(nodename):
                if(element.tree.tag == nodename):
                    if attribute is None:
                        self.tree.remove(element.tree)
                    elif (type(attribute) == str) and\
                            (element.getAttributeValue(attribute) == value):
                        self.tree.remove(element.tree)
                    elif type(attribute) == dict:
                        match = 1
                        for key in attribute:
                            if element.getAttributeValue(key) !=\
                                    attribute[key]:
                                match = 0
                        if match == 1:
                            self.tree.remove(element.tree)
        else:
            self.tree.remove(node.tree)

    def delSubNode(self, nodename, subnodename, attribute=None, value=None):
        node = self.getNode(nodename)
        node.delNode(subnodename, attribute, value)

    def getAttributeValue(self, key, subnodename=None):
        if subnodename is None:
            return self.tree.get(key)
        else:
            node = self.tree.find(subnodename)
            if node is None:
                raise PodError("No tag named " + str(subnodename))
            return node.get(key)
        raise PodError("No attribute named " + key +
                       " for tag " + str(subnodename))

    def getAttributeNameList(self, subnodename=None):
        if subnodename is None:
            return self.tree.keys()
        else:
            node = self.tree.find(subnodename)
            if node is None:
                raise PodError("No tag named " + str(subnodename))
            return node.keys()
        raise PodError("getAttributeNameList error")

    def setAttribute(self, key, value, subname=None):
        if subname is None:
            self.tree.attrib[key] = value
            return value
        else:
            if self.tree.find(subname) is None:
                ET.SubElement(self.tree, subname)
            self.tree.find(subname).attrib[key] = value
            return value

    def getDescription(self):
        try:
            return self.tree.find("description").text
        except AttributeError:
            return ""

    def setDescription(self, description):
        if self.tree.find("description") is not None:
            self.tree.find("description").text = description
        else:
            desc = ET.SubElement(self.tree, "description")
            desc.text = description
        return description

    @property
    def size(self):
        return self.getAttributeValue("size")

    @size.setter
    def size(self, size):
        self.setAttribute("size", str(size))

    def getName(self):
        return self.getAttributeValue("name")

    def setName(self, value):
        return self.setAttribute("name", value)

    @property
    def version(self):
        """ get the version """
        return self.getAttributeValue("version")

    @version.setter
    def version(self, version):
        """ set the version """
        return self.setAttribute("version", version)

    def openXml(self, filename, string=None):
        """ open xml, parameters can be filename or xml string
        """
        if type(filename) == str and string is not None:
            try:
                self.tree = ET.fromstring(filename)
            except SyntaxError, error:
                raise PodError("Xml malformed in " +
                               filename + " : \n" + str(error))
        else:
            try:
                xmlfile = open(filename, 'r')
            except IOError, error:
                raise PodError(str(error), 0)
            content =\
                xmlfile.read().replace(
                    r'<?xml version="1.0" encoding="utf-8"?>', '')
            try:
                self.tree = ET.fromstring(content)
            except SyntaxError, error:
                raise PodError("Xml malformed in " +
                               filename + " :\n" + str(error))

    def createXml(self, tag):
        self.tree = ET.Element(tag)

    def saveXml(self, pathname):
        f = open(pathname, "w")
        f.write(str(self))
        f.close()

    def isVoid(self):
        return self.void
