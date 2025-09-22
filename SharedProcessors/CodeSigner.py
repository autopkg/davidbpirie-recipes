#!/usr/local/autopkg/python
#
# Copyright 2025 David Pirie
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


import plistlib
import subprocess
import os
import shutil

from autopkglib import Processor, ProcessorError


__all__ = ["CodeSigner"]


class CodeSigner(Processor):
    description = ( "Run codesign on a target." )
    input_variables = {
        "target_path": {
            "required": True,
            "description": "Path to the target to be signed."
        },
    }
    output_variables = {}

    __doc__ = description

    def main(self):
        target_path: str = self.env["target_path"]

        if not os.path.exists(target_path):
            raise ProcessorError(f"Target path {target_path} not found.")

        command_line_list = [
            "/usr/bin/codesign",
            "--force",
            "--sign",
            "-",
            "--timestamp=none",
            target_path
        ]

        self.output(f'Running command: {" ".join(command_line_list)}')
        subprocess.call(command_line_list)


if __name__ == '__main__':
    processor = CodeSigner()
    processor.execute_shell()