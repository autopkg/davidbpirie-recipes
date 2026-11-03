import json
from typing import Any, ClassVar
from urllib.parse import quote

from autopkglib import APLooseVersion as LooseVersion
from autopkglib import ProcessorError
from autopkglib.URLGetter import URLGetter

__all__ = ["EpsonURLProvider"]

EPSON_API_URL = "https://download-center.epson.com/api/v1/"
COOKIE_GA = "GA1.1.123456789.1234567890"
HEADER_ACCEPT_LANGUAGE = "en-GB,en;q=0.9,en-US;q=0.8,en-AU;q=0.7"
HEADER_SEC_FETCH_SITE = "same-origin"
HEADER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36 Edg/156.0.0.0"

DEFAULT_OS_CODE = "MAC27"
DEFAULT_LANGUAGE_CODE = "en"
DEFAULT_REGION_CODE = "US"
DEFAULT_CATEGORY_NAME = "Drivers"
DEFAULT_DOWNLOAD_TYPE_NAME = "Printer Driver"


class EpsonURLProvider(URLGetter):
    """Provides a download URL for Epson products from the Epson Download Center page."""

    description = __doc__
    input_variables: ClassVar[dict[str, dict[str, Any]]] = {
        "device_id": {
            "required": True,
            "description": "Epson device id (product name) to find a download for. Check for a valid device id at https://download-center.epson.com/.",
        },
        "os_code": {
            "required": False,
            "description": f"OS code used to search e.g. MAC15, MAC26, MAC27. Defaults to {DEFAULT_OS_CODE}.",
        },
        "language_code": {
            "required": False,
            "description": f"Language code used to search e.g. en. Defaults to {DEFAULT_LANGUAGE_CODE}.",
        },
        "region_code": {
            "required": False,
            "description": f"Region code used to search e.g. US, GB, AU. Defaults to {DEFAULT_REGION_CODE}.",
        },
        "category_name": {
            "required": False,
            "description": f"Name of the download category to filter the available downloads to. Defaults to {DEFAULT_CATEGORY_NAME}.",
        },
        "download_type_name": {
            "required": False,
            "description": f"Name of the download type to filter the available downloads to. Defaults to {DEFAULT_DOWNLOAD_TYPE_NAME}.",
        },
    }
    output_variables: ClassVar[dict[str, dict[str, Any]]] = {
        "url": {
            "description": "URL to the latest release of the product.",
        },
        "version": {
            "description": "Version of the latest release of the product.",
        },
    }

    def query_api_with_curl(self, url_suffix: str) -> Any:
        curl_cmd = super().prepare_curl_cmd()
        curl_cmd.extend(["--cookie", f"_ga={COOKIE_GA}"])
        curl_cmd.extend(["--header", f"accept-language: {HEADER_ACCEPT_LANGUAGE}"])
        curl_cmd.extend(["--header", f"sec-fetch-site: {HEADER_SEC_FETCH_SITE}"])
        curl_cmd.extend(["--header", f"user-agent: {HEADER_USER_AGENT}"])
        curl_cmd.append(f"{EPSON_API_URL}{url_suffix}")
        return json.loads(super().download_with_curl(curl_cmd=curl_cmd, text=True))

    def main(self):
        device_id: str = self.env.get("device_id", "")
        os_code: str = self.env.get("os_code", DEFAULT_OS_CODE)
        language_code: str = self.env.get("language_code", DEFAULT_LANGUAGE_CODE)
        region_code: str = self.env.get("region_code", DEFAULT_REGION_CODE)
        category_name: str = self.env.get("category_name", DEFAULT_CATEGORY_NAME)
        download_type_name: str = self.env.get(
            "download_type_name", DEFAULT_DOWNLOAD_TYPE_NAME
        )

        # Validate os_code and retrieve os_name
        os_response: list[dict] = self.query_api_with_curl(url_suffix="os/")
        self.output(msg="Epson API response for os:", verbose_level=4)
        self.output(msg=json.dumps(os_response, indent=None), verbose_level=4)
        os_name: str = ""
        for os_item in os_response:
            if os_item.get("code") == os_code:
                os_name = os_item.get("name", "")
                break
        else:
            raise ProcessorError(
                f"Provided value for os_code ({os_code}) not found in Epson's API."
            )
        self.output(msg=f"Validated os_code {os_code} ({os_name}).", verbose_level=2)

        # Validate region_code and retrieve region_name
        region_response: list[dict] = self.query_api_with_curl(
            url_suffix=f"region/?language={language_code}"
        )
        self.output(msg="Epson API response for region:", verbose_level=4)
        self.output(msg=json.dumps(region_response, indent=None), verbose_level=4)
        region_name: str = ""
        for region_item in region_response:
            if region_item.get("code") == region_code:
                region_name = region_item.get("name", "")
                break
        else:
            raise ProcessorError(
                f"Provided value for region_code ({region_code}) not found in Epson's API."
            )
        self.output(
            msg=f"Validated region_code {region_code} ({region_name}).", verbose_level=2
        )

        # Validate category_name and retrieve category_code
        cti_category_response: list[dict] = self.query_api_with_curl(
            url_suffix=f"cti_category/?language={language_code}"
        )
        self.output(msg="Epson API response for cti_category:", verbose_level=4)
        self.output(msg=json.dumps(cti_category_response, indent=None), verbose_level=4)
        category_code: str = ""
        for cti_category in cti_category_response:
            if cti_category["name"] == category_name:
                category_code = cti_category["code"]
                break
        else:
            raise ProcessorError(
                f"Provided value for category_name ({category_name}) not found in Epson's API."
            )
        self.output(
            f"Validated category_name {category_name} ({category_code}).",
            verbose_level=2,
        )

        # Validate download_type_name and retrieve cti_code
        cti_response: list[dict] = self.query_api_with_curl(
            url_suffix=f"cti/?language={language_code}"
        )
        self.output(msg="Epson API response for cti:", verbose_level=4)
        self.output(msg=json.dumps(cti_response, indent=None), verbose_level=4)
        cti_code: str = ""
        for cti in cti_response:
            if cti["category"] == category_code and cti["name"] == download_type_name:
                cti_code = cti["code"]
                break
        else:
            raise ProcessorError(
                f"Provided value of download_type_name ({download_type_name}) not found in Epson's API under the provided category ({category_name})."
            )
        self.output(
            f"Validated download_type_name {download_type_name} ({cti_code}).",
            verbose_level=2,
        )

        # Retrieving modules for device_id, os_code, and region_code
        modules_response: dict = self.query_api_with_curl(
            url_suffix=f"modules/?device_id={quote(device_id)}&os={os_code}&region={region_code}&language={language_code}"
        )
        self.output(
            msg="Epson API response for modules (device_id: {device_id}; os_code: {os_code}; region: {region_code}):",
            verbose_level=4,
        )
        self.output(msg=json.dumps(modules_response, indent=None), verbose_level=4)

        # Filtering modules to find all for category_code and cti_code
        modules: dict[str, dict] = {}
        for item in modules_response.get("items", []):
            if (
                item.get("version")
                and item.get("url")
                and item.get("cti_category") == category_code
                and item.get("cti") == cti_code
            ):
                if item.get("version") in modules:
                    raise ProcessorError(
                        f"Duplicate modules found with the same version: {item['version']}"
                    )
                modules[item.get("version")] = item
        if not modules:
            raise ProcessorError(
                f"No modules found matching device_id ({device_id}), os ({os_code}), and region ({region_code})."
            )
        self.output(f"{len(modules)} modules found.", verbose_level=2)

        # Determine latest version
        latest_version: str = max(modules, key=LooseVersion)

        # Set the output_variables
        self.env["url"] = modules[latest_version]["url"]
        self.env["version"] = latest_version

        self.output(
            f"Found {device_id} {os_name} {category_name}->{download_type_name} version {self.env['version']}: {self.env['url']}"
        )


if __name__ == "__main__":
    PROCESSOR = EpsonURLProvider()
    PROCESSOR.execute_shell()
