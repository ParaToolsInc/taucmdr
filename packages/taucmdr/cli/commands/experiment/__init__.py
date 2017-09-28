# -*- coding: utf-8 -*-
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
"""``experiment`` subcommand."""

from taucmdr.cli.cli_view import RootCommand
from taucmdr.model.experiment import Experiment

HELP_PAGE = """
TAU Commander Experiments:
An experiment is defined by: a target, an application, a measurement. Create 
experiments by entering: 
 
tau select <profile_name> <target_name> <measurement_name> 
 
If the target, application, or measurement name can be implied then it may be 
omitted.  For example, if you have only one target and only one application in 
your project then only the measurement name must be specified: 
 
tau select my_profile 
 
The select command will name the new experiment based on the names of the 
selected objects.  You may rename the new experiment with the tau experiment 
edit command, or take full control of experiment creation by explicitly 
specifying each parameter: 
 
tau experiment create <experiment_name> --application <application_name> 
--measurement <measurement_name> --target <target_name>    The entities 
experiment, application and measurement must already be defined.
"""

COMMAND = RootCommand(Experiment, __name__, group="configuration", help_page_fmt=HELP_PAGE)
