#!/usr/local/autopkg/python
#
# Copyright 2024 David Pirie
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from pathlib import Path
import subprocess
import shutil

from autopkglib import Processor, ProcessorError


__all__ = ["GitRepoClone"]


class GitRepoClone(Processor):
    description = ("Clones a git repo with git.")
    input_variables = {
        "repo_url": {
            "required": True,
            "description": "URL of the git repo to be cloned."
        },
        "repo_directory": {
            "required": True,
            "description": "Path to the directory the repo is cloned to."
        },
        "replace_existing": {
            "required": False,
            "description": "Boolean. When set to True (or anything that equates to True), if the repo_path already exists, delete it before cloning. Defaults to False.",
            "default": "False"
        },
        "allow_existing": {
            "required": False,
            "description": "Boolean. When set to False (or anything that equates to False) and replace_existing is True, if the repo_path already exists exits with an error. Defaults to False.",
            "default": "False"
        }
    }
    output_variables = {
        "repo_cloned": {
             "description": "Boolean. True if a git clone is performed."
        }
   }

    __doc__ = description

    def main(self):
        self.repo_url: str = self.env.get("repo_url")
        self.repo_directory: Path = Path(self.env.get("repo_directory"))
        self.replace_existing: bool = (self.env.get("replace_existing", False) == True)
        self.allow_existing: bool = (self.env.get("allow_existing", False) == True)
        self.repo_cloned: bool = False

        if not self.repo_url:
            raise ProcessorError(f"repo_url cannot be empty")

        if not self.repo_directory.parent.exists():
            self.repo_directory.parent.mkdir(mode=0o755, parents=True, exist_ok=True)

        if self.repo_directory.exists() and self.replace_existing:
            try:
                if self.repo_directory.is_file() or self.repo_directory.is_symlink():
                    self.repo_directory.unlink()
                elif self.repo_directory.is_dir():
                    shutil.rmtree(self.repo_directory)
                else:
                    raise ProcessorError(f"Could not remove {self.repo_directory} - it is not a file, link, or directory.")
                self.output(f"Deleted {self.repo_directory}.")
            except OSError as err:
                raise ProcessorError(f"Could not remove {self.repo_directory}: {err}")

        if self.repo_directory.exists():
            if self.allow_existing:
                self.output(f"Repo directory {self.repo_directory} exists and allow_existing is {self.allow_existing}.")
            else:
                raise ProcessorError(f"{self.repo_directory} exists but allow_existing is {self.allow_existing}.")
        else:
            try:
                self.output(subprocess.run(["git", "clone", self.repo_url, str(self.repo_directory)], shell=True, cwd=self.env.get("RECIPE_CACHE_DIR"), capture_output=True, check=True, text=True).stdout)
            except subprocess.CalledProcessError as e:
                raise ProcessorError(f"Error running subprocess: {str(e)}.")
            self.repo_cloned = True

        self.env["repo_cloned"] = self.repo_cloned
        self.output(f"repo_cloned: {self.env['repo_cloned']}")



if __name__ == '__main__':
    processor = GitRepoClone()
    processor.execute_shell()