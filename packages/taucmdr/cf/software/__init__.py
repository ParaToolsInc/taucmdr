#
# Copyright (c) 2015-2026, ParaTools, Inc.
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
"""Software management common objects."""

import importlib
import os
import pkgutil
from taucmdr import util
from taucmdr.error import ConfigurationError


class SoftwarePackageError(ConfigurationError):
    """Indicates there was an error in an external software package."""

    message_fmt = ("%(value)s\n"
                   "\n"
                   "%(hints)s\n"
                   "Please check the selected experiment or send '%(logfile)s' to %(contact)s for assistance.")

def get_installation(name):
    module_name = name + '_installation'
    cls_name = util.camelcase(module_name)
    pkg = __import__(__name__+'.'+module_name, globals(), locals(), [cls_name])
    return getattr(pkg, cls_name)


def _repos_urls(repos):
    """Yield every URL in a ``REPOS`` dictionary whose values are URL lists or dictionaries of them."""
    for value in repos.values():
        if isinstance(value, dict):
            yield from _repos_urls(value)
        else:
            yield from value


def all_sources():
    """Return every source archive that a software package installation can download for every platform.

    Returns:
        dict: Archive file names mapped to lists of their URLs, in the order mirrors are tried.
    """
    # Imported here to avoid circular dependency, as the installation modules import this package.
    from taucmdr.cf.software import ompt_installation, tau_installation  # pylint: disable=import-outside-toplevel
    url_lists = [ompt_installation.TR6_REPOS, ompt_installation.TR4_REPOS, [tau_installation.NIGHTLY]]
    for info in pkgutil.iter_modules(__path__):
        if info.name.endswith('_installation'):
            module = importlib.import_module(f'{__name__}.{info.name}')
            url_lists.append(list(_repos_urls(getattr(module, 'REPOS', None) or {})))
    sources = {}
    for urls in url_lists:
        for url in urls:
            mirrors = sources.setdefault(os.path.basename(url), [])
            if url not in mirrors:
                mirrors.append(url)
    return sources
