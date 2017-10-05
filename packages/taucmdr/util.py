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
"""Utility functions.

Handles system manipulation and status tasks, e.g. subprocess management or file creation.
"""

import re
import os
import sys
import time
import atexit
import subprocess
import errno
import shutil
import urllib
import pkgutil
import tarfile
import gzip
import tempfile
import urlparse
import hashlib
from collections import deque
from contextlib import contextmanager
from zipimport import zipimporter
from zipfile import ZipFile
from termcolor import termcolor
from unidecode import unidecode
from taucmdr import logger
from taucmdr.error import InternalError
from taucmdr.progress import ProgressIndicator, progress_spinner


LOGGER = logger.get_logger(__name__)


_PY_SUFFEXES = ('.py', '.pyo', '.pyc')

_DTEMP_STACK = []

_DTEMP_ERROR_STACK = []

# Don't make this a raw string!  \033 is unicode for '\x1b'.
_COLOR_CONTROL_RE = re.compile('\033\\[([0-9]|3[0-8]|4[0-8])m')


def _cleanup_dtemp():
    if _DTEMP_STACK:
        for path in _DTEMP_STACK:
            if not any(path in paths for paths in _DTEMP_ERROR_STACK):
                rmtree(path, ignore_errors=True)
    if _DTEMP_ERROR_STACK:
        LOGGER.warning('The following temporary directories were not deleted due to build errors: %s.\n',
                       ', '.join(_DTEMP_ERROR_STACK))
atexit.register(_cleanup_dtemp)


def calculate_uid(parts):
    """Create a new unique identifier.

    Args:
        parts (list): **Ordered** list of strings to include in the UID calcuation.

    Returns:
        str: A string of hexidecimal digits uniquely calculated from `parts`.
    """
    uid = hashlib.sha1()
    for part in parts:
        uid.update(part)
    digest = uid.hexdigest()
    LOGGER.debug("UID: (%s): %s", digest, parts)
    return digest[:8]

def mkdtemp(*args, **kwargs):
    """Like tempfile.mkdtemp but directory will be recursively deleted when program exits."""
    path = tempfile.mkdtemp(*args, **kwargs)
    _DTEMP_STACK.append(path)
    return path


def copy_file(src, dest, show_progress=True):
    """Works just like :any:`shutil.copy` except with progress bars."""
    context = progress_spinner if show_progress else _null_context
    with context():
        shutil.copy(src, dest)


def mkdirp(*args):
    """Creates a directory and all its parents.
    
    Works just like ``mkdir -p``.
    
    Args:
        *args: Paths to create.
    """
    for path in args:
        # Avoid errno.EACCES if a parent directory is not writable and the directory exists
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
                LOGGER.debug("Created directory '%s'", path)
            except OSError as exc:
                # Only raise if another process didn't already create the directory
                if not (exc.errno == errno.EEXIST and os.path.isdir(path)):
                    raise

def add_error_stack(path):
    _DTEMP_ERROR_STACK.append(path)

def rmtree(path, ignore_errors=False, onerror=None, attempts=5):
    """Wrapper around shutil.rmtree to work around stale or slow NFS directories.

    Tries repeatedly to recursively remove `path` and sleeps between attempts.

    Args:
        path (str): A directory but not a symbolic link to a directory.
        ignore_errors (bool): If True then errors resulting from failed removals will be ignored.
                              If False or omitted, such errors are handled by calling a handler 
                              specified by `onerror` or, if that is omitted, they raise an exception.
        onerror: Callable that accepts three parameters: function, path, and excinfo.  See :any:shutil.rmtree.
        attempts (int): Number of times to repeat shutil.rmtree before giving up.
    """
    if not os.path.exists(path):
        return
    for i in xrange(attempts-1):
        try:
            return shutil.rmtree(path)
        except Exception as err:        # pylint: disable=broad-except
            LOGGER.warning("Unexpected error: %s", err)
            time.sleep(i+1)
    shutil.rmtree(path, ignore_errors, onerror)


@contextmanager
def umask(new_mask):
    """Context manager to temporarily set the process umask.
    
    Args:
        new_mask: The argument to :any:`os.umask`.
    """ 
    old_mask = os.umask(new_mask)
    yield
    os.umask(old_mask)


_WHICH_CACHE = {}
def which(program, use_cached=True):
    """Returns the full path to a program command.
    
    Program must exist and be executable.
    Searches the system PATH and the current directory.
    Caches the result.
    
    Args:
        program (str): program to find.
        use_cached (bool): If False then don't use cached results.
        
    Returns:
        str: Full path to program or None if program can't be found.
    """
    if not program:
        return None
    assert isinstance(program, basestring)
    if use_cached:
        try:
            return _WHICH_CACHE[program]
        except KeyError:
            pass
    _is_exec = lambda fpath: os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, _ = os.path.split(program)
    if fpath:
        abs_program = os.path.abspath(program)
        if _is_exec(abs_program):
            LOGGER.debug("which(%s) = '%s'", program, abs_program)
            _WHICH_CACHE[program] = abs_program
            return abs_program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if _is_exec(exe_file):
                LOGGER.debug("which(%s) = '%s'", program, exe_file)
                _WHICH_CACHE[program] = exe_file
                return exe_file
    LOGGER.debug("which(%s): command not found", program)
    _WHICH_CACHE[program] = None
    return None


def download(src, dest, timeout=8):
    """Downloads or copies files.
    
    `src` may be a file path or URL.  The destination folder will be created 
    if it doesn't exist.  Download is via curl, wget, or Python's urllib as appropriate.
    
    Args:
        src (str): Path or URL to source file.
        dest (str): Path to file copy or download destination.
        timeout (int): Maximum time in seconds for the connection to the server.  0 for no timeout.
        
    Raises:
        IOError: File copy or download failed.
    """
    assert isinstance(timeout, int) and timeout >= 0
    if src.startswith('file://'):
        src = src[6:]
    if os.path.isfile(src):
        LOGGER.debug("Copying '%s' to '%s'", src, dest)
        mkdirp(os.path.dirname(dest))
        shutil.copy(src, dest)
    else:
        LOGGER.debug("Downloading '%s' to '%s'", src, dest)
        LOGGER.info("Downloading '%s'", src)
        mkdirp(os.path.dirname(dest))
        for cmd in "curl", "wget":
            abs_cmd = which(cmd)
            if abs_cmd and _create_dl_subprocess(abs_cmd, src, dest, timeout) == 0:
                return
            LOGGER.warning("%s failed to download '%s'. Retrying with a different method...", cmd, src)                    
        # Fallback: urllib is usually **much** slower than curl or wget and doesn't support timeout
        if timeout:
            raise IOError("Failed to download '%s'" % src)
        with ProgressIndicator() as progress_bar:
            try:
                urllib.urlretrieve(src, dest, reporthook=progress_bar.update)
            except Exception as err:
                LOGGER.warning("urllib failed to download '%s': %s", src, err)
                raise IOError("Failed to download '%s'" % src)


def _create_dl_subprocess(abs_cmd, src, dest, timeout):
    if "curl" in os.path.basename(abs_cmd):
        size_cmd = [abs_cmd, '-sI', src, '--location', '--max-time', str(timeout)]
        get_cmd = [abs_cmd, '-s', '-L', src, '-o', dest, '--connect-timeout', str(timeout)]
    elif "wget" in os.path.basename(abs_cmd):
        size_cmd = [abs_cmd, src, '--spider', '--server-response', '--timeout=%d' % timeout, '--tries=1']
        get_cmd = [abs_cmd, '-q', src, '-O', dest, '--timeout=%d' % timeout]
    else:
        raise InternalError("Invalid command parameter: %s" % abs_cmd)
    try:
        proc_output = get_command_output(size_cmd)
    except subprocess.CalledProcessError as err:
        return err.returncode
    LOGGER.debug(proc_output)
    try:
        file_size = int(proc_output.partition('Content-Length')[2].split()[1])
    except (ValueError, IndexError):
        LOGGER.warning("Invalid response while retrieving download file size")
        file_size = -1
    with ProgressIndicator(file_size) as progress_bar:
        with open(os.devnull, 'wb') as devnull:
            proc = subprocess.Popen(get_cmd, stdout=devnull, stderr=subprocess.STDOUT)
            while proc.poll() is None:
                try:
                    current_size = os.stat(dest).st_size
                except OSError:
                    pass
                else:
                    progress_bar.update(current_size)
                time.sleep(0.1)
            proc.wait()
            retval = proc.returncode
            LOGGER.debug("%s returned %d", get_cmd, retval)
            return retval

def archive_toplevel(archive):
    """Returns the name of the top-level directory in an archive.
    
    Assumes that the archive file is rooted in a single top-level directory::
        foo
            /bar
            /baz
    
    The top-level directory here is "foo"
    This routine will return stupid results for archives with multiple top-level elements.
    
    Args:
        archive (str): Path to archive file.
        
    Raises:
        IOError: `archive` could not be read.
        
    Returns:
        str: Directory name.
    """
    LOGGER.debug("Determining top-level directory name in '%s'", archive)
    try:
        fin = tarfile.open(archive)
    except tarfile.ReadError:
        raise IOError
    else:
        if fin.firstmember.isdir():
            topdir = fin.firstmember.name
        else:
            dirs = [d.name for d in fin.getmembers() if d.isdir()]
            if dirs:
                topdir = min(dirs, key=len)
            else:
                dirs = set()
                names = [d.name for d in fin.getmembers() if d.isfile()]
                for name in names:
                    dirname, basename = os.path.split(name)
                    while dirname:
                        dirname, basename = os.path.split(dirname)
                    dirs.add(basename)
                topdir = min(dirs, key=len)
        LOGGER.debug("Top-level directory in '%s' is '%s'", archive, topdir)
        return topdir


def _show_extract_progress(members):
    with ProgressIndicator(len(members), show_cpu=False) as progress_bar:
        for i, member in enumerate(members):
            progress_bar.update(i)
            yield member

def extract_archive(archive, dest, show_progress=True):
    """Extracts archive file to dest.
    
    Supports compressed and uncompressed tar archives. Destination folder will
    be created if it doesn't exist.
    
    Args:
        archive (str): Path to archive file to extract.
        dest (str): Destination folder.
    
    Returns:
        str: Full path to extracted files.
        
    Raises:
        IOError: Failed to extract archive.
    """
    topdir = archive_toplevel(archive)
    full_dest = os.path.join(dest, topdir)
    mkdirp(dest)
    with tarfile.open(archive) as fin:
        if show_progress:
            LOGGER.info("Checking contents of '%s'", archive)
            with progress_spinner(show_cpu=False):
                members = fin.getmembers()
            LOGGER.info("Extracting '%s' to create '%s'", archive, full_dest)
            fin.extractall(dest, members=_show_extract_progress(members))
        else:
            LOGGER.info("Extracting '%s' to create '%s'", archive, full_dest)
            fin.extractall(dest)
    if not os.path.isdir(full_dest):
        raise IOError("Extracting '%s' does not create '%s'" % (archive, full_dest))
    return full_dest


def create_archive(fmt, dest, items, cwd=None, show_progress=True):
    """Creates a new archive file in the specified format.
    
    Args:
        fmt (str): Archive fmt, e.g. 'zip' or 'tgz'.
        dest (str): Path to the archive file that will be created.
        items (list): Items (i.e. files or folders) to add to the archive.
        cwd (str): Current working directory while creating the archive. 
    """
    if cwd:
        oldcwd = os.getcwd()
        os.chdir(cwd)
    if show_progress:
        LOGGER.info("Writing '%s'...", dest)
        context = progress_spinner
    else:
        context = _null_context
    with context():
        try:
            if fmt == 'zip':
                with ZipFile(dest, 'w') as archive:
                    archive.comment = "Created by TAU Commander"
                    for item in items:
                        archive.write(item)
            elif fmt in ('tar', 'tgz', 'tar.bz2'):
                mode_map = {'tar': 'w', 'tgz': 'w:gz', 'tar.bz2': 'w:bz2'}
                with tarfile.open(dest, mode_map[fmt]) as archive:
                    for item in items:
                        archive.add(item)
            elif fmt == 'gz':
                with open(items[0], 'rb') as fin, gzip.open(dest, 'wb') as fout:
                    shutil.copyfileobj(fin, fout)
            else:
                raise InternalError("Invalid archive format: %s" % fmt)
        finally:
            if cwd:
                os.chdir(oldcwd)


def path_accessible(path, mode='r'):
    """Check if a file or directory exists and is accessable.
    
    Files are checked by attempting to open them with the given mode.
    Directories are checked by testing their access bits only, which may fail for 
    some filesystems which may have permissions semantics beyond the usual POSIX 
    permission-bit model. We'll fix this if it becomes a problem. 
    
    Args:
        path (str): Path to file or directory to check.
        mode (str): File access mode to test, e.g. 'r' or 'rw'
    
    Returns:
        True if the file exists and can be opened in the specified mode, False otherwise.
    """
    assert mode and set(mode) <= set(('r', 'w'))
    if not os.path.exists(path):
        return False
    if os.path.isdir(path):
        modebits = 0
        if 'r' in mode:
            modebits |= os.R_OK
        if 'w' in mode:
            modebits |= os.W_OK | os.X_OK
        return os.access(path, modebits)
    else:
        handle = None
        try:
            handle = open(path, mode)
        except IOError as err:
            if err.errno == errno.EACCES:
                return False
            # Some other error, not permissions
            raise
        else:
            return True
        finally:
            if handle:
                handle.close()
        return False

@contextmanager
def _null_context():
    yield


def create_subprocess(cmd, cwd=None, env=None, stdout=True, log=True, show_progress=False, error_buf=50):
    """Create a subprocess.
    
    See :any:`subprocess.Popen`.
    
    Args:
        cmd (list): Command and its command line arguments.
        cwd (str): If not None, change directory to `cwd` before creating the subprocess.
        env (dict): Environment variables to set or unset before launching cmd.
        stdout (bool): If True send subprocess stdout and stderr to this processes' stdout.
        log (bool): If True send subprocess stdout and stderr to the debug log.
        error_buf (int): If non-zero, stdout is not already being sent, and return value is
                          non-zero then send last `error_buf` lines of subprocess stdout and stderr
                          to this processes' stdout.
        
    Returns:
        int: Subprocess return code.
    """
    subproc_env = dict(os.environ)
    if env: 
        for key, val in env.iteritems():
            if val is None:
                subproc_env.pop(key, None)
                LOGGER.debug("unset %s", key)
            else:
                subproc_env[key] = val
                LOGGER.debug("%s=%s", key, val)
    LOGGER.debug("Creating subprocess: cmd=%s, cwd='%s'\n", cmd, cwd)
    context = progress_spinner if show_progress else _null_context
    with context():
        if error_buf:
            buf = deque(maxlen=error_buf)
        proc = subprocess.Popen(cmd, cwd=cwd, env=subproc_env, 
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        with proc.stdout:
            # Use iter to avoid hidden read-ahead buffer bug in named pipes:
            # http://bugs.python.org/issue3907
            for line in iter(proc.stdout.readline, b''):
                if log:
                    LOGGER.debug(line[:-1])
                if stdout:
                    print line,
                if error_buf:
                    buf.append(line)
        proc.wait()
    retval = proc.returncode
    LOGGER.debug("%s returned %d", cmd, retval)
    if retval and error_buf and not stdout:
        for line in buf:
            print line,
    return retval


def get_command_output(cmd, cwd=None, env=None):
    """Return the possibly cached output of a command.
    
    Just :any:`subprocess.check_output` with a cache.
    Subprocess stderr is always sent to subprocess stdout.
    
    Args:
        cmd (list): Command and its command line arguments.
        cwd (str): Change directory to `cwd` if given, otherwise use :any:`os.getcwd`.
        env (dict): Environment variables to set before launching cmd.

    Raises:
        subprocess.CalledProcessError: return code was non-zero.
        
    Returns:
        str: Subprocess output.
    """
    key = repr((cmd, cwd, env))
    try:
        return get_command_output.cache[key]
    except AttributeError:
        get_command_output.cache = {}
    except KeyError:
        pass
    else:
        LOGGER.debug("Using cached output for command: %s", cmd)
    LOGGER.debug("Checking subprocess output: %s", cmd)
    stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    get_command_output.cache[key] = stdout
    LOGGER.debug(stdout)
    LOGGER.debug("%s returned 0", cmd)
    return stdout


def page_output(output_string):
    """Pipe string to a pager.

    If PAGER is an environment then use that as pager, otherwise
    use `less`.

    Args:
        output_string (str): String to put output.

    """
    output_string = unidecode(output_string.decode('utf-8'))
    if os.environ.get('__TAUCMDR_DISABLE_PAGER__', False):
        print output_string
    else:
        pager_cmd = os.environ.get('PAGER', 'less -F -R -S -X -K').split(' ')
        proc = subprocess.Popen(pager_cmd, stdin=subprocess.PIPE)
        proc.communicate(output_string)


def human_size(num, suffix='B'):
    """Converts a byte count to human readable units.
    
    Args:
        num (int): Number to convert.
        suffix (str): Unit suffix, e.g. 'B' for bytes.
        
    Returns: 
        str: `num` as a human readable string. 
    """
    if not num:
        num = 0
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def parse_bool(value, additional_true=None, additional_false=None):
    """Parses a value to a boolean value.
    
    If `value` is a string try to interpret it as a bool:
    * ['1', 't', 'y', 'true', 'yes', 'on'] ==> True
    * ['0', 'f', 'n', 'false', 'no', 'off'] ==> False
    Otherwise raise TypeError.
    
    Args:
        value: value to parse to a boolean.
        additional_true (list): optional additional string values that stand for True.
        additional_false (list): optional additional string values that stand for False.
        
    Returns:
        bool: True if  `value` is true, False if `value` is false.
        
    Raises:
        ValueError: `value` does not parse.
    """
    true_values = ['1', 't', 'y', 'true', 'yes', 'on']
    false_values = ['0', 'f', 'n', 'false', 'no', 'off', 'none']
    if additional_true:
        true_values.extend(additional_true)
    if additional_false:
        false_values.extend(additional_false)
    if isinstance(value, basestring):
        value = value.lower()
        if value in true_values:
            return True
        elif value in false_values:
            return False
        else:
            raise TypeError
    return bool(value)


def is_url(url):
    """Check if `url` is a URL.
    
    Args:
        url (str): String to check
        
    Returns:
        bool: True if `url` is a URL, False otherwise.
    """
    return bool(len(urlparse.urlparse(url).scheme))


def camelcase(name):
    """Converts a string to CamelCase.
    
    Args:
        name (str): String to convert.
        
    Returns:
        str: `name` in CamelCase.
    """
    return ''.join(x.capitalize() for x in name.split('_'))


def hline(title, *args, **kwargs):
    """Build a colorful horizontal rule for console output.
    
    Uses :any:`logger.LINE_WIDTH` to generate a string of '=' characters
    as wide as the terminal.  `title` is included in the string near the
    left of the horizontal line. 
    
    Args:
        title (str): Text to put on the horizontal rule.
        *args: Positional arguments to pass to :any:`termcolor.colored`.
        **kwargs: Keyword arguments to pass to :any:`termcolor.colored`.
    
    Returns:
        str: The horizontal rule.
    """
    text = "{:=<{}}\n".format('== %s ==' % title, logger.LINE_WIDTH)
    return color_text(text, *args, **kwargs)


def color_text(text, *args, **kwargs):
    """Use :any:`termcolor.colored` to colorize text.
    
    Args:
        text (str): Text to colorize.
        *args: Positional arguments to pass to :any:`termcolor.colored`.
        **kwargs: Keyword arguments to pass to :any:`termcolor.colored`.
        
    Returns:
        str: The colorized text.
    """
    return termcolor.colored(text, *args, **kwargs)


def uncolor_text(text):
    """Remove color control chars from a string.
    
    Args:
        text (str): Text to colorize.
        
    Returns:
        str: The text without control chars.
    """
    return re.sub(_COLOR_CONTROL_RE, '', text)


def walk_packages(path, prefix):
    """Fix :any:`pkgutil.walk_packages` to work with Python zip files.
    
    Python's default :any:`zipimporter` doesn't provide an `iter_modules` method so
    :any:`pkgutil.walk_packages` silently fails to list modules and packages when
    they are in a zip file.  This implementation works around this.
    """
    def seen(path, dct={}):     # pylint: disable=dangerous-default-value
        if path in dct:
            return True
        dct[path] = True
    for importer, name, ispkg in _iter_modules(path, prefix):
        yield importer, name, ispkg
        if ispkg:
            __import__(name)
            path = getattr(sys.modules[name], '__path__', None) or []
            path = [p for p in path if not seen(p)]
            for item in walk_packages(path, name+'.'):
                yield item


def _zipimporter_iter_modules(archive, path):
    """The missing zipimporter.iter_modules method."""
    libdir, _, pkgpath = path.partition(archive + os.sep)
    with ZipFile(os.path.join(libdir, archive)) as zipfile:
        namelist = zipfile.namelist()
    
    def iter_modules(prefix):
        for fname in namelist:
            fname, ext = os.path.splitext(fname)
            if ext in _PY_SUFFEXES:
                extrapath, _, modname = fname.partition(pkgpath + os.sep)
                if extrapath or modname == '__init__':
                    continue
                pkgname, modname = os.path.split(modname)
                if pkgname:
                    if os.sep in pkgname:
                        continue
                    yield prefix + pkgname, True
                else:
                    yield prefix + modname, False
    return iter_modules


def _iter_modules(paths, prefix):
    # pylint: disable=no-member,redefined-variable-type
    yielded = {}
    for path in paths:
        importer = pkgutil.get_importer(path)
        if isinstance(importer, zipimporter):
            archive = os.path.basename(importer.archive)
            iter_importer_modules = _zipimporter_iter_modules(archive, path)
        else:
            iter_importer_modules = importer.iter_modules
        for name, ispkg in iter_importer_modules(prefix):
            if name not in yielded:
                yielded[name] = True
                yield importer, name, ispkg
 
