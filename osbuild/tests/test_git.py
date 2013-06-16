import os
import tempfile
import unittest
import subprocess

from osbuild import git


class TestGit(unittest.TestCase):
    def _create_repo(self):
        path = tempfile.mkdtemp()
        os.chdir(path)

        subprocess.check_call(["git", "init"])

        subprocess.check_call(["git", "config", "user.name", "Test Test"])
        subprocess.check_call(["git", "config", "user.email", "test@test.org"])

        with open("README", "w") as f:
            f.write("")

        subprocess.check_call(["git", "add", "README"])

        self._commit(path, "Initial commit")

        return path

    def _commit(self, remote, log):
        os.chdir(remote)
        subprocess.check_call(["git", "commit", "-a", "-m", log])

    def _get_head(self, remote):
        os.chdir(remote)
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).strip()

    def _read_file(self, module):
        content = None

        f = open(os.path.join(module.local, "README"))
        content = f.read()
        f.close()

        return content

    def _create_branch(self, remote, name):
        os.chdir(remote)
        subprocess.check_call(["git", "checkout", "-b", name])

    def _write_file(self, remote, content):
        f = open(os.path.join(remote, "README"), "w")
        f.write(content)
        f.close()

    def _create_module(self, remote, branch="master", tag=None):
        path = tempfile.mkdtemp()
        name = "test"

        return git.Module(path=path, name=name, remote=remote, branch=branch,
                          tag=tag)

    def _setup_module(self):
        remote = self._create_repo()

        module = self._create_module(remote)
        module.update()

        return module

    def test_clone(self):
        module = self._setup_module()
        self.assertTrue(os.path.exists(os.path.join(module.local, "README")))

    def test_update_on_master(self):
        module = self._setup_module()

        remote = module._remotes["origin"]
        self._write_file(remote, "masterchange")
        self._commit(remote, "masterchange")

        module.update()

        self.assertEquals("masterchange", self._read_file(module))

    def test_update_on_branch(self):
        remote = self._create_repo()
        self._create_branch(remote, "test")

        module = self._create_module(remote, branch="test")

        remote = module._remotes["origin"]
        self._write_file(remote, "branchchange")
        self._commit(remote, "branchchange")

        module.update()

        self.assertEquals("branchchange", self._read_file(module))

    def test_update_detached(self):
        remote = self._create_repo()

        module = self._create_module(remote, tag=self._get_head(remote))
        module.update()

        remote = module._remotes["origin"]
        self._write_file(remote, "detachedchange")
        self._commit(remote, "detachedchange")

        module.tag = self._get_head(remote)
        module.update()

        self.assertEquals("detachedchange", self._read_file(module))
