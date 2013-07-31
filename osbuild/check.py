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
import subprocess
import json
import logging
import difflib
from StringIO import StringIO

from osbuild import config
from osbuild import command
from osbuild import xvfb
from osbuild import build

_checkers = {}


def check_one(module_name):
    for module in config.load_modules():
        if module.name == module_name:
            return _check_module(module)

    return False


def check():
    if not build.build():
        return False

    modules = config.load_modules()
    for module in modules:
        if not _check_module(module):
            return False

    return True


def _check_module(module):
    if not module.has_checks:
        return True

    print("* Checking %s" % module.name)
    return _checkers[module.build_system](module)


def _diff_output(output, path):
    with open(path) as f:
        diff = difflib.unified_diff(f.readlines(),
                                    StringIO(output).readlines())

        joined = "".join([line for line in diff])
        if joined:
            print("\njs-beautify check failed for %s\n\n" % path)
            print(joined)
            return True

    return False


def _volo_checker(module):
    source_dir = module.get_source_dir()

    os.chdir(source_dir)
    with open("package.json") as f:
        package = json.load(f)
        if "dependencies" in package["volo"]:
            command.run(["volo", "-nostamp", "-f", "add"], retry=10)

    test_dir = os.path.join(source_dir, "test")
    if os.path.exists(test_dir):
        os.chdir(test_dir)
        command.run(["karma", "start", "--single-run", "--no-colors",
                     "--log-level debug"])

    for root, dirs, files in os.walk(module.get_source_dir()):
        if root == source_dir and "lib" in dirs:
            dirs.remove("lib")
        for f in files:
            path = os.path.join(root, f)

            if f.endswith(".js"):

                try:
                    command.run(["jshint", path])
                except subprocess.CalledProcessError:
                    return False

                logging.info("Running js-beautify on %s" % path)
                args = ["js-beautify", "--good-stuff", path]
                if _diff_output(subprocess.check_output(args), path):
                    return False
            elif f.endswith(".css"):
                less_name = f.replace(".css", ".less")
                if os.path.exists(os.path.join(root, less_name)):
                    continue

                logging.info("Running js-beautify on %s" % path)
                args = ["js-beautify", "--type", "css",
                        "--indent-size", "2", path]
                if _diff_output(subprocess.check_output(args), path):
                    return False
            elif f.endswith(".html"):
                logging.info("Running js-beautify on %s" % path)
                args = ["js-beautify", "--type", "html",
                        "--indent-size", "2", path]
                if _diff_output(subprocess.check_output(args), path):
                    return False

    return True

_checkers['volo'] = _volo_checker


def _distutils_checker(module):
    result = True

    os.chdir(module.get_source_dir())

    command.run(["python", "setup.py", "lint"])

    xvfb_proc, orig_display = xvfb.start()

    try:
        command.run(["python", "setup.py", "test"])
    except subprocess.CalledProcessError:
        result = False

    xvfb.stop(xvfb_proc, orig_display)

    return result

_checkers['distutils'] = _distutils_checker


def _autotools_checker(module):
    result = True
    os.chdir(module.get_source_dir())
    xvfb_proc, orig_display = xvfb.start()

    try:
        command.run(["dbus-launch", "--exit-with-session",
                     "make", "test"])
    except subprocess.CalledProcessError:
        result = False

    xvfb.stop(xvfb_proc, orig_display)

    return result

_checkers['autotools'] = _autotools_checker
