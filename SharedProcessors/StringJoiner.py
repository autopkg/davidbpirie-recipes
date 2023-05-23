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

from autopkglib import Processor, ProcessorError

__all__ = ["StringJoiner"]


class StringJoiner(Processor):
    """This processor joins lists of strings together into a single
    string. It takes a dictionary (string_joiner_dict) as input, with the
    keys as the names of the variables to be set, and the values each
    being dictionaries themselves. Each value dictionary must contain
    an array of input_strings (strings), but can also optionally contain
    prefix, suffix, value_prefix, and value_suffix string values.
    If string_joiner_dict is not provided or empty, the processor
    completes without error and without making any changes.
    Example:
        <key>output_var_name</key>
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
        <group><value>Input string 1</value><value>Input string 2</value></group>
    being assigned to output_var_name.
    """

    input_variables = {
        "string_joiner_dict": {
            "required": False,
            "description": "Dictionary of inputs, with the key as the resulting output variable name. See Processor Description for more details."
        }
    }
    output_variables = {
        "result_output_var_name": {
            "description": "The result value. Note the actual name of the variable(s) matches the input string_joiner_dict keys."
        }
    }

    description = __doc__


    def main(self):
        string_joiner_dict = self.env.get("string_joiner_dict")

        if not string_joiner_dict:
            return
        if type(string_joiner_dict) != dict:
            raise ProcessorError(f"string_joiner_dict must be a dictionary - {type(string_joiner_dict)} provided.")

        for result_output_var_name, string_joiner_input in string_joiner_dict.items():
            if type(string_joiner_input) != dict:
                raise ProcessorError(f"string_joiner_dict values must all be dictionaries - {type(string_joiner_input)} provided for key {result_output_var_name}.")

            input_strings = string_joiner_input.get("input_strings")
            prefix = string_joiner_input.get("prefix")
            suffix = string_joiner_input.get("suffix")
            value_prefix = string_joiner_input.get("value_prefix")
            value_suffix = string_joiner_input.get("value_suffix")

            result_output = ""

            if input_strings:
                if type(input_strings) != list:
                    input_strings = [input_strings]

                for input_string in input_strings:
                    result_output += f"{str(value_prefix or '')}{input_string}{str(value_suffix or '')}"

                if result_output:
                    result_output = f"{str(prefix or '')}{result_output}{str(suffix or '')}"

            self.env[result_output_var_name] = result_output
            self.output(f"{result_output_var_name}: {self.env[result_output_var_name]}")


if __name__ == "__main__":
    PROCESSOR = StringJoiner()
    PROCESSOR.execute_shell()