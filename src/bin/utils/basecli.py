#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     cli.py
# Purpose:  Basic Command Line Interface for Orchestra elements
#
# Author:   Fabrice MOUSSET and Fabien Marteau
#
# Created:  2008/01/17
# Licence:  GPLv3 or newer
# pylint: disable=W0613
# ----------------------------------------------------------------------------
"""Basic Command Line Interface"""

import cmd
import re
import os
import sys
import readline

from periphondemand.bin.define import PODSCRIPTEXT
from periphondemand.bin.define import BASE_PROMPT

from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils import wrappersystem as sy

SETTINGS = Settings()


class BaseCli(cmd.Cmd):
    """ Command line management """
    case_insensitive = True
    comment_marks = '#*'
    exclude_from_history = ['EOF', 'source', 'savehistory']
    multiline_commands = []
    shortcuts = {'?': 'help', '!': 'shell'}
    terminators = ';\n'
    default_extension = 'txt'
    old_completer = None

    def __init__(self, parent=None, project=None, *args, **kwargs):
        cmd.Cmd.__init__(self, *args, **kwargs)
        self.parent = parent
        SETTINGS.history = SETTINGS.history[:-1]
        self._project = project

        if parent is None:
            self.setPrompt(BASE_PROMPT)
        else:
            self.stdin = parent.stdin
            self.stdout = parent.stdout
            self.use_rawinput = parent.use_rawinput

        self.base_prompt = BASE_PROMPT
        self.continuation_prompt = ""
        self._locals = {}
        self._globals = {}

    def finishStatement(self, firstline):
        """ finish the statement """
        statement = firstline
        while not self.statementHasEnded(statement):
            inp = self.pseudo_input(self.continuation_prompt)
            statement = '%s\n%s' % (statement, inp)
        return statement
        # assembling a list of lines and joining them at the end would be
        # faster,
        # but statementHasEnded needs a string arg; anyway, we're getting
        # user input and users are slow.

    def write(self, message):
        """ Write a message """
        self.stdout.write(message)

    def readline(self):
        """ Read a line """
        return self.stdin.readline()

    def pseudo_input(self, prompt):
        """ copied from cmd's cmdloop; like input,
            but accounts for changed stdin, stdout
        """

        if self.use_rawinput:
            try:
                line = input(prompt)
            except EOFError:
                line = 'EOF'
        else:
            self.stdout.write(prompt)
            self.stdout.flush()
            line = self.stdin.readline()
            if not len(line):
                line = 'EOF'
            else:
                if line[-1] == '\n':  # this was always true in Cmd
                    line = line[:-1]
        return line

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """

        # An almost perfect copy from Cmd; however,
        # the pseudo_input portion
        # has been split out so that it can be called separately

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey + ": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro) + "\n")
            stop = None
            while not stop:
                try:
                    if self.cmdqueue:
                        line = self.cmdqueue.pop(0)
                    else:
                        line = self.pseudo_input(self.prompt)
                    line = self.precmd(line)
                    if line == "exit":
                        sys.exit(0)
                    if SETTINGS.is_script():
                        print("$ " + line)
                    stop = self.onecmd(line)
                    stop = self.postcmd(stop, line)
                except KeyboardInterrupt:
                    print(PodError("User keyboard interrupt"))
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass

    statement_end_pattern = re.compile(r'[%s]\s*$' % terminators)

    def statementHasEnded(self, lines):
        """ statement has ended """
        return bool(self.statement_end_pattern.search(lines)) or\
            lines[-3:] == 'EOF'

    def clean(self, astring):
        """cleans up a string"""
        if self.case_insensitive:
            return astring.strip().lower()
        return astring.strip()

    def parseline(self, line):
        """Parse the line into a command name and a string containing
        the arguments.  Returns a tuple containing (command, args, line).
        'command' and 'args' may be None if the line couldn't be parsed.
        """
        line = line.strip()
        if not line:
            return None, None, line
        shortcut = self.shortcuts.get(line[0])
        if shortcut and hasattr(self, 'do_%s' % shortcut):
            line = '%s %s' % (shortcut, line[1:])
        i, number = 0, len(line)
        while i < number and line[i] in self.identchars:
            i = i + 1
        command, arg = line[:i], line[i:].strip().strip(self.terminators)
        return command, arg, line

    def onecmd(self, line):
        """Interpret the argument as though it had been typed in response
        to the prompt.

        This may be overridden, but should not normally need to be;
        see the precmd() and postcmd() methods for useful execution hooks.
        The return value is a flag indicating whether interpretation of
        commands by the interpreter should stop.
        """
        try:
            (command, args) = line.split(None, 1)
        except ValueError:
            (command, args) = line, ''

        try:
            (sub_cmd, end_cmd) = command.split('.', 1)
            command = sub_cmd
            args = ' '.join([end_cmd, args])
        except ValueError:
            pass

        if self.case_insensitive:
            command = command.lower()
        statement = ' '.join([command, args])
        if command in self.multiline_commands:
            statement = self.finishStatement(statement)
        return cmd.Cmd.onecmd(self, statement)

    # Override methods in Cmd object #
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion,
           Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)  # sets up command completion
        self._locals = {}  # Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentation,
           Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)  # Clean up command completion
        # print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted.
        """
        # SETTINGS.addHistory(line)
        # Remove comments lines and void line
        try:
            if str(line)[0] in str(self.comment_marks):
                return ""
        except IndexError:
            return ""

        if line:
            SETTINGS.history.append(self.base_prompt + "." + line.strip())
        return line

    def default(self, line):
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """

        print("*** Unknown Syntax : %s" % line +
              "\n(type help for a list of valid command)\n")

    def do_shell(self, arg):
        """Pass command to a system shell when line begins with '!'."""
        os.system(arg)

    def emptyline(self):
        """Do nothing on empty line."""
        pass

    def do_quit(self, arg):
        """Exits from the command line interpreter.\n"""
        return True

    do_exit = do_quit

    def do_EOF(self, args):
        """Exit on system end of file character.\n"""
        return self.do_exit(args)

    do_eof = do_EOF

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of
            commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        # The only reason to define this method is
        # for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    # Property to manage active projet
    def setPrompt(self, prompt, name=None):
        """Update command line prompt and continuation prompt."""
        prompt = str(prompt).strip()
        if self.parent is None:
            self.base_prompt = prompt
        else:
            self.base_prompt = self.parent.base_prompt + "." + prompt
        if name is not None:
            self.prompt = self.base_prompt + ":" + name + "> "
        else:
            self.prompt = self.base_prompt + "> "
        self.continuation_prompt = " " * len(self.base_prompt) + "> "

    def completelist(self, line, text, alist):
        """ Complete list """
        completion = [a for a in alist if a.startswith(text)]
        return completion

    def completeargs(self, text, line, template):
        """ complete using template
        """
        # splitting lines
        argline = line.split(" ")[1:]
        argtemplate = template.split(" ")
        # last line argument
        argl = argline[-1]
        argt = argtemplate[argline.index(argl)]
        # splitting subargs
        subargline = argl.split('.')
        subargtemplate = argt.split('.')
        #
        listargs = []
        for subargl, subargt, i in zip(subargline,
                                       subargtemplate,
                                       range(len(subargline))):
            thematching = re.match(r'^[\[|\<](.*?)[\]|\>]$', subargt)
            subargt = thematching.group(1)
            if i < len(subargline) - 1:
                listargs.append([subargt, subargl])
            else:
                return self.completelist(line, text,
                                         self.listcompletion(listargs,
                                                             subargl, subargt))

    def listcompletion(self, listargs, subargl, subargt):
        """ return a list of possibility using template:
[] optional argument
<> mandatory arguments
masterinstancename : give list of instances with master bus interface
slaveinstancename  : give list of instances with slave  bus interface
libraryname        : give list of available libraries
componentname      : give list of components available in library
                     (for projectcli)
componentversion   : give list of components version available in component
genericname        : give list of generic instance name
platformlib        : give list of platform library available
platformname       : give list of platform available
instancename       : give list of instances in project
interfacename      : give list of interface in instance
portname           : give list of port in interface
pinnum             : give list of num for a port
simulationtoolchain: give list of toolchain available for simulation
drivertoolchain    : give list of toolchain available for driver
synthesistoolchain : give list of toolchain available for synthesis
forcename          : give list of pin where value can be forced
IO_name            : give list of platform IO pin name
fpga_attributes    : give list of fpga attributes in platform
        """
        # read listargs (come from template)
        if len(listargs) > 0:
            if listargs[0][0] == "masterinstancename" or\
               listargs[0][0] == "slaveinstancename" or\
               listargs[0][0] == "instancename":
                instance = self._project.get_instance(listargs[0][1])
                instancename = instance.instancename
            elif listargs[0][0] == "platformlib":
                platformlib = listargs[0][1]
            elif listargs[0][0] == "libraryname":
                libraryname = listargs[0][1]
            elif listargs[0][0] == "componentname":
                componentname = listargs[0][1]
            else:
                return []
        if len(listargs) > 1:
            if listargs[1][0] == "interfacename":
                interface = instance.get_interface(listargs[1][1])
                interfacename = interface.name
            elif listargs[1][0] == "componentname":
                componentname = listargs[1][1]
            else:
                return []
        if len(listargs) > 2:
            if listargs[2][0] == "portname":
                port = interface = interface.get_port(listargs[2][1])
                portname = port.name
            else:
                return []
        # fill list
        if subargt == "masterinstancename":
            return [interface.parent.instancename
                    for interface in
                    self._project.interfaces_master]
        elif subargt == "slaveinstancename":
            return [interface.parent.instancename
                    for interface in
                    self._project.interfaces_slave]
        elif subargt == "instancename":
            return [instance.instancename
                    for instance in self._project.instances]
        elif subargt == "interfacename":
            return ["" + instancename + "." + interface.name
                    for interface in instance.interfaces]
        elif subargt == "masterinterfacename":
            return ["" + instancename + "." + interface.name
                    for interface in instance.master_interfaces]
        elif subargt == "slaveinterfacename":
            return ["" + instancename + "." + interface.name
                    for interface in instance.slave_interfaces]
        elif subargt == "portname":
            return ["" + instancename + "." + interfacename + "." +
                    port.name for port in interface.ports]
        elif subargt == "pinnum":
            return ["" + instancename + "." + interfacename +
                    "." + portname + "." + str(i)
                    for i in range(int(port.size))]
        elif subargt == "libraryname":
            arglist = self._project.library.libraries
            return arglist

        elif subargt == "platformlib":
            arglist = SETTINGS.personal_platformlib_name_list
            arglist.append("standard")
            return arglist
        elif subargt == "forcename":
            arglist = ["" + port.name
                       for port in
                       self._project.platform.platform_ports]
            return arglist
        elif subargt == "forcestate":
            return ["gnd", "vcc", "undef"]
        elif subargt == "componentname":
            try:
                libraryname.lower()
            except Exception as error:
                raise error
            arglist = [libraryname + "." + componentname
                       for componentname in
                       self._project.library.list_components(
                           libraryname)]
            return arglist
        elif subargt == "componentversion":
            try:
                libraryname.lower()
            except Exception as error:
                raise error
            return [libraryname + "." + componentname + "." + comp
                    for comp in
                    self._project.get_components_versions(
                        libraryname, componentname)]

        elif subargt == "platformname":
            if platformlib == "standard":
                return ["standard." + name
                        for name in
                        self._project.availables_plat()]
            else:
                return [platformlib + "." + name
                        for name in
                        sy.list_files(
                            SETTINGS.get_platform_lib_path(platformlib))]

        elif subargt == "genericname":
            return ["" + instancename + "." + generic.name
                    for generic in instance.generics]

        elif subargt == "simulationtoolchain":
            return self._project.get_simulation_toolchains()

        elif subargt == "synthesistoolchain":
            return self._project.get_synthesis_toolchains()
        elif subargt == "drivertoolchain":
            return self._project.get_driver_toolchains()
        elif subargt == "IO_name":
            return [port.name for port in
                    self._project.get_ios()]
        elif subargt == "fpga_attributes":
            platform = self._project.platform
            return platform.get_attr_names("fpga")
        else:
            return []

    def checkargs(self, line, template):
        """ check line with template
        """
        argline = line.split(" ")
        argtemplate = template.split(" ")
        try:
            argline.remove('')
        except ValueError:
            pass
        if len(argline) < self.minArgNumber(template, ' ') or \
           len(argline) > self.maxArgNumber(template, ' '):
            raise PodError(
                "Wrong argument number:\n%s\n instead of\n %s" % (line,
                                                                  template), 0)

        for argl, argt in zip(argline, argtemplate):
            if re.match(r"^\.\.", argl):
                subargline = argl[2:].split(".")
                subargline[0] = ".." + subargline[0]
            elif re.match(r"^\.", argl):
                subargline = argl[1:].split(".")
                subargline[0] = "." + subargline[0]
            else:
                subargline = argl.split(".")
            if (len(subargline) < self.minArgNumber(argt, '.')) or\
                    (len(subargline) > self.maxArgNumber(argt, '.')):
                raise PodError(
                    "Wrong subargument:\n%s\ninstead of\n%s" % (argl,
                                                                argt), 0)

    def minArgNumber(self, template, separator):
        """ return the minimun argument number
        """
        argnumber = 0
        args = template.split(separator)
        for arg in args:
            if re.match(r'^\<', arg):
                argnumber = argnumber + 1
        return argnumber

    def maxArgNumber(self, template, separator):
        """ return the maximum argument number
        """
        args = template.split(separator)
        return len(args)

    def isPlatformSelected(self):
        """ check if platform is selected, if not raise error """
        self._project.platform

    def do_history(self, args):
        """ history
        print command history
        """
        for line in SETTINGS.history:
            print(line)

    def do_savehistory(self, line):
        """ savehistory <filename>
        save history command
        """
        try:
            self.checkargs(line, "<filename>")
        except PodError as error:
            print(str(error))
            return
        # Create the file
        filename = line.split(" ")[-1]
        filename = filename + PODSCRIPTEXT
        try:
            historyfile = open(filename, "w")
        except IOError as error:
            print(str(error))
            return
        # suppress the last command (its savehistory itself)
        SETTINGS.history = SETTINGS.history[:-1]
        for line in SETTINGS.history:
            # do not write source or EOF command
            if not (re.match(r'.*\.source', line) or re.match(r'.*EOF', line)):
                # suppress POD root
                wline = ".".join(line.split('.')[1:])
                # suppress the project name
                regexp = re.compile(r'(.*)\:(.*?)(\..*)')
                wline = regexp.sub(r'\1\3', wline)
                historyfile.write(wline + "\n")
        print("History wrote")

    def do_ls(self, line):
        """ ls
list files and directory in the current directory
        """
        sy.shell_ls(line)


class Statekeeper(object):
    """ save and restore state """

    def __init__(self, obj, attribs):
        self.obj = obj
        self.attrib_names = attribs
        self.attribs = {}
        self.save()

    def save(self):
        """ save state """
        for attrib in self.attrib_names:
            self.attribs[attrib] = getattr(self.obj, attrib)

    def restore(self):
        """ restore state """
        for attrib in self.attrib_names:
            setattr(self.obj, attrib, self.attribs[attrib])
