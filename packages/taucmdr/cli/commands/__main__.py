# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
#
# Copyright (c) 2015, ParaTools, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""TAU Commander command line program entry point.

Sets up logging verbosity and launches subcommands.  Avoid doing too much work here.
Instead, process arguments in the appropriate subcommand.
"""

import os, shlex
import sys
import taucmdr
import argcomplete
from taucmdr import cli, logger, util, TAUCMDR_VERSION, TAUCMDR_SCRIPT
from taucmdr.cli import UnknownCommandError, arguments, _get_commands, get_all_commands, commands_description, COMMANDS_PACKAGE_NAME, find_command
from taucmdr.cli.command import AbstractCommand
from taucmdr.cli.commands.build import COMMAND as build_command
from taucmdr.cli.commands.trial.create import COMMAND as trial_create_command
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.model.project import Project
from taucmdr.model.application import Application
from taucmdr.model.measurement import Measurement
from taucmdr.model.experiment import Experiment
from taucmdr.model.target import Target

LOGGER = logger.get_logger(__name__)

HELP_PAGE_FMT = """'%(command)s' page to be written.

Hints:
 - All parameters can be specified partially e.g. these all do the same thing:
     taucmdr target create my_new_target --device_arch=GPU
     taucmdr targ cre my_new_target --device=GPU
     taucmdr t c my_new_target --d=GPU"""


class MainCommand(AbstractCommand):
    """Main entry point to the command line interface."""

    def __init__(self):
        summary_parts = [util.color_text("TAU Commander %s" % TAUCMDR_VERSION, 'red', attrs=['bold']),
                         util.color_text(" [ ", attrs=['bold']),
                         util.color_text(taucmdr.TAUCMDR_URL, 'cyan', attrs=['bold']),
                         util.color_text(" ]", attrs=['bold'])] 
        super(MainCommand, self).__init__(__name__, summary_fmt=''.join(summary_parts), help_page_fmt=HELP_PAGE_FMT)
        self.command = os.path.basename(TAUCMDR_SCRIPT)
    
    def _construct_parser(self):
        usage = "%s [arguments] <subcommand> [options]"  % self.command
        _green = lambda x: "{:<35}".format(util.color_text(x, 'green'))
        epilog_parts = ["", cli.commands_description(), "",
                        util.color_text("Shortcuts:", attrs=["bold"]),
                        _green("  %(command)s <compiler>") + "Execute a compiler command", 
                        "                  - Example: %(command)s gcc *.c -o a.out",
                        "                  - Alias for '%(command)s build <compiler>'",
                        _green("  %(command)s <program>") + "Gather data from a program",
                        "                  - Example: %(command)s ./a.out",
                        "                  - Alias for '%(command)s trial create <program>'",
                        _green("  %(command)s metrics") + "Show metrics available in the current experiment",
                        "                  - Alias for '%(command)s target metrics'",                       
                        _green("  %(command)s select") + "Select configuration objects to create a new experiment",
                        "                  - Alias for '%(command)s experiment create'",
                        _green("  %(command)s show") + "Show data from the most recent trial",
                        "                  - Alias for '%(command)s trial show'",
                        "",
                        "See `%(command)s help <subcommand>` for more information on a subcommand."]
        epilog = '\n'.join(epilog_parts) % {'color_command': util.color_text(self.command, 'cyan'), 
                                            'command': self.command}
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage,
                                      description=self.summary,
                                      epilog=epilog)
        
        def Write(*things, **kwargs):
            kwargs["sep"] = kwargs.get("sep", " ") # if sep is not set use ' ' as default
            kwargs["end"] = kwargs.get("end", "\n") # if sep is not set use ' ' as default
            with open('output.txt','a') as file:
                for thing in things:
                    if type(thing) != str:
                        try:
                            thing = str(thing)
                        except:
                            thing = repr(thing)
                    file.write(thing+kwargs['sep'])
                file.write(kwargs['end'])
        Write('\n'*30)

        def get_applications():
            try:
                # this will fail if tau initialize has not been run yet
                app_ctrl = Application.controller(PROJECT_STORAGE)
            except:
                Write('loading applications failed')
                return []
            applications = {a['name'] for a in app_ctrl.all()}
            Write('applications ========> ',applications,'\n')
            return applications

        def get_measurements():
            try:
                # this will fail if tau initialize has not been run yet
                app_ctrl = Measurement.controller(PROJECT_STORAGE)
            except:
                Write('loading measurements failed')
                return []
            measurements = {a['name'] for a in app_ctrl.all()}
            Write('measurements ========> ',measurements,'\n')
            return measurements
        
        def get_experiments():
            try:
                # this will fail if tau initialize has not been run yet
                exp_ctrl = Experiment.controller(PROJECT_STORAGE)
            except:
                Write('loading experiments failed')
                return []
            experiments = {a['name'] for a in exp_ctrl.all()}
            Write('experiments ========> ',experiments,'\n')
            return experiments

        def get_target():
            try:
                # this will fail if tau initialize has not been run yet
                tar_ctrl = Target.controller(PROJECT_STORAGE)
            except:
                Write('loading target failed')
                return []
            target = {a['name'] for a in tar_ctrl.all()}
            Write('target ========> ',target,'\n')
            return target

        def add_special_cases(complist, completions):
            Write('        ---- complist', complist)
            if complist[1] == 'select':
                if '--experiment' in complist:
                    completions += get_experiments()
                elif '--measurement' in complist:
                    Write('measurements in complist')
                    completions += get_measurements()
                elif '--application' in complist:
                    completions += get_applications()
                elif '--target' in complist:
                    completions += get_target()
                else:
                    if complist[-1] == 'select':
                        # tau select trace should not show applications, etc
                        completions += get_applications()
                        completions += get_measurements()
                        completions += get_experiments()
                        completions += get_target()
            if complist[1] == 'application':
                if complist[-1] in ['copy','edit','delete']:
                    completions += get_applications()

            # many more should go here
            return completions

        def add_commands(complist):
            """
            complist: list of commands entered so far

            returns a list of strings to complete with
            """
            all_cmds = [x.replace('taucmdr.cli.commands.','').split('.') for x in get_all_commands()]
            cmd_dict = {i[0]:[] for i in all_cmds if len(i) == 1} # set keys to subcommands, values to []
            all_cmds = [i for i in all_cmds if len(i) == 2] # only allow items of length 2 (items of length 1 were saved to cmd_dict)
            for i in all_cmds:
                cmd_dict[i[0]].append(i[1]) # add all the options to subcommands to cmd_dict
            
            if len(complist) == 2:
                for subcommand in cmd_dict.keys():
                    if subcommand.startswith(complist[-1]):
                        return cmd_dict[subcommand]
            elif len(complist) == 3:
                for subcommand in cmd_dict.keys():
                    if subcommand.startswith(complist[-2]):
                        return cmd_dict[subcommand]
            return []

        def my_completer(prefix, parsed_args, **kwargs):
            '''
            delegate work to other functions 
            for tau select, provide all experiments, measurements, etc
            for tau select --experiment, only provide existing experiments
            for tau select -- measurement, only provide existing measurements
            etc 
            get this working with just experiments first, then expand to all cases
            '''
            # pylint: disable=protected-access 
            subcommands = set(sorted((i[0] for i in _get_commands(COMMANDS_PACKAGE_NAME).iteritems() if i[0] != '__module__')))
            subcommands.remove('main')
            complist = shlex.split(os.environ['COMP_LINE'])
            for option in ['-v','-q','--verbose','--quiet']:
                if option in complist:
                    complist.remove(option)
                    Write('  ----- altered complist',complist)
            correct_prefix = complist[-1]
            if len(complist) == 1 and not parsed_args.command:
                Write('subcommand is not entered')
                return tuple(subcommands)
            
            if len(complist) == 2 and not parsed_args.command:
                Write('subcommand is half entered. autocomplete the one they started')
                # if it is an unambiguous command like se still autocomplete it
                return [x for x in subcommands if x.startswith(correct_prefix)]

            if parsed_args.command and len(complist) < 3:
                Write('subcommand is entered, complete the next step')
                # tau select *names of experiments*
                try:
                    found_cmd = find_command([complist[-1]])
                    Write(' ----  found_cmd:',found_cmd)
                    # get the next available commands from found_cmd
                    # pylint: disable=protected-access 
                    parser = found_cmd._construct_parser()
                except:
                    Write('\n!!!!!!COMMAND NOT FOUND'*3)
                    Write('\nreturning nothing []')
                    return []
                completions = []
                for item in parser.actions: # doesn't have normal commands like edit for tau application. Only has optional ones
                    if item.option_strings:
                        for op in item.option_strings: # it is a list that is usually one item but all commands have ['-h', '--help'] 
                            completions.append(op)
                completions += add_commands(complist)
                completions = add_special_cases(complist, completions)
                # Write(correct_prefix,'starts with experiment:','--experiment'.startswith(correct_prefix))
                return tuple(completions)

            if not parsed_args.options:
                Write('second command is not half entered. complete the one they started')
                completions = add_commands(complist)
                completions = add_special_cases(complist, completions)
                Write('  ----- returning ',completions)
                return [x for x in completions if x.startswith(correct_prefix)]
            else:
                Write('subcommand and one command after have been parsed. complete more than that')
                completions = []
                completions = add_special_cases(complist,completions)
                return completions

        parser.add_argument('command',
                            help="See subcommand descriptions below",
                            metavar='<subcommand>').completer = my_completer
        parser.add_argument('options',
                            help="Options to be passed to <subcommand>",
                            metavar='[options]',
                            nargs=arguments.REMAINDER).completer = my_completer
        parser.add_argument('-V', '--version', action='version', version=taucmdr.version_banner())
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-v', '--verbose',
                           help="show debugging messages",
                           const='DEBUG',
                           default=arguments.SUPPRESS,
                           action='store_const')
        group.add_argument('-q', '--quiet',
                           help="suppress all output except error messages",
                           const='ERROR',
                           default=arguments.SUPPRESS,
                           action='store_const')        
                
        argcomplete.autocomplete(parser)
        return parser
            
    def main(self, argv):
        """Program entry point.

        Args:
            argv (list): Command line arguments.

        Returns:
            int: Process return code: non-zero if a problem occurred, 0 otherwise
        """
        args = self._parse_args(argv)
        cmd = args.command
        cmd_args = args.options
        
        log_level = getattr(args, 'verbose', getattr(args, 'quiet', logger.LOG_LEVEL))
        logger.set_log_level(log_level)
        LOGGER.debug('Arguments: %s', args)
        LOGGER.debug('Verbosity level: %s', logger.LOG_LEVEL)

        # Try to execute as a TAU command
        try:
            return cli.execute_command([cmd], cmd_args)
        except UnknownCommandError:
            pass

        # Check shortcuts
        shortcut = None
        from taucmdr.model.project import Project
        uses_python = Project.selected().experiment().populate()['application'].get_or_default('python')
        if not uses_python and build_command.is_compatible(cmd): # should return false for python
            shortcut = ['build']
            cmd_args = [cmd] + cmd_args
        elif trial_create_command.is_compatible(cmd): # should return true for python
            shortcut = ['trial', 'create']
            cmd_args = [cmd] + cmd_args
        elif 'show'.startswith(cmd):
            shortcut = ['trial', 'show']
        elif 'metrics'.startswith(cmd):
            expr = Project.selected().experiment()
            targ_name = expr.populate('target')['name']
            shortcut = ['target', 'metrics']
            cmd_args.insert(0, targ_name)
        if shortcut:
            LOGGER.debug('Trying shortcut: %s', shortcut)
            return cli.execute_command(shortcut, cmd_args)
        else:
            LOGGER.debug('No shortcut found for %r', cmd)
     
        # Not sure what to do at this point, so advise the user and exit
        LOGGER.info("Unknown command.  Calling `%s help %s` to get advice.", TAUCMDR_SCRIPT, cmd)
        return cli.execute_command(['help'], [cmd])


COMMAND = MainCommand()

if __name__ == '__main__':
    sys.exit(COMMAND.main(sys.argv[1:]))
