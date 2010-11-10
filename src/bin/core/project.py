#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Project.py
# Purpose:  
#
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
#
# Created:  24/04/2008
# Licence:  GPLv3 or newer
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

__doc__ = ""
__version__ = "1.0.0"
__author__ = "Fabien Marteau <fabien.marteau@armadeus.com>"

import os,re
from   periphondemand.bin.define import *

from   periphondemand.bin.utils.wrapperxml    import WrapperXml
from   periphondemand.bin.utils.settings      import Settings
from   periphondemand.bin.utils.display       import Display
from   periphondemand.bin.utils.error         import *
from   periphondemand.bin.utils               import wrappersystem as sy

from   periphondemand.bin.core.component      import Component
from   periphondemand.bin.core.platform       import Platform
from   periphondemand.bin.core.library        import Library

from   periphondemand.bin.toolchain.simulation import Simulation
from   periphondemand.bin.toolchain.synthesis  import Synthesis
from   periphondemand.bin.toolchain.driver     import Driver


settings = Settings()
display  = Display()

class Project(WrapperXml):
    """This class manage the project
        attributes:
            instanceslist  -- list of objects component in the project
            settings       -- Settings object containing system parameters
            platform       -- platform oblect containing platform dependances
    """
   
    def __init__(self,projectpathname,void=0,
                 description="insert a description here"):
        """ create project if doesn't exist
        """
        self.void = void
        WrapperXml.__init__(self,nodename="void")
        self.instanceslist = []

        self.simulation    = None
        self.synthesis     = None
        self.driver        = None

        self.library = Library()

        self.bspdir        = None
        self.bspos         = None
        if not self.isVoid():
            if projectpathname.find(XMLEXT) >= 0:
                try:
                    settings.projectpath = os.path.abspath(
                            os.path.dirname(projectpathname))
                except IOError,e:
                    raise Error(str(e),0)
            else:
                settings.projectpath = projectpathname
            settings.author = ""
            name =os.path.basename(projectpathname) 
            if sy.fileExist(projectpathname):
                self.loadProject(projectpathname)
            else:
                self.createProject(name)
            self.setDescription(description)
            
            settings.active_project = self

    def createProject(self,name):
        if sy.dirExist(settings.projectpath):
            raise Error("Can't create project, directory "+name +\
                        " allready exists",0)
        sy.makeDirectory(settings.projectpath)

        sy.makeDirectory(settings.projectpath+BINARYPROJECTPATH)
        sy.makeDirectory(settings.projectpath+COMPONENTSPATH)
        sy.makeDirectory(settings.projectpath+OBJSPATH)

        sy.makeDirectory(settings.projectpath+SIMULATIONPATH)
        sy.makeDirectory(settings.projectpath+SYNTHESISPATH)
        sy.makeDirectory(settings.projectpath+DRIVERSPATH)

        self.createXml("project")
        self.setName(name)
        self.setVersion("1.0")
        self.saveProject()
        self.void = 0

    def loadProject(self,pathname):
        """ Load the  project
        """
        self.openXml(pathname)
        components = self.getNode("components")
        # load components
        if(components):
            for node in components.getNodeList("component"):
                if node.getAttribute("platform")==None:
                    comp = Component(self)
                else:
                    comp = Platform(self,node=self.getNode("platform"))
                try:
                    comp.loadInstance(node.getAttribute("name"))
                except IOError:
                    self.delSubNode("components",
                                    "component",
                                    "name",node.getAttribute("name"))
                    raise Error("Can't open "+node.getAttribute("name")+\
                                    " directory",0)
                else:
                    self.instanceslist.append(comp)

        # load toolchains
        #toolchains = self.getNode("toolchain")
        #if(toolchains):
        #       node = toolchains.getNode("simulation")
        #       if node!=None:
        #           self.simulation = Simulation(self,node.getName())
        #       node = toolchains.getNode("synthesis")
        #       if node!=None:
        #           self.synthesis = Synthesis(self,node.getName())
        try:
            self.synthesis = Synthesis(self)
        except Error,e:
            display.msg(str(e))
        try:
            self.simulation = Simulation(self)
        except Error,e:
            display.msg(str(e))
         

        # Set bus master-slave
        for masterinterface in self.getInterfaceMaster():
            for slave in masterinterface.getSlavesList():
                slaveinterface = slave.getInterface()
                # FIXME: allocMem change address
                masterinterface.allocMem.addInterfaceSlave(slaveinterface)
                slaveinterface.setMaster(masterinterface)

        # set bsp directory
        if self.getNode(nodename="bsp")!= None:
            self.bspdir = self.getNode(nodename="bsp").getAttribute("directory")
        self.void=0

    def setSynthesisToolChain(self,toolchainname):
        if toolchainname not in self.getSynthesisToolChainList():
            raise Error("No toolchain named "+toolchainname+" in POD")
        sy.copyFile(settings.path+TOOLCHAINPATH+SYNTHESISPATH+\
                    "/"+toolchainname+"/"+toolchainname+XMLEXT,
                    settings.projectpath+SYNTHESISPATH+"/")
        sy.renameFile(settings.projectpath+SYNTHESISPATH+"/"+toolchainname+XMLEXT,
                      settings.projectpath+SYNTHESISPATH+"/synthesis"+XMLEXT)
        self.synthesis = Synthesis(self)
 
    def getSynthesisToolChain(self):
        try:
            return self.synthesis
        except:
            return None

    def setSimulationToolChain(self,toolchainname):
        if toolchainname not in self.getSimulationToolChainList():
            raise Error("No toolchain named "+toolchainname+" in POD")
        sy.copyFile(settings.path+TOOLCHAINPATH+SIMULATIONPATH+\
                    "/"+toolchainname+"/"+toolchainname+XMLEXT,
                    settings.projectpath+SIMULATIONPATH+"/")
        sy.renameFile(settings.projectpath+SIMULATIONPATH+"/"+toolchainname+XMLEXT,
                      settings.projectpath+SIMULATIONPATH+"/simulation"+XMLEXT)
        self.simulation = Simulation(self)
  
    def getSimulationToolChain(self):
        try:
            return self.simulation
        except:
            return None

    def setDriverToolChain(self,toolchainname):
        if toolchainname not in self.getDriverToolChainList():
            raise Error("No toolchain named "+toolchainname+" in POD")
        sy.copyFile(settings.path+TOOLCHAINPATH+DRIVERSPATH+\
                    "/"+toolchainname+"/"+toolchainname+XMLEXT,
                    settings.projectpath+DRIVERSPATH+"/")
        sy.renameFile(settings.projectpath+DRIVERSPATH+"/"+toolchainname+XMLEXT,
                      settings.projectpath+DRIVERSPATH+"/drivers"+XMLEXT)
        self.driver = Driver(self)

    def getDriverToolChain(self):
        try:
            return self.driver
        except:
            return None

    def setLanguage(self,language):
        self.setAttribute("name",language,"language")

    def setForce(self, portname, state):
        platform = self.getPlatform()
        interfaces_list = platform.getInterfacesList()
        if len(interfaces_list) != 1:
            raise Error("I found "+str(len(interfaces_list))+\
            " FPGAs ("+str(interfaces_list)+") and multiple FPGA project is not implemented yet.")
        port = interfaces_list[0].getPort(portname)
        if port.getDir() == "in":
            raise Error("The value of this port can't be set because of it's direction (in)")
        port.setForce(state)

    def getForcesList(self):
        """ List FPGA forced FPGA pin """
        platform = self.getPlatform()
        return platform.getForcesList()

    def addinstance(self,**keys):
        """ Add a component in project
            addinstance(self,component)
            addinstance(self,libraryname,componentname)
            addinstance(self,libraryname,componentname,instancename)
            addinstance(self,libraryname,componentname,componentversion)
            addinstance(self,libraryname,componentname,
                                    componentversion,instancename)
        """
        if "component" in keys:
            comp=keys["component"]
            instancename = comp.getInstanceName()
        elif "componentname" in keys and "libraryname" in keys:
            componentname = keys["componentname"]
            libraryname = keys["libraryname"]

            if "instancename" in keys:
                instancename = keys["instancename"]
                # check if instancename is not <componentname><number><number>
                if re.match(r'^'+componentname+'\d{2}$',instancename):
                    raise Error("Instance name forbiden, it's reserved for "+\
                            "automatic instance name generation :"+instancename,0)
                #check instance availability
                for instance in self.getInstancesList():
                    if instance.getName() == instancename:
                        raise Error("This instance name already exists",0)
            else:
                instancename =\
                        componentname+\
                        "%02d"%self.getInstanceAvailability(componentname)

            if "componentversion" in keys:
                componentversion = keys["componentversion"]
            else:
                componentversion = None
            # Load and create component
            if (componentname == instancename) :
                raise Error("Instance name can't be the same as component name",0)
            comp = Component(self)
            comp.loadNewInstance(libraryname,
                                  componentname,
                                  componentversion,
                                  instancename)
            comp.setNum(self.getInstanceAvailability(componentname))
        else:
            raise Error("Key not known in addinstance",0)

        #Add component to project
        self.instanceslist.append(comp)
        if comp.getName() != "platform":
            self.addSubNode(nodename="components",
                            subnodename="component",
                            attributename="name",
                            value=instancename)
        else:
            attrib = {"name":instancename,"platform":"true"}
            self.addSubNode(nodename="components",
                            subnodename="component",
                            attributedict=attrib)
        display.msg("Component "+comp.getName()+" added as "+instancename)

    def getInterfaceMaster(self):
        """ Return a list of master interface
        """
        interfacelist = []
        for instance in self.getInstancesList():
            for interface in instance.getInterfacesList():
                if interface.getClass() == "master":
                    interfacelist.append(interface)
        return interfacelist

    def getInterfaceSlave(self):
        """ Return a list of slave interface
        """
        interfacelist = []
        for instance in self.getInstancesList():
            for interface in instance.getInterfacesList():
                if interface.getClass() == "slave":
                    interfacelist.append(interface)
        return interfacelist

    def getSysconsList(self):
        """ return syscon interface list
        """
        sysconlist = []
        for instance in self.getInstancesList():
            for interface in instance.getInterfacesList():
                if interface.getClass() == "clk_rst":
                    if len(interface.getPortsList()) == 2:
                        direction = "ok"
                        for port in interface.getPortsList():
                            if port.getDir() != "out":
                                direction="nok"
                        if direction=="ok":
                            sysconlist.append(interface)
        return sysconlist

    def getInstance(self,instancename):
        """ Return the instance by name
        """
        for instance in self.getInstancesList():
            if instance.getInstanceName() == instancename:
                return instance
        raise Error("Instance " + instancename + " doesn't exists",1)

    def getInstancesList(self):
        return self.instanceslist
    def getVariablePortsList(self):
        """ Get list of all variable ports available in project
        """
        variable_ports_list = []
        for port in self.getPortsList():
            if port.isvariable():
                variable_ports_list.append(port)
        return variable_ports_list
    def getPortsList(self):
        """ Get list of all ports available in project
        """
        ports_list = []
        for instance in self.getInstancesList():
            for interface in instance.getInterfacesList():
                for port in interface.getPortsList():
                    ports_list.append(port)
        return ports_list
    def getInstanceListofComponent(self,componentname):
        """ return a list of instances for a componentname """
        listinstance = []
        for instance in self.getInstancesList():
            if instance.getName() == componentname:
                listinstance.append(instance)
        return listinstance

    def getInstanceAvailability(self,componentname):
        """ Return the number of the same component in project
        """
        cmpt = 0
        if self.getNode("components") ==None:
            return 0
        for element in self.getInstancesList():
            if element.getName() == componentname: cmpt = cmpt + 1
        return cmpt

    def getPlatform(self):
        """ return component instance platform
        """
        for component in self.getInstancesList():
            if component.getName() == "platform":
                return component
        raise Error("No platform in project",1)

    def getPlatformName(self):
        """ return platform name """
        return self.getNode("platform").getAttribute("name")

    def getListClockPorts(self):
        """ return a list of external clock port
        """
        # looking for port connected to platform with type="CLK" and "in" direction
        portlist = []
        platformname = self.getPlatform().getInstanceName()
        for instance in [instance for instance in self.getInstancesList()]:
            if not instance.isPlatform():
                for interface in instance.getInterfacesList():
                    for port in interface.getPortsList():
                        if (port.getDir() == "in") and \
                                (port.getSize() == "1") and \
                                        (port.getType()=="CLK"):
                            for pin in port.getListOfPin():
                                if len(pin.getConnections()) == 1:
                                    connection = pin.getConnections()[0]
                                    if connection["instance_dest"] == platformname:
                                        portlist.append(port)
        return portlist

    def selectPlatform(self,platformname):
        """ Select a platform for the project
        """
        #suppress platform if already exists
        try:
            self.delPlatform()
        except Error,e:
            if e.getLevel() < 2:
                raise e
            print e

        if platformname in self.listAvailablePlatforms():
            platformdir = settings.path+PLATFORMPATH+"/"+platformname+"/"
            platform = Platform(self,file=platformdir+platformname+XMLEXT)

            if sy.fileExist(platformdir+SIMULATIONPATH):
                sy.copyAllFile(platformdir+SIMULATIONPATH,
                        settings.projectpath+SIMULATIONPATH)
            self.addinstance(component=platform)
            self.addNode(node=platform)
            # Adding platform default components
            for component in platform.getComponentsList():
                self.addinstance(libraryname=component["type"],
                                  componentname=component["name"])
            # Connect slaves and clock if just one master is present
            if len(self.getInterfaceMaster()) == 1:
                interfacemaster = self.getInterfaceMaster()[0]
                # autoconnect slaves
                for interface in self.getInterfaceSlave():
                    interfacemaster.connectBus(interface.getParent(),
                                               interface.getName())
                # autoconnect syscon
                if len(self.getSysconsList()) == 1:
                    syscon = self.getInstancesList()[0]
                    syscon.getSysconInterface().connectClkDomain(
                            interfacemaster.getParent().getName(),
                            interfacemaster.getName())
        else:
            raise Error("This platform is not available",0)

    def delPlatform(self):
        """ Suppress platform from project
        """
        # find platform in components list
        try:
            platform = self.getPlatform()
        except Error:
            raise Error("No platform in project",2)
        
        self.delProjectInstance(platform.getInstanceName())
        self.delNode("platform")

    def listAvailablePlatforms(self):
        """ List all supported platforms
        """
        platformlist = sy.listDirectory(settings.path+PLATFORMPATH)
        return platformlist

    def delProjectInstance(self,instancename):
        """ Remove instance from project
        """
        instance = self.getInstance(instancename)
        #remove pins connections from project instances to this instancename
        for comp in self.getInstancesList():
            comp.deletePin(instancedest=instancename)
        #remove busses connections from project instances to this instancename
        for comp in self.getInstancesList():
            if comp.getName() != "platform":
                comp.deleteBus(instanceslavename=instancename)
        #Remove components from project
        self.instanceslist.remove(instance)
        self.reNum(instance.getName())
        self.delSubNode("components",
                        "component",
                        "name",
                        instance.getInstanceName())
        instance.delInstance()
        display.msg("Component "+instancename+" deleted")

    def saveProject(self):
        for comp in self.instanceslist:
            comp.saveInstance()
        if self.synthesis != None:
            self.synthesis.save()
        if self.simulation != None:
            self.simulation.save()
        self.saveXml(settings.projectpath + "/" + self.getName() + XMLEXT)

    def connectPin(self,portsource,pinsourcenum,portdest,pindestnum):
        """ connect pin between two instances 
        """
        #source connection
        portsource.connectPin(pinsourcenum,portdest,pindestnum)
        #destination connection
        portdest.connectPin(pindestnum,portsource,pinsourcenum)

    def deletePin(self,instancesourcename,interfacesourcename,
                        portsourcename,pinsourcenum,instancedestname,
                        interfacedestname,portdestname,pindestnum):
        """ delete pin between two instances 
        """
        source = self.getInstance(instancesourcename)
        interfacesource = source.getInterface(interfacesourcename)
        portsource = interfacesource.getPort(portsourcename)

        # test if destination given
        if (instancedestname!=None) and (interfacedestname!=None) \
            and (portdestname != None) and (pindestnum!=None):
            dest = self.getInstance(instancedestname)
            #source connection
            source.deletePin(dest,
                             interfacedestname,
                             portdestname,
                             pindestnum,
                             interfacesourcename,
                             portsourcename,
                             pinsourcenum)
            #destination connection
            dest.deletePin(source,
                           interfacesourcename,
                           portsourcename,
                           pinsourcenum,
                           interfacedestname,
                           portdestname,
                           pindestnum)
        else: # if only source given, delete all connection from this source
            if pinsourcenum != None:
                pinsource = portsource.getPin(pinsourcenum)
            elif int(portsource.getSize()) == 1: # if source num not given, 
                                                # test if port 1-sized
                    pinsourcenum = "0"
                    pinsource = portsource.getPin("0")
            else:
               raise Error,("Source pin number not given, and port size > 1",0)
            for connection in pinsource.getConnections():
                dest = self.getInstance(connection["instance_dest"])
                source.deletePin(dest,
                                 connection["interface_dest"],
                                 connection["port_dest"],
                                 connection["pin_dest"],
                                 interfacesourcename,
                                 portsourcename,
                                 pinsourcenum)
                dest.deletePin(source,
                               interfacesourcename,
                               portsourcename,
                               pinsourcenum,
                               connection["interface_dest"],
                               connection["port_dest"],
                               connection["pin_dest"])  

    def generateIntercon(self,instance_name,interface_name):
        """ generate intercon for interface interface_name """
        # test if intercon already exists
        from   periphondemand.bin.code.intercon       import Intercon
        try:
            intercon =\
                    self.getInstance(
                            instance_name+"_"+interface_name+"_intercon")
        except Error:
            pass
        else:
            print Error(instance_name+"_"+interface_name\
                    +" allready exists",INFO)
            self.delProjectInstance(intercon.getInstanceName())

        intercon = Intercon(
                self.getInstance(instance_name).getInterface(interface_name),self
                )
        self.addinstance(component=intercon)
        self.saveProject()

    def connectPort(self, 
            instance_source_name, interface_source_name, port_source_name, 
            instance_dest_name,interface_dest_name, port_dest_name):
        """ Connect all pin of a port source on all pin of 
            port dest
        """
        instance_source = self.getInstance(instance_source_name)
        interface_source = instance_source.getInterface(interface_source_name)
        port_source = interface_source.getPort(port_source_name)

        instance_dest = self.getInstance(instance_dest_name)
        interface_dest = instance_dest.getInterface(interface_dest_name)
        port_dest = interface_dest.getPort(port_dest_name)

        port_source.connectPort(port_dest)

    def connectBus(self,instancemaster,interfacemaster,instanceslave,interfaceslave):
        """ Connect a master bus to a slave bus
        """
        instance = self.getInstance(instancemaster)
        instance.connectBus(interfacemaster,
                self.getInstance(instanceslave),
                interfaceslave)

    def connectClkDomain(self,instancesourcename,instancedestname,
            interfacesourcename,interfacedestname):
        """ Connect clock domain
        """
        instancesource = self.getInstance(instancesourcename)
        # check if it's clock&rst generator
        if instancesource.getInterface(interfacesourcename).getClass() != "clk_rst":
            raise Error("Interface "+interfacesourcename+" must be 'clk_rst' ",0)

        # Check pin direction
        for port in instancesource.getInterface(interfacesourcename).getPortsList():
            if port.getDir() != "out":
                raise Error("Signals of clock generator must be 'out'",0)

        instancedest = self.getInstance(instancedestname)
        # check if iterface dest is clk&rst
        if instancedest.getInterface(interfacesourcename).getClass() != "clk_rst":
            raise Error("Interface "+\
                    instancedest.getInterface(interfacesourcename).getClass()+\
                    " must be 'clk_rst'",0)
        # clk&rst dest must be slave (pin direction 'in')
        for port in instancedest.getInterface(interfacesourcename).getPortsList():
            if port.getDir() != "in":
                raise Error("Signal "+port.getName()+" must be 'in'",0)
        # Connect
        instancesource.connectClkDomain(instancedestname,
                                        interfacesourcename,
                                        interfacedestname)

    def deleteBus(self,instancemaster,instanceslave,
                interfacemaster=None,interfaceslave=None):
        """ Delete a slave bus connection
        """
        instance = self.getInstance(instancemaster)
        instance.deleteBus(instanceslave,interfacemaster,interfaceslave)

    def reNum(self,componentname):
        """ Renum all instances in the correct order
        """
        complist = []
        for comp in self.instanceslist:
            if comp.getName() == componentname:
                complist.append(comp)
        num = 0
        for comp in complist:
            comp.setNum(num)
            num = num + 1

    def autoConnectBus(self):
        """ autoconnect bus
        """
        master = self.getInterfaceMaster()
        # autoconnection can be made only if they are 1 master interface
        if len(master) < 1:
            raise Error("No bus master in project",0)
        elif len(master) > 1:
            raise Error("More than one bus master in project, "+\
                "bus connection must be made by hand",0)
        master = master[0]

        # find slaves bus
        slaves = self.getInterfaceSlave()
        if len(slaves) == 0:
            raise Error(" No slave bus in project",0)

        # Check if only one syscon
        syscon = self.getSysconsList()
        if len(syscon) < 1:
            raise Error("No syscon in project",0)
        elif len(syscon) > 1:
            raise Error("More than one clock and reset generator, "+\
                            "bus connection must be made by hand",0)

        syscon = syscon[0]
        
        # connect each slave with the same bus name than master
        for interfaceslave in slaves:
            if interfaceslave.getBusName() == master.getBusName():
                try:
                    # connect bus
                    master.connectBus(interfaceslave.getParent(),
                                interfaceslave.getName())
                except Error,e:
                    e.setLevel(2)
                    display.msg(str(e))

        # Connect clock and reset
        self.connectClkDomain(syscon.getParent().getInstanceName(),\
                              master.getParent().getInstanceName(),\
                              syscon.getName(),\
                              master.getName())
        display.msg("Bus connected")
             
    def check(self):
        """ This function check all the project wiring
        """

        ##########################################
        # Check connections on variable ports
        for port in self.getVariablePortsList():
            if port.checkVariablePort() is False:
                raise Error("Pin connections on port "+\
                        str(port.getParent().getParent().getInstanceName())+"."+\
                        str(port.getParent().getName())+"."+\
                        str(port.getName())+\
                        "is wrong, pin number must be followed.")

        ###########################################
        #check Busses, all slaves bus need a master
        listmaster = self.getInterfaceMaster()
        listslave  = self.getInterfaceSlave()

        #Delete all slaves component from listslave 
        for master in listmaster:
            for slave in master.getSlavesList():
                for slave2 in listslave:
                    if slave2.getParent().getInstanceName()==\
                        slave.getInstanceName() and \
                            slave2.getName() == slave.getInterfaceName():
                        listslave.remove(slave2)

        for slave in listslave:
            display.msg(slave.getParent().getInstanceName()+\
                    " is not connected on a master bus",1)
        if len(listslave) != 0:
            display.msg("Some slave bus are not connected",1)

        ##########################################
        #Check bus address
        dict_reg = {}
        for master in listmaster:
            for slave in master.getSlavesList():
                for register in slave.getInterface().getRegisterMap():
                    if dict_reg.has_key(register["offset"]):
                        display.msg("Register conflict at "+hex(register["offset"])+\
                                " between "+str(slave.getInstanceName())+"."+\
                                str(register["name"])+" and "\
                                +str(dict_reg[register["offset"]][0])+"."+\
                                str(dict_reg[register["offset"]][1]),0)
                        dict_reg[register["offset"]]=(
                                str(dict_reg[register["offset"]][0])+","+\
                                slave.getInstanceName()+"/!\\",
                                str(dict_reg[register["offset"]][1])+ ","+\
                                register["name"]+"/!\\")
                    else:
                        dict_reg[register["offset"]] = (slave.getInstanceName(),
                                                        register["name"])
            display.msg("")
            display.msg("Mapping for interface " + master.getName() + ":")
            display.msg("Address  | instance.interface             | size        ")
            display.msg("---------------------------------------------------------")
            for register in master.allocMem.getMapping():
                display.msg("%8s"%register[0]+" | "+"%30s"%register[1]+\
                        " | "+"%10s"%register[2])
            display.msg("---------------------------------------------------------")

    def getSimulationToolChainList(self):
        """ list all toolchain availables
        """
        filelist = sy.listDirectory(settings.path + TOOLCHAINPATH +SIMULATIONPATH)
        return filelist

    def getSynthesisToolChainList(self):
        """ list all toolchains availables
        """
        filelist = sy.listDirectory(settings.path + TOOLCHAINPATH +SYNTHESISPATH)
        return filelist

    def getDriverToolChainList(self):
        """ list all toolchains availables
        """
        filelist = sy.listDirectory(settings.path + TOOLCHAINPATH +DRIVERSPATH)
        return filelist

    # TODO: move it in library class
    def getComponentVersionList(self,libraryname,componentname):
        """ list component version name in archive
        """
        filelist = sy.listFiles(self.library.getLibraryPath(libraryname)+\
                "/"+componentname)
        outlist = []
        for name in filelist:
            # take only xml file
            ext = XMLEXT[1:] # suppress dot
            pattern = ".*%s"%ext+"$"
            if re.match(pattern,name):                
                # Suppress extension
                name = name.split(".")[0]
                outlist.append(name)
        return outlist

    def generateReport(self,filename=None):
        """ generate a project report """
        TAB = "    "
        if filename==None:
            report_file=open(settings.projectpath+\
                    "/"+self.getName()+\
                    "_report.txt","w")
        else:
            report_file=open(filename,"w")
        text = "* Master interfaces mapping:\n"
        for master in self.getInterfaceMaster():
            masterinstance = master.getParent()
            text+="\n  "+masterinstance.getInstanceName()+"."+\
                    master.getName()+":\n"
            for slave in master.getSlavesList():
                interfaceslave = slave.getInterface()
                instance = interfaceslave.getParent()
                text+=TAB+instance.getInstanceName()+\
                        "."+interfaceslave.getName()+\
                        ":\n"
                for reg in interfaceslave.getRegisterMap():
                    text+=TAB+"  "+"0x%02x : %s\n"%(reg["offset"],
                            reg["name"])
        report_file.write(text)
        report_file.close()
        return text

