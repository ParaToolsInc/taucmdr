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
"""``taucmdr trial`` subcommand."""

from taucmdr.cli.cli_view import RootCommand
from taucmdr.model.trial import Trial

HELP_PAGE="""
TAU Commander trials 

A trial is created by running the binary: tau trial create ./a.out <args> 
more commonly though it is simply created by using the tau prefix and execution
command - that is: tau ./a.out or tau mpirun -np # ./a.out <args> The binary 
a.out will be executed and the TAU Commander specified data will be collected.  
This completes data collection to form a trial. 
 
Delete a trial: tau trial delete <trial_number> 
 
Edit a trial: tau trial edit <trial_number> --description <free form text> 
 
Export a trial: tau trial export <trial_number> [optional arg] 
Optional argument is:  --destination <path> 
 
Viewing data for a trial: Enter tau trial show or tau show and TAU Commander 
will open up the appropriate display window to graphically show the data of 
the trial.  This will be the last trial collected with the active or selected 
experiment.  To see data for a different trial for this experiment just enter 
the trial number after show (e.g. tau trial show 0).  Please note that trial 
numbers begin with 0.  The first trial is trial number 0.   If tau dashboard 
shows 3 trials those 3 trials are numbered 0, 1, 2 
 
Alternatively, you may enter: tau show <trial #> This will have the same affect 
as: tau trial show 0 
 
You may also specify files instead of trial numbers, in this case enter: 
tau show <data_file> or Tau trial show <data_file> 
 
Optional arguments for Tau trial command are shown above before this help section.
 
"""

COMMAND = RootCommand(Trial, __name__, group="configuration",
                      summary_fmt="Create and manage experiment trials.", help_page_fmt=HELP_PAGE)
