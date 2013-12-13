from distutils.core import setup, Command, Extension
from distutils.command.build_py import build_py
import commands

from distutils.sysconfig import get_config_vars
import os, sys, string, shutil, errno
from site import USER_BASE

flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}

def get_additional_include_dir_from_env():
    kw = {'include_dirs':[], 'library_dirs':[], 'libraries':[]}
    for token in commands.getoutput("echo $CPLUS_INCLUDE_PATH").split(":"):
        if token != "":
            kw['include_dirs'].append(token)
    return kw

# define pkgconfig return data
def pkgconfig(pkgname, required=True):

    if commands.getoutput("pkg-config --exists "+pkgname+" ; echo $?") == "0":
        print "-- "+pkgname + " found"
    else:
        print "-- "+pkgname + " not found"
        if required:
            raise ValueError("  -- This package ("+pkgname+") is required.")
        return None
    kw = {'include_dirs':[], 'library_dirs':[], 'libraries':[], "compiler_options":[]}
    for token in commands.getoutput("pkg-config --libs --cflags "+pkgname).split():
        if token[:2] in flag_map:
            kw[flag_map[token[:2]]].append(token[2:])
#        else:
#            print "token: '"+token+"' not taken into account"
    return kw


def get_package_from_build_type(pkgname, required=True, Debug=False, dbg_postfix="_dbg"):
    if Debug:
        res = pkgconfig(pkgname+dbg_postfix, False)
        if res is None:
            print "-- looking for release version of package:"
            return pkgconfig(pkgname+dbg_postfix, required)
        else:
            return res
    else:
        return pkgconfig(pkgname+dbg_postfix, required)


def get_packages_data(lpkg):
    kw = {'include_dirs':[], 'library_dirs':[], 'libraries':[]}
    for pkg in lpkg:
        for n in kw:
            kw[n].extend(pkg[n])
    return kw

def force_symlink(file1, file2):
    try:
        os.symlink(file1, file2)
    except OSError, e:
        if e.errno == errno.EEXIST:
            shutil.rmtree(file2)
            os.symlink(file1, file2)

class develop(Command):
    description = "Create symbolic link instead of installing files"
    user_options = [
            ('prefix=', None, "installation prefix"),
            ('uninstall', None, "uninstall development files")
            ]

    def initialize_options(self):
        self.prefix = None
        self.uninstall = 0

    def finalize_options(self):
        self.py_version = (string.split(sys.version))[0]
        if self.prefix is None:
            self.prefix = USER_BASE
        self.prefix = os.path.expanduser(self.prefix)

    def run(self):
        for package_name in self.distribution.packages:
            out_dir = os.path.join(self.prefix, "lib", "python"+self.py_version[0:3], "site-packages")
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)

            out_dir = os.path.join(out_dir, package_name)
            src_dir = os.path.join(os.getcwd(),self.distribution.package_dir[package_name])
            if self.uninstall == 1:
                if os.path.islink(out_dir):
                    print "Removing symlink "+out_dir
                    os.remove(out_dir)
                else:
                    print "Not in dev mode, nothing to do"
            else:
                if os.path.islink(out_dir):
                    print "Already in dev mode"
                else:
                    print "Creating symlink "+src_dir+" -> "+out_dir
                    force_symlink(src_dir, out_dir)

cmdclass={'develop': develop}

try:
    # add a command for building the html doc
    from sphinx.setup_command import BuildDoc
    cmdclass['build_doc'] = BuildDoc
except ImportError:
    pass


if sys.argv[0] == "setup.py":
    script_name=sys.argv[0]
    script_args=sys.argv[1:]
else:
    script_name=sys.argv[1]
    script_args=sys.argv[2:]

