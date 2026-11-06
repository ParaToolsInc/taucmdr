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
"""Sphinx extension that writes a reference page for each ``tau`` command.

The pages are written to ``cli/`` in the documentation source directory when the build starts.
"""

import contextlib
import io
import os
import textwrap

from taucmdr import cli, logger

PAGE_WIDTH = 100
"""int: Line width of the help text on each page."""

_NO_HELP_PAGE_FMT = "No help page for '%(command)s'"
"""str: The help page :any:`AbstractCommand` gives a command that has none."""


def command_names():
    """Return the name of every command, without the script name.

    Returns:
        list: ``'__main__'``, the top-level command, followed by the subcommands in sorted order.
    """
    names = [cli.command_from_module_name(module_name).split(' ', 1)[1] for module_name in cli.get_all_commands()]
    return ['__main__'] + sorted(names)


def _page_name(name):
    return 'tau' if name == '__main__' else name.replace(' ', '_')


def _find_command(name):
    return cli.find_command([] if name == '__main__' else name.split())


@contextlib.contextmanager
def _plain_output():
    """Render help at :any:`PAGE_WIDTH`, uncolored, without TAU Commander's log messages."""
    line_width, log_level = logger.LINE_WIDTH, logger.LOG_LEVEL
    logger.LINE_WIDTH = PAGE_WIDTH
    logger.set_log_level('WARNING')
    try:
        # Help is colored only when stdout is a terminal.
        with contextlib.redirect_stdout(io.StringIO()):
            yield
    finally:
        logger.LINE_WIDTH = line_width
        logger.set_log_level(log_level)


def _code_block(text):
    return '.. code-block:: text\n\n' + textwrap.indent(text.strip('\n'), '   ') + '\n'


def command_page(name):
    """Return the reST page for a command.

    Args:
        name (str): A name from :any:`command_names`.

    Returns:
        str: The page.
    """
    command = _find_command(name)
    with _plain_output():
        summary = command.summary
        help_page = command.help_page
        usage = command.format_usage(show_defaults=False)
    title = command.command
    parts = [title, '=' * len(title), '', summary, '']
    if command.help_page_fmt != _NO_HELP_PAGE_FMT:
        parts.append(_code_block(help_page))
    parts.extend(['Usage', '-----', '', _code_block(usage)])
    return '\n'.join(parts)


def index_page(names):
    """Return the reST index page for the command reference.

    Args:
        names (list): Names from :any:`command_names`.

    Returns:
        str: The page.
    """
    entries = ''.join(f'   {_page_name(name)}\n' for name in names)
    return ('Command reference\n'
            '=================\n'
            '\n'
            'Argument defaults depend on the host. '
            'Run ``tau <command> --help`` to see the defaults on your system.\n'
            '\n'
            '.. toctree::\n'
            '   :maxdepth: 1\n'
            '\n'
            f'{entries}')


def write_pages(outdir):
    """Write the index and one page per command to `outdir`.

    A page whose content hasn't changed isn't rewritten, so Sphinx doesn't rebuild it.
    Other ``.rst`` files in `outdir` are removed.

    Args:
        outdir (str): Directory to write the pages to.

    Returns:
        list: Paths of the index and the command pages.
    """
    os.makedirs(outdir, exist_ok=True)
    names = command_names()
    pages = {'index.rst': index_page(names)}
    pages.update((_page_name(name) + '.rst', command_page(name)) for name in names)
    for filename in os.listdir(outdir):
        if filename.endswith('.rst') and filename not in pages:
            os.remove(os.path.join(outdir, filename))
    paths = []
    for filename, content in pages.items():
        path = os.path.join(outdir, filename)
        try:
            with open(path, encoding='utf-8') as fin:
                unchanged = fin.read() == content
        except FileNotFoundError:
            unchanged = False
        if not unchanged:
            with open(path, 'w', encoding='utf-8') as fout:
                fout.write(content)
        paths.append(path)
    return paths


def _builder_inited(app):
    write_pages(os.path.join(app.srcdir, 'cli'))


def setup(app):
    """Sphinx extension entry point."""
    app.connect('builder-inited', _builder_inited)
    return {'parallel_read_safe': True, 'parallel_write_safe': True}
