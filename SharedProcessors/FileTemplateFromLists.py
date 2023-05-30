#!/usr/local/autopkg/python
#
# Copyright 2023 David Pirie
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

from string import Template

from autopkglib import Processor, ProcessorError

__all__ = ["FileTemplateFromLists"]

class MyTemplate(Template):
    pattern = r"""
    %(?:
      (?P<escaped>%)                     | # Escape sequence of two delimiters
      (?P<named>[a-zA-Z_][a-zA-Z_0-9]*)  | # delimiter and a Python identifier
      (?P<braced>[a-zA-Z_][a-zA-Z_0-9]*) | # delimiter and a braced identifier
      (?P<invalid>)                        # Other ill-formed delimiter exprs
    )%
    """

class FileTemplateFromLists(Processor):
    """This processor uses Python's string.Template() class to substitute
    specified placeholders in a file with lists of strings, which are
    joined together with 'glue' values.
    It takes a dictionary (substitution_dict) as input, with the
    keys as the placeholders (without surrounding %s) to be substituted,
    and the values each being dictionaries themselves. Each value dictionary
    must contain an array of input_strings (strings), but can also optionally
    contain prefix, suffix, value_prefix, and value_suffix string values.
    If substitution_dict is not provided or empty, the processor
    completes without error and writes an output file identical to the source.
    substitution_dict example:
        <key>SUBSTITUTE_NAME_1</key>
        <dict>
            <key>input_strings</key>
            <array>
                <string>Input string 1</string>
                <string>Input string 2</string>
            </array>
            <key>prefix</key>
            <string>&lt;group&gt;</string>
            <key>suffix</key>
            <string>&lt;/group&gt;</string>
            <key>value_prefix</key>
            <string>&lt;value&gt;</string>
            <key>value_suffix</key>
            <string>&lt;/value&gt;</string>
        </dict>
    would result in the string:
        %SUBSTITUTE_NAME_1%
    in the input file being replaced with:
        <group><value>Input string 1</value><value>Input string 2</value></group>
    """

    input_variables = {
        "template_path": {
            "required": True,
            "description": "Path to the template file to apply the substitution on.",
        },
        "destination_path": {
            "required": True,
            "description": "Path where the file with the substitions performed will be written.",
        },
        "substitution_dict": {
            "required": False,
            "description": "Dictionary of inputs, with the key as the placeholder to be substituted. See Processor Description for more details."
        },
    }
    output_variables = {
    }

    description = __doc__


    def main(self):
        template_path = self.env["template_path"]
        destination_path = self.env["destination_path"]
        substitution_dict = self.env.get("substitution_dict")

        # Validate substitution_dict
        if not substitution_dict:
            substitution_dict = {}
        if type(substitution_dict) != dict:
            raise ProcessorError(f"substitution_dict must be a dictionary - {type(substitution_dict)} provided.")

        # Generate substitutions
        substitutions = {}
        for substitution_name, substitution_input in substitution_dict.items():
            # Validate key value
            if type(substitution_input) != dict:
                raise ProcessorError(f"substitution_dict values must all be dictionaries - {type(substitution_input)} provided for key {substitution_name}.")

            input_strings = substitution_input.get("input_strings")
            prefix = substitution_input.get("prefix")
            suffix = substitution_input.get("suffix")
            value_prefix = substitution_input.get("value_prefix")
            value_suffix = substitution_input.get("value_suffix")

            # Default to an empty substitution
            substitutions[substitution_name] = ""
            if input_strings:
                # Convert non-lists (eg strings) to a single-item list
                if type(input_strings) != list:
                    input_strings = [input_strings]

                # Concatenate each value, with value prefix/suffix
                for input_string in input_strings:
                    substitutions[substitution_name] += f"{str(value_prefix or '')}{input_string}{str(value_suffix or '')}"

                # Add prefix/suffix if not empty
                if result_output:
                    substitutions[substitution_name] = f"{str(prefix or '')}{result_output}{str(suffix or '')}"

            self.output(f"Substituting {substitution_name} with '{substitutions[substitution_name]}' if found.")

        # Read source template
        with open(template_path, 'r') as template_file:
            template_string = template_file.read()

        # Perform substitution
        substituted_string = MyTemplate(template_string).safe_substitute(substitutions)

        # Write the substituted text to the destination file
        with open(destination_path, 'w') as destination_file:
            destination_file.write(substituted_string)

        self.output(f"Templated {template_path} to {destination_path}.")


if __name__ == "__main__":
    PROCESSOR = FileTemplateFromLists()
    PROCESSOR.execute_shell()