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

from __future__ import absolute_import

import subprocess

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error
import plistlib
import re

__all__ = ["FirstActivePackageInChoice"]


class FirstActivePackageInChoice(Processor):
    """This processor generates a plist using installer -showChoicesXML, then
    looks through the plist for the specified choice identifier, and returns
    the first package name listed in pathsOfActivePackagesInChoice after
    stripping off the source pkg path."""

    description = __doc__
    input_variables = {
        "choices_pkg_path": {
            "description": "Path to the source pkg.",
            "required": True,
        },
        "desired_choice": {
            "description": ("The desired choice identifier."),
            "required": True,
        },
    }
    output_variables = {
        "first_active_pkg": {"description": "The name of the first pkg in pathsOfActivePackagesInChoice."}
    }

    def output_showchoicesxml(self, choices_pkg_path: str):
        """Invoke the installer showChoicesXML command and return
        the contents"""
        (choices_result, error) = subprocess.Popen(
            ["/usr/sbin/installer", "-showChoicesXML", "-pkg", choices_pkg_path],
            stdout=subprocess.PIPE,
        ).communicate()
        if choices_result:
            try:
                choices_plist = bytearray(
                    re.search(
                        r"(?s)<\?xml.*</plist>", choices_result.decode("utf-8")
                    ).group(),
                    "utf-8",
                )
                choices_list = plistlib.loads(choices_plist)
            except Exception as err:
                raise ProcessorError(
                    f"Unexpected error parsing manifest as a plist: '{err}'"
                )
            child_items = choices_list[0]["childItems"]
            return child_items
        if error:
            raise ProcessorError("No Plist generated from installer command")

    def get_child_with_identifier(self, child_items: list, desired_choice: str):
        for child_item in child_items:
            if child_item["childItems"]:
                result = self.get_child_with_identifier(child_items=child_item["childItems"], desired_choice=desired_choice)
                if result:
                    return result
            if child_item["choiceIdentifier"] == desired_choice:
                return child_item
        return None

    def main(self):
        choices_pkg_path = self.env.get("choices_pkg_path")
        desired_choice = self.env.get("desired_choice")

        child_items = self.output_showchoicesxml(choices_pkg_path)
        desired_child_item = self.get_child_with_identifier(child_items=child_items, desired_choice=desired_choice)
        first_active_pkg = desired_child_item["pathsOfActivePackagesInChoice"][0].split("#",1)[1]
        self.env["first_active_pkg"] = first_active_pkg
        self.output(f"first_active_pkg: {self.env['first_active_pkg']}")

if __name__ == "__main__":
    PROCESSOR = FirstActivePackageInChoice()
    PROCESSOR.execute_shell()