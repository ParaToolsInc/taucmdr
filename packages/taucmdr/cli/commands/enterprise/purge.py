# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, ParaTools, Inc.
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
"""``enterprise purge`` subcommand."""

from taucmdr import EXIT_SUCCESS, ENTERPRISE_URL, logger
from taucmdr.cf.storage.levels import ENTERPRISE_STORAGE
from taucmdr.cli import arguments
from taucmdr.model.project import Project
from taucmdr.cli.command import AbstractCommand

LOGGER = logger.get_logger(__name__)

class EnterprisePurgeCommand(AbstractCommand):
    """``enterprise purge`` subcommand."""

    def _construct_parser(self):
        usage = "%s --force" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        mode_dest = 'mode'
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument('-f', '--force',
                                help="force changes to be pushed even if existing remote objects change",
                                const='force', action='store_const', dest=mode_dest,
                                default=arguments.SUPPRESS)
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        mode = getattr(args, 'mode', None) or 'none'
        if mode != 'force':
            self.parser.error("Specify --force to purge tables.")
        else:
            token, db_name = Project.connected()
            ENTERPRISE_STORAGE.connect_database(url=ENTERPRISE_URL, db_name=db_name, token=token)
            ENTERPRISE_STORAGE.purge_all_tables()
            LOGGER.info("Tables in %s purged." % db_name)
        return EXIT_SUCCESS


COMMAND = EnterprisePurgeCommand(__name__,
                                      summary_fmt="Delete every record in every table in the remote database.")
