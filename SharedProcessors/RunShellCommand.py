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

from autopkglib import Processor, ProcessorError
import subprocess

__all__ = ["RunShellCommand"]


class RunShellCommand(Processor):
    """This processor runs a provided shell command, returning the arguments,
    return code, and what was sent to stdout and stderr."""

    description = __doc__
    input_variables = {
        "subprocess_args": {
            "description": "Array of arguments to run.",
            "required": True,
        },
        "subprocess_timeout": {
            "description": "A value in seconds that specifies how long to wait for the subprocess to complete before timing out.",
            "required": False,
        },
        "subprocess_fail_on_error": {
            "description": "Whether to throw an exception if the return code is not 0.",
            "required": False,
            "default": "True",
        },
        "subprocess_cwd": {
            "description": "Current working directory to run the command from. Defaults to %RECIPE_CACHE_DIR%.",
            "required": False
        }
    }
    output_variables = {
        "subprocess_args": {
            "description": "Array of the arguments that were run."
        },
        "subprocess_returncode": {
            "description": "The return code of the subprocess."
        },
        "subprocess_stdout": {
            "description": "The standard output of the subprocess.",
        },
        "subprocess_stderr": {
            "description": "The standard error of the subprocess.",
        },
    }

    def main(self):
        self.subprocess_args = self.env.get("subprocess_args")
        self.subprocess_timeout = self.env.get("subprocess_timeout", None)
        self.subprocess_fail_on_error = (str(self.env.get("subprocess_fail_on_error")).lower() == "true")
        self.subprocess_cwd = self.env.get("subprocess_cwd", self.env.get("RECIPE_CACHE_DIR"))

        self.output(f"subprocess_args: {' '.join(self.subprocess_args)}")
        result = subprocess.run(self.subprocess_args, shell=True, cwd=self.subprocess_cwd, capture_output=True, check=self.subprocess_fail_on_error, text=True, timeout=self.subprocess_timeout)

        self.env["subprocess_args"] = result.args
        self.env["subprocess_returncode"] = result.returncode
        self.output(f"subprocess_returncode: {self.env['subprocess_returncode']}")
        self.env["subprocess_stdout"] = result.stdout.rstrip('\n')
        self.output(f"subprocess_stdout: {self.env['subprocess_stdout']}")
        self.env["subprocess_stderr"] = result.stderr.rstrip('\n')
        self.output(f"subprocess_stderr: {self.env['subprocess_stderr']}")

if __name__ == "__main__":
    PROCESSOR = RunShellCommand()
    PROCESSOR.execute_shell()