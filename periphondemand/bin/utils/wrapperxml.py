#! /usr/bin/python3
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
        if not hasattr(self, 'void'):
            self.void = True

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
            self.open_xml(filename)
        except IOError as error:
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
        except SyntaxError as error:
            raise PodError("XML malformed :\n" + str(error), 0)

    def __str__(self):
        return ('<?xml version="1.0" encoding="utf-8"?>\n' +
                ET.tostring(self.tree, "utf-8").decode("utf-8"))

    @property
    def text(self):
        """ Return node's text content
        """
        text = self.tree.text
        if not text:
            return ""
        else:
            return text

    @text.setter
    def text(self, text):
        """ set node's text content
        """
        self.tree.text = text

    def get_subnodes(self, nodename, subnodename):
        """ Return a list of subnodes
        """
        nodelist = []
        try:
            for element in self.get_node(nodename).get_nodes(subnodename):
                nodelist.append(element)
            return nodelist
        except AttributeError:
            return []

    def get_nodes(self, nodename):
        """ Return a list of nodes """
        nodelist = []
        for node in self.tree.findall(nodename):
            tmp = WrapperXml(etnode=node)
            nodelist.append(tmp)
        return nodelist

    def get_node(self, nodename):
        """ return the first node found """
        try:
            return self.get_nodes(nodename)[0]
        except IndexError:
            return None

    def add_subnode(self, **keys):
        """ Add a subnode in the object tree
            add_subnode(self,nodename,subnode)
            add_subnode(self,nodename,subnodename,attributename,value)
            add_subnode(self,nodename,subnodename,attributedict)
        """
        if "nodename" in keys:
            node = self.get_node(nodename=keys["nodename"])
            if node is None:
                node = self.add_node(nodename=keys["nodename"])
            if "subnode" in keys:
                return node.add_node(node=keys["subnode"])
            elif "subnodename" in keys:
                subnodename = keys["subnodename"]
                if "attributename" in keys:
                    return node.add_node(nodename=subnodename,
                                         attributename=keys["attributename"],
                                         value=keys["value"])
                elif "attributedict" in keys:
                    return node.add_node(nodename=subnodename,
                                         attributedict=keys["attributedict"])
                else:
                    raise PodError("Key not known in addSubNode " + str(keys))
            else:
                raise PodError("Key not known in addSubNode" + str(keys))
        else:
            raise PodError("Key not known in addSubNode" + str(keys))

    def add_node(self, **keys):
        """ Add a node in the tree,
            add_node(self,node)
            add_node(self,nodename)
            add_node(self,nodename,attributename,value)
            add_node(self,nodename,attributedict)
        """
        if "node" in keys:
            node = keys["node"]
        elif "nodename" in keys:
            node = WrapperXml(nodename=keys["nodename"])
            if "attributename" in keys:
                node.set_attr(keys["attributename"], keys["value"])
            elif "attributedict" in keys:
                attributedict = keys["attributedict"]
                for key in attributedict:
                    node.set_attr(key, attributedict[key])
        else:
            raise PodError("Keys not known in addNode", 0)

        try:
            self.tree.append(node.tree)
        except AttributeError:  # if tree doesn't exits
            self.tree = node.tree
        return node

    def del_node(self, node, attribute=None, value=None):
        """delete a node, attribute can be single or, if they're multiple
           attribute, attribute is a dictionnary
           del_node(self, node, attribute=None, value=None)
           del_node(self, node_name, {attribute1:value1, attribute1:value1,..})
        """
        if type(node) == str:
            nodename = node
            for element in self.get_nodes(nodename):
                if(element.tree.tag == nodename):
                    if attribute is None:
                        self.tree.remove(element.tree)
                    elif (type(attribute) == str) and\
                            (element.get_attr_value(attribute) == value):
                        self.tree.remove(element.tree)
                    elif type(attribute) == dict:
                        match = 1
                        for key in attribute:
                            if element.get_attr_value(key) !=\
                                    attribute[key]:
                                match = 0
                        if match == 1:
                            self.tree.remove(element.tree)
        else:
            self.tree.remove(node.tree)

    def del_subnode(self, nodename, subnodename, attribute=None, value=None):
        """ Delete a subnode """
        node = self.get_node(nodename)
        node.del_node(subnodename, attribute, value)

    def get_attr_value(self, key, subnodename=None):
        """ Get attribute value of node """
        if subnodename is None:
            return self.tree.get(key)
        else:
            node = self.tree.find(subnodename)
            if node is None:
                raise PodError("No tag named " + str(subnodename))
            return node.get(key)
        raise PodError("No attribute named " + key +
                       " for tag " + str(subnodename))

    def get_attr_names(self, subnodename=None):
        """ get attribute name list """
        if subnodename is None:
            return self.tree.keys()
        else:
            node = self.tree.find(subnodename)
            if node is None:
                raise PodError("No tag named " + str(subnodename))
            return node.keys()
        raise PodError("get_attr_names error")

    def set_attr(self, key, value, subname=None):
        """ set an attribute value """
        if subname is None:
            self.tree.attrib[key] = value
            return value
        else:
            if self.tree.find(subname) is None:
                ET.SubElement(self.tree, subname)
            self.tree.find(subname).attrib[key] = value
            return value

    @property
    def description(self):
        """ get description """
        try:
            return self.tree.find("description").text
        except AttributeError:
            return ""

    @description.setter
    def description(self, description):
        """ set description """
        if self.tree.find("description") is not None:
            self.tree.find("description").text = description
        else:
            desc = ET.SubElement(self.tree, "description")
            desc.text = description
        return description

    @property
    def size(self):
        size = self.get_attr_value("size")
        if size.isdigit():
            return int(size)
        else:
            generic = self.parent.parent.get_generic(str(size))
            value = int(generic.get_attr_value("value"))
            return value

    @size.setter
    def size(self, size):
        """ set size """
        self.set_attr("size", str(size))

    @property
    def name(self):
        """ return the name of the tree """
        return self.get_attr_value("name")

    @name.setter
    def name(self, value):
        """ set the name of the tree """
        return self.set_attr("name", value)

    @property
    def version(self):
        """ get the version """
        return self.get_attr_value("version")

    @version.setter
    def version(self, version):
        """ set the version """
        return self.set_attr("version", version)

    def open_xml(self, filename, string=None):
        """ open xml, parameters can be filename or xml string
        """
        if type(filename) == str and string is not None:
            try:
                self.tree = ET.fromstring(filename)
            except SyntaxError as error:
                raise PodError("Xml malformed in " +
                               filename + " : \n" + str(error))
        else:
            try:
                xmlfile = open(filename, 'r')
            except IOError as error:
                raise PodError(str(error), 0)
            content =\
                xmlfile.read().replace(
                    r'<?xml version="1.0" encoding="utf-8"?>', '')
            try:
                self.tree = ET.fromstring(content)
            except SyntaxError as error:
                raise PodError("Xml malformed in " +
                               filename + " :\n" + str(error))

    def create_xml(self, tag):
        """ create xml with tag as top"""
        self.tree = ET.Element(tag)

    def save_xml(self, pathname):
        """ save xml in file """
        fxml = open(pathname, "w")
        fxml.write(str(self))
        fxml.close()

    @property
    def num(self):
        """ Get the instance number """
        return self.get_attr_value("num")

    @num.setter
    def num(self, num):
        """ select the instance number """
        return self.set_attr("num", str(num))

    def get_instance(self, instancename=None):
        """ get the parent instance of this interface """
        if instancename is None:
            instancename = self.instancename
        return self.parent.get_instance(instancename)
