""" Peripheral On Demand global define
"""

import periphondemand

#global
POD_CONFIG="~/.podrc"
POD_PATH = periphondemand.__path__[0]
PLATFORMPATH = "/platforms"
BUSPATH = "/busses/"
TEMPLATESPATH = "/templates"
TOOLCHAINPATH = "/toolchains"

SIMULATIONPATH = "/simulation"
SYNTHESISPATH = "/synthesis"
DRIVERSPATH = "/drivers"

# extension
TCLEXT = ".tcl"
ARCHIVEEXT = ".zip"
XMLEXT = ".xml"
VHDLEXT = ".vhd"
UCFEXT = ".ucf"
BITSTREAMEXT = ".bit"

#for components
LIBRARYPATH = "/library"
COMPONENTSPATH = "/components"
HDLDIR = "hdl"
DRIVERS_TEMPLATES_PATH = "/drivers_templates"

# for project
BINARYPROJECTPATH = "/binaries"
OBJSPATH = "/objs"
BINARY_PREFIX = "top_"
BINARY_SUFFIX = ".bit"

# template
HEADERTPL = "/headervhdl.tpl"

# color (see VT100 console manual for more details)
COLOR_DEBUG="\033[32;7m"   # White on green

COLOR_ERROR="\033[31;7m"           # white on red
COLOR_ERROR_MESSAGE="\033[31;1m"   # red on white
COLOR_WARNING="\033[35;7m"         # white on purple 
COLOR_WARNING_MESSAGE="\033[35;1m" # purple on white 
COLOR_INFO="\033[34;7m"            # white on blue
COLOR_INFO_MESSAGE="\033[34;1m"    # blue on white
COLOR_SHELL="\033[33;3m"              # green on black
COLOR_END="\033[0m"

