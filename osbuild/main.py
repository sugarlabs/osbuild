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

import argparse
import json

from osbuild import config
from osbuild import build
from osbuild import clean
from osbuild import state
from osbuild import shell


def run_build():
    if not build.build():
        return False

    return True


def setup(config_args):
    config.setup(**config_args)
    return True


def cmd_clean():
    parser = argparse.ArgumentParser()
    parser.add_argument("module", nargs="?",
                        help="name of the module to clean")
    parser.add_argument("--build-state", action="store_true",
                        help="clean the build state only")
    args = parser.parse_args()

    if args.build_state:
        state.clean(state.BUILT_MODULES)
    elif args.module:
        if not build.clean_one(args.module):
            return False
    else:
        if not clean.clean():
            return False

    return True


def cmd_pull():
    parser = argparse.ArgumentParser()
    parser.add_argument("module", nargs="?",
                        help="name of the module to pull")
    parser.add_argument("--revisions",
                        help="json dict with the revisions to pull")
    args = parser.parse_args()

    if args.module:
        if not build.pull_one(args.module):
            return False
    else:
        revisions = {}
        if args.revisions:
            revisions = json.loads(args.revisions)

        if not build.pull(revisions):
            return False

    return True


def cmd_shell():
    shell.start()


def cmd_build():
    parser = argparse.ArgumentParser()
    parser.add_argument("module", nargs="?",
                        help="name of the module to build")
    args = parser.parse_args()

    if args.module:
        result = build.build_one(args.module)
    else:
        result = run_build()

    return result
