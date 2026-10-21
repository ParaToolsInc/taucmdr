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
"""TAU Commander's entry point, run by the ``tau`` launcher as ``python -I -m taucmdr``."""

# Without `-I`, Python has already imported `taucmdr/__init__.py` and `importlib.metadata`, both standard library only.
# Keep it that way: modules shadowing third-party packages on `PYTHONPATH` must not run before the re-exec.
import os
import sys
from contextlib import contextmanager


@contextmanager
def _profiler():
    """Profile TAU Commander if ``__TAUCMDR_PROFILE_TAUCMDR__`` is ``stdout`` or a file name."""
    profile_taucmdr = os.environ.get('__TAUCMDR_PROFILE_TAUCMDR__')
    if not profile_taucmdr:
        yield
    else:
        from cProfile import Profile  # pylint: disable=import-outside-toplevel
        prof = Profile()
        prof.enable()
        try:
            yield
        finally:
            prof.disable()
            if profile_taucmdr == "stdout":
                prof.print_stats(sort="tottime")
            else:
                prof.dump_stats(profile_taucmdr)
                print("Profile written to '%s'" % profile_taucmdr)
                print("Hint: Use `pyprof2calltree -k -i '%s'` to view it" % profile_taucmdr)


def main():
    """Run the ``tau`` command line, first restarting Python in isolated mode if it isn't already."""
    if not sys.flags.isolated:
        launcher = os.path.join(os.path.dirname(sys.executable), 'tau')
        os.environ.setdefault('__TAUCMDR_SCRIPT__', launcher if os.path.isfile(launcher) else 'tau')
        os.execv(sys.executable, [sys.executable, '-I', '-m', 'taucmdr', *sys.argv[1:]])
    with _profiler():
        from taucmdr.cli.commands.__main__ import COMMAND  # pylint: disable=import-outside-toplevel
        sys.exit(COMMAND.main(sys.argv[1:]))


if __name__ == '__main__':
    main()
