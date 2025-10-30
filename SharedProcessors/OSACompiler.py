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


__all__ = ["OSACompiler"]


class OSACompiler(Processor):
    description = (
        "Compile AppleScripts and other OSA language scripts using osacompile."
    )
    input_variables = {
        "script_source": {
            "required": True,
            "description": "Path to the source file to be compiled.",
        },
        "compiled_script": {
            "required": True,
            "description": "Path to the compiled result. Will be deleted first if already exists.",
        },
    }
    output_variables = {}

    __doc__ = description

    def main(self):
        script_source: str = self.env["script_source"]
        compiled_script: str = self.env["compiled_script"]

        if os.path.exists(compiled_script):
            try:
                if os.path.isdir(compiled_script) and not os.path.islink(
                    compiled_script
                ):
                    shutil.rmtree(compiled_script)
                else:
                    os.unlink(compiled_script)
            except OSError as err:
                raise ProcessorError(
                    f"Can't remove existing {compiled_script}: {err.strerror}"
                )

        command_line_list = [
            "/usr/bin/osacompile",
            "-o",
            compiled_script,
            script_source,
        ]

        self.output(f'Running command: {" ".join(command_line_list)}')
        subprocess.call(command_line_list)


if __name__ == "__main__":
    processor = OSACompiler()
    processor.execute_shell()
