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


import plistlib
import subprocess
import os

from autopkglib import Processor, ProcessorError


__all__ = ["FlatToDistPkg"]


class FlatToDistPkg(Processor):
    description = ( "Converts a flat package to a distribution-style package." )
    input_variables = {
        "pkg_path": {
            "required": True,
            "description": "Path to the flat package to be converted."
        }
    }
    output_variables = {
        "pkg_path": {
             "description": "Path to the distribution-style pacakge."
        }
   }

    __doc__ = description

    def main(self):

    	# rename flat package so that we can slot the distribution-style package into place
        pkg_dir = os.path.dirname( self.env[ "pkg_path" ] )
        pkg_base_name = os.path.basename( self.env[ "pkg_path" ] )
        ( pkg_name_no_extension, pkg_extension ) = os.path.splitext( pkg_base_name )

        flat_pkg_path = os.path.join( pkg_dir, pkg_name_no_extension + "-flat" + pkg_extension )
        os.rename( self.env[ "pkg_path" ], flat_pkg_path )

        command_line_list = [ "/usr/bin/productbuild", \
                              "--package", \
                              flat_pkg_path, \
                              self.env[ "pkg_path" ] ]

        print(command_line_list)

        # print command_line_list
        subprocess.call( command_line_list )



if __name__ == '__main__':
    processor = FlatToDistPkg()
    processor.execute_shell()