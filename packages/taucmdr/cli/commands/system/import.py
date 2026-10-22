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
"""``system import`` subcommand."""

# Watch out! "import" is a Python keyword, so this can't just be named after its command
# since `import import` doesn't work.

import fnmatch
import hashlib
import os
import shutil
from taucmdr import EXIT_SUCCESS, logger, util
from taucmdr.error import ConfigurationError
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.cf.software import all_sources
from taucmdr.cf.software.tau_installation import complete_nightly_names
from taucmdr.cf.storage.levels import require_system_storage


LOGGER = logger.get_logger(__name__)


def _same_file(path1, path2):
    if os.path.getsize(path1) != os.path.getsize(path2):
        return False
    digests = []
    for path in path1, path2:
        digest = hashlib.sha256()
        with open(path, 'rb') as fin:
            for block in iter(lambda fin=fin: fin.read(1 << 20), b''):
                digest.update(block)
        digests.append(digest.digest())
    return digests[0] == digests[1]


def import_sources(bundle, src_dir):
    """Copy the source archives in a directory into a storage level's source archive directory.

    Only files named like an archive TAU Commander downloads are copied.  A file already in `src_dir`
    under the same name is never replaced.  Afterwards the TAU nightly archive is present under both of
    the names searched by TAU installations (see :any:`complete_nightly_names`).

    Args:
        bundle (str): Directory holding the archives; made by ``tau system fetch``.
        src_dir (str): The storage level's source archive directory.  It is created if it doesn't already exist.

    Returns:
        list: Names of the files added to `src_dir`.

    Raises:
        ConfigurationError: `bundle` isn't a directory, or an archive can't be read.  Nothing has been copied.
    """
    if not os.path.isdir(bundle):
        raise ConfigurationError(f"'{bundle}' isn't a directory.")
    known = set(all_sources())
    archives = []
    for name in sorted(os.listdir(bundle)):
        path = os.path.join(bundle, name)
        if not os.path.isfile(path):
            continue
        if name not in known and not fnmatch.fnmatch(name, 'tau-nightly-*.tgz'):
            LOGGER.warning("Skipped '%s', which isn't a source package TAU Commander uses.", path)
            continue
        try:
            util.archive_toplevel(path)
        except OSError as err:
            raise ConfigurationError(f"'{path}' isn't a readable archive: {err}",
                                     "Copy it again, or download it again with `tau system fetch`.") from err
        archives.append(name)
    util.mkdirp(src_dir)
    added = []
    for name in archives:
        source, target = os.path.join(bundle, name), os.path.join(src_dir, name)
        if os.path.exists(target):
            if _same_file(source, target):
                LOGGER.info("'%s' is already in '%s'", name, src_dir)
            else:
                LOGGER.warning("Kept the existing '%s', which differs from '%s'.", target, source)
            continue
        shutil.copy2(source, target)
        LOGGER.info("Imported '%s'", name)
        added.append(name)
    return added + complete_nightly_names(src_dir)


class ImportCommand(AbstractCommand):
    """Copies source archives into system-level storage."""

    def _construct_parser(self):
        usage = "%s <directory>" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('directory', help="Directory of source packages, e.g. from `tau system fetch`",
                            metavar='<directory>')
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        storage = require_system_storage()
        storage.connect_filesystem()
        src_dir = os.path.join(storage.prefix, 'src')
        added = import_sources(os.path.abspath(args.directory), src_dir)
        self.logger.info("Added %d files to '%s'", len(added), src_dir)
        return EXIT_SUCCESS


COMMAND = ImportCommand(__name__, summary_fmt="Add source packages to system-level storage.")
