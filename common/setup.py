# -*- coding: utf-8 -*-
# setup.py
# Copyright (C) 2013 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
setup file for leap.soledad.common
"""
import re
from setuptools import setup
from setuptools import find_packages

import versioneer
versioneer.versionfile_source = 'src/leap/soledad/common/_version.py'
versioneer.versionfile_build = 'leap/soledad/common/_version.py'
versioneer.tag_prefix = ''  # tags are like 1.2.0
versioneer.parentdir_prefix = 'leap.soledad.common-'

from pkg import utils

trove_classifiers = (
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: "
    "GNU General Public License v3 or later (GPLv3+)",
    "Environment :: Console",
    "Operating System :: OS Independent",
    "Operating System :: POSIX",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Topic :: Database :: Front-Ends",
    "Topic :: Software Development :: Libraries :: Python Modules"
)

DOWNLOAD_BASE = ('https://github.com/leapcode/soledad/'
                 'archive/%s.tar.gz')
_versions = versioneer.get_versions()
VERSION = _versions['version']
VERSION_FULL = _versions['full']
DOWNLOAD_URL = ""

# get the short version for the download url
_version_short = re.findall('\d+\.\d+\.\d+', VERSION)
if len(_version_short) > 0:
    VERSION_SHORT = _version_short[0]
    DOWNLOAD_URL = DOWNLOAD_BASE % VERSION_SHORT

cmdclass = versioneer.get_cmdclass()


from setuptools import Command


class freeze_debianver(Command):
    """
    Freezes the version in a debian branch.
    To be used after merging the development branch onto the debian one.
    """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        proceed = str(raw_input(
            "This will overwrite the file _version.py. Continue? [y/N] "))
        if proceed != "y":
            print("He. You scared. Aborting.")
            return
        template = r"""
# This file was generated by the `freeze_debianver` command in setup.py
# Using 'versioneer.py' (0.7+) from
# revision-control system data, or from the parent directory name of an
# unpacked source archive. Distribution tarballs contain a pre-generated copy
# of this file.

version_version = '{version}'
version_full = '{version_full}'
"""
        templatefun = r"""

def get_versions(default={}, verbose=False):
        return {'version': version_version, 'full': version_full}
"""
        subst_template = template.format(
            version=VERSION_SHORT,
            version_full=VERSION_FULL) + templatefun
        with open(versioneer.versionfile_source, 'w') as f:
            f.write(subst_template)


#
# Couch backend design docs file generation.
#

from os import listdir
from os.path import realpath, dirname, isdir, join, isfile, basename
import json
import binascii


old_cmd_sdist = cmdclass["sdist"]


def build_ddocs_py(basedir=None, with_src=True):
    """
    Build `ddocs.py` file.

    For ease of development, couch backend design documents are stored as
    `.js` files in  subdirectories of `src/leap/soledad/common/ddocs`. This
    function scans that directory for javascript files, builds the design
    documents structure, and encode those structures in the `ddocs.py` file.

    This function is used when installing in develop mode, building or
    generating source distributions (see the next classes and the `cmdclass`
    setuptools parameter.

    This funciton uses the following conventions to generate design documents:

      - Design documents are represented by directories in the form
        `<prefix>/<ddoc>`, there prefix is the `src/leap/soledad/common/ddocs`
        directory.
      - Design document directories might contain `views`, `lists` and
        `updates` subdirectories.
      - Views subdirectories must contain a `map.js` file and may contain a
        `reduce.js` file.
      - List and updates subdirectories may contain any number of javascript
        files (i.e. ending in `.js`) whose names will be mapped to the
        corresponding list or update function name.
    """
    cur_pwd = dirname(realpath(__file__))
    common_path = ('src', 'leap', 'soledad', 'common')
    dest_common_path = common_path
    if not with_src:
        dest_common_path = common_path[1:]
    prefix = join(cur_pwd, *common_path)

    dest_prefix = prefix
    if basedir is not None:
        # we're bulding a sdist
        dest_prefix = join(basedir, *dest_common_path)

    ddocs_prefix = join(prefix, 'ddocs')

    if not isdir(ddocs_prefix):
        print "No ddocs/ folder, bailing out..."
        return

    ddocs = {}

    # design docs are represented by subdirectories of `ddocs_prefix`
    for ddoc in [f for f in listdir(ddocs_prefix)
                 if isdir(join(ddocs_prefix, f))]:

        ddocs[ddoc] = {'_id': '_design/%s' % ddoc}

        for t in ['views', 'lists', 'updates']:
            tdir = join(ddocs_prefix, ddoc, t)
            if isdir(tdir):

                ddocs[ddoc][t] = {}

                if t == 'views':  # handle views (with map/reduce functions)
                    for view in [f for f in listdir(tdir)
                                 if isdir(join(tdir, f))]:
                        # look for map.js and reduce.js
                        mapfile = join(tdir, view, 'map.js')
                        reducefile = join(tdir, view, 'reduce.js')
                        mapfun = None
                        reducefun = None
                        try:
                            with open(mapfile) as f:
                                mapfun = f.read()
                        except IOError:
                            pass
                        try:
                            with open(reducefile) as f:
                                reducefun = f.read()
                        except IOError:
                            pass
                        ddocs[ddoc]['views'][view] = {}

                        if mapfun is not None:
                            ddocs[ddoc]['views'][view]['map'] = mapfun
                        if reducefun is not None:
                            ddocs[ddoc]['views'][view]['reduce'] = reducefun

                else:  # handle lists, updates, etc
                    for fun in [f for f in listdir(tdir)
                                if isfile(join(tdir, f))]:
                        funfile = join(tdir, fun)
                        funname = basename(funfile).replace('.js', '')
                        try:
                            with open(funfile) as f:
                                ddocs[ddoc][t][funname] = f.read()
                        except IOError:
                            pass
    # write file containing design docs strings
    ddoc_filename = "ddocs.py"
    with open(join(dest_prefix, ddoc_filename), 'w') as f:
        for ddoc in ddocs:
            f.write(
                "%s = '%s'\n" %
                (ddoc, binascii.b2a_base64(json.dumps(ddocs[ddoc]))[:-1]))
    print "Wrote design docs in %s" % (dest_prefix + '/' + ddoc_filename,)


from setuptools.command.develop import develop as _cmd_develop


class cmd_develop(_cmd_develop):
    def run(self):
        # versioneer:
        versions = versioneer.get_versions(verbose=True)
        self._versioneer_generated_versions = versions
        # unless we update this, the command will keep using the old version
        self.distribution.metadata.version = versions["version"]
        _cmd_develop.run(self)
        build_ddocs_py()


# versioneer powered
old_cmd_build = cmdclass["build"]


class cmd_build(old_cmd_build):
    def run(self):
        old_cmd_build.run(self)
        build_ddocs_py(basedir=self.build_lib, with_src=False)


cmdclass["freeze_debianver"] = freeze_debianver
cmdclass["build"] = cmd_build
cmdclass["develop"] = cmd_develop


# XXX add ref to docs

setup(
    name='leap.soledad.common',
    version=VERSION,
    cmdclass=cmdclass,
    url='https://leap.se/',
    download_url=DOWNLOAD_URL,
    license='GPLv3+',
    description='Synchronization of locally encrypted data among devices '
                '(common files).',
    author='The LEAP Encryption Access Project',
    author_email='info@leap.se',
    maintainer='Kali Kaneko',
    maintainer_email='kali@leap.se',
    long_description=(
        "Soledad is the part of LEAP that allows application data to be "
        "securely shared among devices. It provides, to other parts of the "
        "LEAP project, an API for data storage and sync."
    ),
    classifiers=trove_classifiers,
    namespace_packages=["leap", "leap.soledad"],
    packages=find_packages('src', exclude=['*.tests', '*.tests.*']),
    package_dir={'': 'src'},
    test_suite='leap.soledad.common.tests',
    install_requires=utils.parse_requirements(),
    tests_require=utils.parse_requirements(
        reqfiles=['pkg/requirements-testing.pip']),
    extras_require={
        'couchdb': ['couchdb'],
    },
)
