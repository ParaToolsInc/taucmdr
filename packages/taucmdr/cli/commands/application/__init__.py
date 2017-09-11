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
"""``application`` subcommand."""

from taucmdr.cli.cli_view import RootCommand
from taucmdr.model.application import Application


HELP_PAGE = """
TAU Commander Applications:

Creating new applications:
Enter:  tau application create <new_application_name>

Copying a TAU Commander Application:
Enter: tau application copy <existing_application_name> <new_application_name>
The new application has the same properties as the original existing application.

Editing a TAU Commander Application:
Enter: tau application edit <application_name> --<application_property> <property setting>
The following properties are set to True/False (T/F):
    cuda, mpc, mpi, opencl, openmp, pthreads, shmem, tbb
    e.g. tau application edit <application_name> --mpi T
The property linkage is set to static/dynamic (default is dynamic) this is changed by:
    tau application edit <application_name> --linkage static

The application name can be changed with –new-name as shown below:
tau application edit <application_name> <new_application_name>

A selective instrumentation file may be specified with --select-file and its path.
e.g. tau application edit <application_name> --select_file <path>

Delete a TAU Commander Application:
Enter: tau application delete <application_name>

List TAU Commander Applications in a project:
Enter: tau application list
tau application list –l (long description)
tau application list –s (short description)
"""


COMMAND = RootCommand(Application, __name__, group="configuration", help_page_fmt=HELP_PAGE)
