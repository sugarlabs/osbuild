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
import textwrap

from osbuild import config


def start():
    os.environ["OSBUILD_SHELL"] = "yes"

    script = """
             if [ -f ~/.bashrc ]; then
                . ~/.bashrc
             fi

             export PS1="[osbuild \W]$ "
             """

    bashrc_path = os.path.join(config.etc_dir, "bashrc")

    with open(bashrc_path, "w") as f:
        f.write(textwrap.dedent(script))

    args = ["/bin/bash", "--rcfile", bashrc_path]

    os.execlp(args[0], *args)
