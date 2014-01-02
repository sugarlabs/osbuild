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

import json
import os

from osbuild import utils

interactive = True
config_dir = None
docs_dir = None
install_dir = None
lib_dir = None
share_dir = None
bin_dir = None
etc_dir = None
libexec_dir = None
package_files = None
system_lib_dirs = None
home_state_dir = None
build_state_dir = None
home_dir = None
git_user_name = None
git_email = None
karma_browser_path = None

_source_dir = None
_dist_dir = None
_prefs_path = None
_cached_prefs = None


class Module:
    def __init__(self, info):
        self.name = info["name"]
        self.repo = info["repo"]
        self.branch = info.get("branch", "master")
        self.tag = info.get("tag", None)
        self.auto_install = info.get("auto-install", False)
        self.options = info.get("options", [])
        self.options_evaluated = info.get("options_evaluated", [])
        self.clean_stamp = info.get("clean_stamp", None)
        self.has_checks = info.get("has_checks", False)
        self.no_libdir = info.get("no_libdir", False)
        self.makefile_name = info.get("makefile_name", "Makefile")
        self.has_docs = info.get("has_docs", False)
        self.docs_dir = info.get("docs_dir", self.name)
        self.docs_extras = info.get("docs_extras", None)
        self.dist = info.get("dist", False)
        self.build_system = info.get("build_system", None)

        if self.build_system is None:
            self.build_system = self._guess_build_system()

    def get_source_dir(self):
        return os.path.join(get_source_dir(), self.name)

    def _guess_build_system(self):
        source_dir = self.get_source_dir()

        package_json = os.path.join(source_dir, "package.json")

        if os.path.exists(os.path.join(source_dir, "setup.py")):
            return "distutils"
        elif os.path.exists(package_json):
            with open(package_json) as f:
                parsed_json = json.load(f)
                if "volo" in parsed_json:
                    return "volo"
                else:
                    return "npm"
        elif (os.path.exists(os.path.join(source_dir, "autogen.sh")) or
              os.path.exists(os.path.join(source_dir, "configure"))):
            return "autotools"
        else:
            return None


def setup(**kwargs):
    global config_dir
    config_dir = kwargs.get("config_dir", None)

    global docs_dir
    docs_dir = kwargs["docs_dir"]

    global _prefs_path
    _prefs_path = kwargs.get("prefs_path", None)

    global _source_dir
    _source_dir = kwargs["source_dir"]

    global _dist_dir
    _dist_dir = kwargs["dist_dir"]

    global build_state_dir
    build_state_dir = kwargs["build_state_dir"]
    utils.ensure_dir(build_state_dir)

    global home_state_dir
    home_state_dir = kwargs["home_state_dir"]
    utils.ensure_dir(home_state_dir)

    global home_dir
    home_dir = os.path.join(home_state_dir, kwargs["profile_name"])
    utils.ensure_dir(home_dir)

    _setup_install_dir(kwargs["install_dir"])

    if "git_user_name" in kwargs:
        global git_user_name
        git_user_name = kwargs["git_user_name"]

    if "git_email" in kwargs:
        global git_email
        git_email = kwargs["git_email"]

    if "interactive" in kwargs:
        global interactive
        interactive = kwargs["interactive"]

    if "karma_browser" in kwargs:
        global karma_browser_path
        karma_browser_path = os.path.join(bin_dir, kwargs["karma_browser"])


def get_dist_dir():
    global _dist_dir
    utils.ensure_dir(_dist_dir)
    return _dist_dir


def get_source_dir():
    global _source_dir
    utils.ensure_dir(_source_dir)
    return _source_dir


def get_prefs():
    global _cached_prefs

    if _cached_prefs:
        return _cached_prefs

    # Defaults
    prefs = {}

    if _prefs_path is not None:
        try:
            with open(_prefs_path) as f:
                prefs.update(json.load(f))
        except IOError:
            pass

        _cached_prefs = prefs

    return prefs


def load_modules():
    with open(os.path.join(config_dir, "modules.json")) as f:
        return [Module(info) for info in json.load(f)]


def _setup_install_dir(path):
    global system_lib_dirs
    global install_dir
    global share_dir
    global bin_dir
    global etc_dir
    global lib_dir
    global libexec_dir

    install_dir = path
    utils.ensure_dir(install_dir)

    share_dir = os.path.join(install_dir, "share")
    bin_dir = os.path.join(install_dir, "bin")
    etc_dir = os.path.join(install_dir, "etc")
    libexec_dir = os.path.join(install_dir, "libexec")
    lib_dir = os.path.join(install_dir, "lib64")
    system_lib_dirs = ["/usr/lib64"]
