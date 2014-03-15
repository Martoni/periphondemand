#!/bin/sh

# code
pep8 src/bin/code/__init__.py
pep8 src/bin/code/intercon.py
pep8 src/bin/code/topgen.py
pep8 src/bin/code/vhdl/__init__.py
#pep8 src/bin/code/vhdl/topvhdl.py

# commandeline
pep8 src/bin/commandline/__init__.py
pep8 src/bin/commandline/drivercli.py
pep8 src/bin/commandline/projectcli.py
pep8 src/bin/commandline/simulationcli.py
pep8 src/bin/commandline/synthesiscli.py

# core
pep8 src/bin/core/__init__.py
pep8 src/bin/core/project.py
pep8 src/bin/core/allocmem.py
pep8 src/bin/core/bus.py
pep8 src/bin/core/component.py
pep8 src/bin/core/driver_templates.py
pep8 src/bin/core/generic.py
pep8 src/bin/core/hdl_file.py
pep8 src/bin/core/interface.py
pep8 src/bin/core/library.py
pep8 src/bin/core/pin.py
pep8 src/bin/core/platform.py
pep8 src/bin/core/port.py
pep8 src/bin/core/register.py
pep8 src/bin/core/simulationlib.py
pep8 src/bin/core/slave.py

# toolchain
pep8 src/bin/toolchain/__init__.py
pep8 src/bin/toolchain/driver.py
pep8 src/bin/toolchain/simulation.py
pep8 src/bin/toolchain/synthesis.py
