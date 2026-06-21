#!/usr/local/autopkg/python
#
# Copyright 2014 Timothy Sutton
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
"""See docstring for SampleSharedProcessor class"""

from __future__ import absolute_import

import re
from pathlib import Path

from autopkglib import Processor, ProcessorError
from autopkglib.Copier import Copier

__all__ = ["CiscoSecureClientHeadendPkgCollector"]


class CiscoSecureClientHeadendPkgCollector(Copier):
    """This processor collects the required pkgs from the dmg files
    inside the Cisco Secure Client headend deployment package, and
    creates an postinstall script that will install each of them.

    The generated postinstall will also copy a vpn management profile
    from Profiles/vpn/MgmtTun/VpnMgmtTunProfile.xml to
    /opt/cisco/secureclient/vpn/profile/mgmttun/VpnMgmtTunProfile.xml
    if it is found, and registers the ThousandEyes Endpoint Agent
    if csc_te_agent_connectstring is populated.
    """

    description = __doc__
    input_variables = {
        "scripts_dir": {
            "required": True,
            "description": "The pkg scripts dir where the result will be written.",
        },
        "csc_webdeploy_binaries": {
            "required": True,
            "description": "The path of the binaries folder from inside the headend package.",
        },
        "csc_modules": {
            "required": False,
            "default": [],
            "description": "A list of modules to collect the pkgs for. "
            + "core-vpn is always inserted first",
        },
        "csc_te_agent_connectstring": {
            "required": False,
            "default": "",
            "description": "If populated, the generated postinstall script will "
            + "attempt to use it to register the ThousandEyes Endpoint Agent.",
        },
        "csc_disable_launchagent": {
            "required": False,
            "default": "false",
            "description": "If set, the postinstall script will disable the "
            + "launchagent for the currently logged-in user.",
        },
        "csc_error_passthrough": {
            "required": False,
            "default": "false",
            "description": "If set, the postinstall script will return a non-0 "
            + "exit code if installer does for any of the individual pkgs.",
        },
    }
    output_variables = {}

    def main(self):
        """Do the work."""
        try:
            assert self.env is not None

            scripts_dir: Path = Path(self.env.get("scripts_dir", ""))
            self.output(msg=f"scripts_dir = {scripts_dir.absolute()}", verbose_level=1)
            if not scripts_dir.is_dir():
                raise ProcessorError(
                    f"Path for scripts_dir does not exist: {scripts_dir.absolute()}."
                )

            csc_webdeploy_binaries: Path = Path(
                self.env.get("csc_webdeploy_binaries", "")
            )
            self.output(
                msg=f"csc_webdeploy_binaries = {csc_webdeploy_binaries.absolute()}",
                verbose_level=1,
            )
            if not csc_webdeploy_binaries.is_dir():
                raise ProcessorError(
                    "Path for csc_webdeploy_binaries does not exist: "
                    + f"{csc_webdeploy_binaries.absolute()}"
                )

            csc_modules: list = list(dict.fromkeys(self.env.get("csc_modules", [])))
            if "core-vpn" in csc_modules:
                csc_modules.remove("core-vpn")
            csc_modules.insert(0, "core-vpn")
            self.output(
                msg=f"csc_modules = {', '.join(csc_modules)}",
                verbose_level=1,
            )

            csc_te_agent_connectstring: str = self.env.get(
                "csc_te_agent_connectstring", ""
            )
            self.output(
                msg=f"csc_te_agent_connectstring = {csc_te_agent_connectstring}",
                verbose_level=1,
            )

            csc_disable_launchagent: bool = str(
                self.env.get("csc_disable_launchagent", "false")
            ).lower() in ("1", "true", "yes")
            self.output(
                msg=f"csc_disable_launchagent = {csc_disable_launchagent}",
                verbose_level=1,
            )

            csc_error_passthrough: bool = str(
                self.env.get("csc_error_passthrough", "false")
            ).lower() in ("1", "true", "yes")
            self.output(
                msg=f"csc_error_passthrough = {csc_error_passthrough}",
                verbose_level=1,
            )

            binary_dmgs: list[Path] = [
                x
                for x in csc_webdeploy_binaries.iterdir()
                if x.is_file()
                and x.name.startswith("cisco-secure-client-macos-")
                and x.name.endswith("-webdeploy-k9.dmg")
            ]
            self.output(
                msg=f"binary_dmgs = {', '.join([str(x.absolute()) for x in binary_dmgs])}",
                verbose_level=1,
            )

            all_dmgs: set[Path] = set()
            all_pkg_names: list[str] = []
            for csc_module in csc_modules:
                self.output(msg=f"Processing module {csc_module}.", verbose_level=2)
                pattern = re.compile(
                    r"cisco-secure-client-macos-[\d\.]*-"
                    + csc_module
                    + "-webdeploy-k9.dmg"
                )
                module_dmgs: list[Path] = [
                    x for x in binary_dmgs if pattern.search(x.name)
                ]
                self.output(
                    msg=f"{csc_module} module_dmgs = {', '.join([str(x.absolute()) for x in module_dmgs])}",
                    verbose_level=2,
                )
                if not module_dmgs:
                    raise ProcessorError(
                        f"No module dmgs found for module {csc_module}."
                    )

                for module_dmg in module_dmgs:
                    self.output(
                        msg=f"Processing {csc_module} dmg {module_dmg}.",
                        verbose_level=2,
                    )
                    mount_point: Path = Path(self.mount(pathname=module_dmg))
                    self.output(
                        msg=f"mount_point = {mount_point.absolute()}", verbose_level=2
                    )
                    all_dmgs.add(module_dmg)

                    pkg_path: Path = mount_point / f"{module_dmg.stem}.pkg"
                    self.output(
                        msg=f"pkg_path = {pkg_path.absolute()}", verbose_level=2
                    )
                    if not pkg_path.exists():
                        raise ProcessorError(
                            f"Expected DMG to contain pkg {module_dmg.stem}.pkg, but not found."
                        )

                    self.copy(
                        source_item=pkg_path,
                        dest_item=scripts_dir / pkg_path.name,
                        overwrite=True,
                    )
                    all_pkg_names.append(pkg_path.name)
            self.output(
                msg=f"all_dmgs = {', '.join([str(x.absolute()) for x in all_dmgs])}",
                verbose_level=1,
            )
            self.output(
                msg=f"all_pkg_names = {', '.join(all_pkg_names)}", verbose_level=1
            )

            postinstall_script: str = '''#!/bin/zsh --no-rcs

################################################################################
#
# Installs Cisco Secure Client components using the Headend Deployment Package.
# See https://community.cisco.com/t5/security-knowledge-base/deploying-cisco-secure-client-on-macos-via-mdm-emm/ta-p/5546310
#
# If SRC_MGMT_PROFILE exists, copies it to DST_MGMT_PROFILE.
# Installs the selected component packages in order, starting with core-vpn.
# If CSC_TE_AGENT_CONNECTIONSTRING is populated, uses it to register
# the ThousandEyes Agent.
#
################################################################################

ROOT_DIR="$( cd -- "$(/usr/bin/dirname "$0")"; pwd -P )"
CSC_DIR=/opt/cisco/secureclient

SRC_MGMT_PROFILE="${ROOT_DIR}/Profiles/vpn/MgmtTun/VpnMgmtTunProfile.xml"
DST_MGMT_PROFILE="${CSC_DIR}/vpn/profile/mgmttun/VpnMgmtTunProfile.xml"

CSC_APP_NAME="Cisco Secure Client"
CSC_APP_DIR="/Applications/Cisco"
CSC_GUI_APP_DIR="${CSC_APP_DIR}/${CSC_APP_NAME}.app"
CSC_GUI_BINARY="${CSC_GUI_APP_DIR}/Contents/MacOS/${CSC_APP_NAME}"

CSC_TE_APP_DIR="${CSC_APP_DIR}/Cisco Secure Client - ThousandEyes Endpoint Agent.app"
CSC_TE_AGENT_BINARY="${CSC_TE_APP_DIR}/Contents/MacOS/csc_te_agent"
CSC_TE_AGENT_CONNECTIONSTRING="''' + csc_te_agent_connectstring + '"'
            for pkg_name in all_pkg_names:
                if csc_error_passthrough:
                    postinstall_script += (
                        """

echo Installing """
                        + pkg_name
                        + """
if ! /usr/sbin/installer -pkg "${ROOT_DIR}/"""
                        + pkg_name
                        + """" -target /; then
    echo Error: Installer failed for """
                        + pkg_name
                        + """
    exit 1
fi"""
                    )
                else:
                    postinstall_script += (
                        """

echo Installing """
                        + pkg_name
                        + """
/usr/sbin/installer -pkg "${ROOT_DIR}/"""
                        + pkg_name
                        + """" -target /"""
                    )
                postinstall_script += """

if [ -e "${SRC_MGMT_PROFILE}" ]; then
    echo "Copying Cisco Secure Client management VPN profile from ${SRC_MGMT_PROFILE} to ${DST_MGMT_PROFILE}"
    /bin/cp "${SRC_MGMT_PROFILE}" "${DST_MGMT_PROFILE}"
fi

if [ ! -z "{CSC_TE_AGENT_CONNECTIONSTRING}" ]; then
    echo "Registering ThousandEyes Agent"
    if [ ! -e "${CSC_TE_AGENT_BINARY}" ]; then
        echo "Error: ThousandEyes agent binary ${CSC_TE_AGENT_BINARY} not found"
        exit 2
    fi
    "${CSC_TE_AGENT_BINARY}" --register "${CSC_TE_AGENT_CONNECTIONSTRING}"
fi"""
            if csc_disable_launchagent:
                postinstall_script += """

CURRENTUSER_UID=$(echo "show State:/Users/ConsoleUser" | /usr/sbin/scutil | /usr/bin/awk '/ UID/ { print $3 }')
if [ -z "${CURRENTUSER_UID}" ] || [ "${CURRENTUSER_UID}" -eq 0 ] ; then
    echo "No user currently logged in"
else
    /bin/launchctl asuser ${CURRENTUSER_UID} /usr/bin/open -a "${CSC_GUI_APP_DIR}"
    /bin/launchctl asuser ${CURRENTUSER_UID} "${CSC_GUI_BINARY}" disableAutoStart
    /usr/bin/pkill -SIGTERM "${CSC_APP_NAME}"
fi"""
            postinstall_script += """

exit 0
"""

            postinstall_path: Path = scripts_dir / "postinstall"
            self.output(
                msg=f"postinstall_path = {postinstall_path.absolute()}", verbose_level=1
            )
            with open(postinstall_path, "w", encoding="utf-8") as postinstall_file:
                postinstall_file.write(postinstall_script)
            postinstall_path.chmod(mode=0o755)

            for dmg_path in all_dmgs:
                self.output(
                    msg=f"Unmounting dmg {dmg_path.absolute()}", verbose_level=1
                )
                self.unmount(dmg_path)
        except Exception as err:
            raise ProcessorError(err) from err


if __name__ == "__main__":
    PROCESSOR: Processor = CiscoSecureClientHeadendPkgCollector()
    PROCESSOR.execute_shell()
