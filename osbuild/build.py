# Copyright 2013 Daniel Narvaez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import multiprocessing
import shutil
import subprocess
import logging

from osbuild import command
from osbuild import config
from osbuild import state
from osbuild import git

_builders = {}
_distributors = {}


def build_one(module_name):
    for module in config.load_modules():
        if module.name == module_name:
            return _build_module(module)

    return False


def pull_one(module_name):
    for module in config.load_modules():
        if module.name == module_name:
            return _pull_module(module)

    return False


def pull(revisions={}):
    to_pull = config.load_modules()

    if to_pull:
        print("\n= Pulling =\n")

    for module in to_pull:
        if state.pulled_module_should_clean(module):
            source_dir = module.get_source_dir()

            if os.path.exists(source_dir):
                if not _clean_module(module):
                    print("! Could not clean module, pull failed.")
                    return False

                shutil.rmtree(source_dir, ignore_errors=True)

    for module in to_pull:
        revision = revisions.get(module.name, None)
        if not _pull_module(module, revision):
            return False

    return True


def build():
    to_build = []
    for module in config.load_modules():
        if not state.built_module_is_unchanged(module):
            to_build.append(module)

    if not to_build:
        return True

    print("\n= Building =\n")

    for module in to_build:
        if not _build_module(module):
            return False

    return True


def _clean_module(module):
    print("* Cleaning %s" % module.name)

    git_module = git.get_module(module)
    if os.path.exists(module.get_source_dir()):
        return git_module.clean()
    else:
        return True


def clean_one(module_name):
    for module in config.load_modules():
        if module.name == module_name:
            return _clean_module(module)

    return False


def clean(continue_on_error=True):
    for module in config.load_modules():
        if not _clean_module(module) and not continue_on_error:
            return False

    return True


def _pull_module(module, revision=None):
    print("* Pulling %s" % module.name)

    git_module = git.get_module(module)

    try:
        git_module.update(revision)
    except subprocess.CalledProcessError:
        return False

    logging.info("{0} HEAD: {1}".format(module.name, git_module.get_head()))

    state.pulled_module_touch(module)

    return True


def _build_autotools(module):
    makefile_path = os.path.join(module.get_source_dir(), module.makefile_name)

    if not os.path.exists(makefile_path):
        configure = os.path.join(module.get_source_dir(), "autogen.sh")
        if not os.path.exists(configure):
            configure = os.path.join(module.get_source_dir(), "configure")

        args = [configure, "--prefix=/usr"]
        args.extend(module.options)
        command.run(args)

    jobs = multiprocessing.cpu_count() * 2

    command.run(["make", "-j", "%d" % jobs])
    command.run(["sudo", "make", "install"])


_builders["autotools"] = _build_autotools


def _build_distutils(module):
    setup = os.path.join(module.get_source_dir(), "setup.py")
    command.run(["python", setup, "install"])

_builders["distutils"] = _build_distutils


def _build_module(module):
    print("* Building %s" % module.name)

    source_dir = module.get_source_dir()

    if not os.path.exists(source_dir):
        print("Source directory does not exist. Please pull the sources "
              "before building.")
        return False

    os.chdir(source_dir)

    try:
        if module.build_system is not None:
            _builders[module.build_system](module)
    except subprocess.CalledProcessError:
        return False

    state.built_module_touch(module)

    return True
