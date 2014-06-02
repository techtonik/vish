"""Run subprocess.
"""
import os
import sys
import subprocess

if sys.version_info < (3, 0):
    FileNotFoundError = OSError


def get_ve_base(vexrc):
    """Find a directory to look for virtualenvs in.
    """
    # set ve_base to a path we can look for virtualenvs:
    # 1. .vexrc
    # 2. WORKON_HOME (as defined for virtualenvwrapper's benefit)
    # 3. $HOME/.virtualenvs
    # (unless we got --path, then we don't need it)
    ve_base = vexrc[None].get('virtualenvs')
    if ve_base:
        ve_base = os.path.expanduser(ve_base)
    else:
        ve_base = os.environ.get('WORKON_HOME')
    if not ve_base:
        home = os.environ.get('HOME', None)
        if not home:
            return None
        ve_base = os.path.join(home, '.virtualenvs')
    return ve_base


def get_command(options, vexrc):
    """Find a command to run.
    """
    command = options.rest
    if not command:
        command = vexrc[None].get('shell') or os.environ.get('SHELL')
        command = [command] if command else None
    return command


def make_env(environ, defaults, options):
    """Make an environment to run with.
    """
    # Copy the parent environment, add in defaults from .vexrc.
    env = os.environ.copy()
    env.update(defaults)

    # Leaving in existing PYTHONHOME can cause some errors
    if 'PYTHONHOME' in env:
        del env['PYTHONHOME']

    # Now we have to adjust PATH to find scripts for the virtualenv...
    path = environ.get('PATH', None)
    assert path
    assert options.path
    ve_bin = os.path.join(options.path, 'bin')
    assert ve_bin

    # I don't expect this to fail, but I'd rather be slightly paranoid and fail
    # early before putting a nonexistent path on PATH.
    assert os.path.exists(ve_bin), "ve_bin %r does not exist" % ve_bin

    # If user is currently in a virtualenv, DON'T just prepend
    # to its path (vex foo; echo $PATH -> " /foo/bin:/bar/bin")
    # but don't incur this cost unless we're already in one.
    # activate handles this by running 'deactivate' first, we don't
    # have that so we have to use other ways.
    # This would not be necessary and things would be simpler if vex
    # did not have to interoperate with a ubiquitous existing tool.
    # virtualenv doesn't...
    current_ve = env.get('VIRTUAL_ENV')
    if current_ve:
        # Since activate doesn't export _OLD_VIRTUAL_PATH, we are going to
        # manually remove the virtualenv's bin.
        # A virtualenv's bin should not normally be on PATH except
        # via activate or similar, so I'm OK with this solution.
        current_ve_bin = os.path.join(current_ve, 'bin')
        segments = path.split(os.pathsep)
        segments.remove(current_ve_bin)
        path = os.pathsep.join(segments)

    env['PATH'] = os.pathsep.join([ve_bin, path])
    env['VIRTUAL_ENV'] = options.path
    return env


def run(command, env, cwd):
    """Run the given command.
    """
    try:
        process = subprocess.Popen(command, env=env, cwd=cwd)
        process.wait()
    except FileNotFoundError:
        return None
    return process.returncode