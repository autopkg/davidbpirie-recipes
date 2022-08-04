#!/usr/local/autopkg/python
#
# Copyright 2022 David Pirie
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

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

__all__ = ["MicrosoftOneDriveVersioner"]


class MicrosoftOneDriveVersioner(Processor):
    """This processor generates a version string for Microsoft OneDrive
    to match the version used in Jamf Pro Patch Management.
    For example, when CFBundleShortVersionString is 22.065.0412
    and CFBundleVersion is 22065.0412.0004, Jamf Pro Patch Management
    has a version of 22.065.0412.0004.
    """

    input_variables = {
        "bundle_short_version": {
            "required": True,
            "description": "The version string from CFBundleShortVersionString"
        },
        "bundle_version": {
            "required": False,
            "description": "The version string from CFBundleVersion",
            "default": ""
        }
    }
    output_variables = {
        "version": {
            "description": "Generated version string"
        }
    }

    description = __doc__

    def main(self):
        """Main process."""
        bundle_short_version = self.env.get("bundle_short_version")
        self.output("bundle_short_version: {}".format(bundle_short_version))
        bundle_version = self.env.get("bundle_version")
        self.output("bundle_version: {}".format(bundle_version))
        first_period = bundle_short_version.index('.')
        bundle_short_version_reduced = bundle_short_version[:first_period] + bundle_short_version[first_period+1:]
        if (bundle_short_version_reduced in bundle_version) and (bundle_version.index(bundle_short_version_reduced) == 0):
            version = bundle_short_version + bundle_version[len(bundle_short_version_reduced):]
        else:
            version = bundle_short_version
        replacement_string = self.env.get("replacement_string")
        self.env["version"] = version
        self.output("Version: {}".format(version))


if __name__ == "__main__":
    PROCESSOR = MicrosoftOneDriveVersioner()
    PROCESSOR.execute_shell()