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
"""``measurement`` subcommand."""

from taucmdr.cli.cli_view import RootCommand
from taucmdr.model.measurement import Measurement

HELP_PAGE = """
TAU Commander Measurements:
=============================================================================
Create a new measurement- enter: 
`tau measurement create <profile_name> --profile` or            
`tau measurement create <profile_name> --trace` 
 
Edit TAU Commander Measurements. The following measurement data arguments 
may be edited `--callpath [depth]` and `--metrics [PAPI metrics]` 
e.g. `tau measurement edit <measurement_name> --callpath 3` 
 
The following measurement instrumentation settings may be defined with commands: 
`--compiler-inst [mode]`   (valid  modes are: `always, fallback, never` ) 
`--source-inst [mode]` (valid modes are: `automatic, manual, never` ) 
 
The default is sampling, where TAU Commander will use the symbols in the binary 
when built with -g to decipher code information.  Source instrumentation 
relies on the Program Database Toolkit (PDT) to add information to track and 
the last is utilization of the compiler to instrument the source code.   
There are several TAU commands that can explicitly be added to the code which 
is beyond the scope of this introductory manual.  Those interested can find 
more information in the TAU User Guide 
(https://www.cs.uoregon.edu/research/tau/docs/newguide/index.html). 
 
The following measurement instrumentation arguments can be set to True or False 
(T/F) `--keep-inst-files --reuse-inst-files --sample` 
 
The following measurement arguments are set to True or False `--callsite 
--comm-matrix --cuda --io --metadata-merge --mpi --opencl --shmem --throttle 
The following measurement arguments may be set; --throttle-num-calls [count] 
--throttle-per-calls [us] (us=microseconds)` 
 
The following memory and output formats are set to True or False (T/F) 
`--heap-usage --memory-alloc --profile --trace`
 A measurement can be renamed with: 
`Tau measurement --new-name <measurement_name> <new_measurement_name>` 
A measurement can be deleted with: `tau measurement --delete <measurement_name>`
Measurements are listed with: `tau measurement list` (optional `--l` or `--s` 
(long or short descriptions)).

_____________________________________________________________________________
"""


COMMAND = RootCommand(Measurement, __name__, group="configuration", help_page_fmt=HELP_PAGE)
