#
# Copyright (c) 2026, ParaTools, Inc.
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
"""``system fetch`` subcommand."""

import datetime
import os
import shutil
from taucmdr import EXIT_FAILURE, EXIT_SUCCESS, logger, util
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.cf.software import all_sources


LOGGER = logger.get_logger(__name__)


def fetch_sources(dest, sources):
    """Download source archives into a directory, trying each archive's mirrors in order.

    A download that isn't a readable archive, such as a server's error page, counts as a failed mirror.
    The TAU nightly archive is also stored in a copy with today's date.

    Args:
        dest (str): Directory to download into.  It's created if it doesn't exist.
        sources (dict): Archive file names mapped to lists of URLs, as from :any:`all_sources`.

    Returns:
        list: Names of the archives that couldn't be downloaded from any mirror.
    """
    util.mkdirp(dest)
    failed = []
    for name, urls in sources.items():
        path = os.path.join(dest, name)
        for url in urls:
            try:
                util.download(url, path)
                util.archive_toplevel(path)
            except OSError as err:
                LOGGER.warning("Couldn't get '%s' from '%s': %s", name, url, err)
                if os.path.exists(path):
                    os.remove(path)
            else:
                LOGGER.info("Fetched '%s'", name)
                break
        else:
            failed.append(name)
    nightly = os.path.join(dest, 'tau-nightly.tgz')
    if os.path.exists(nightly):
        shutil.copy2(nightly, os.path.join(dest, datetime.datetime.now().strftime('tau-nightly-%Y-%m-%d.tgz')))
    return failed


class FetchCommand(AbstractCommand):
    """Downloads every source archive TAU Commander can use, for copying to a system without acccess to the public internet."""

    def _construct_parser(self):
        usage = "%s <directory>" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('directory', help="Directory to download into", metavar='<directory>')
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        dest = os.path.abspath(args.directory)
        sources = all_sources()
        failed = fetch_sources(dest, sources)
        if failed:
            self.logger.error("Couldn't download %d of %d source archives: %s", len(failed), len(sources),
                              ', '.join(failed))
            return EXIT_FAILURE
        self.logger.info("Downloaded %d source archives to '%s'", len(sources), dest)
        return EXIT_SUCCESS


COMMAND = FetchCommand(__name__, summary_fmt="Download source packages for installing without internet access.")
