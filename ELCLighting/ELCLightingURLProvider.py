import json
import re
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import unquote, urlparse

from autopkglib import APLooseVersion as LooseVersion
from autopkglib import ProcessorError
from autopkglib.URLGetter import URLGetter

__all__ = ["ELCLightingURLProvider"]

DEFAULT_BASE_URL = "https://www.elclighting.com/support/knowledge-and-downloads/"
DEFAULT_PRODUCT_NAME = "dmxlanv4"
DEFAULT_PLATFORM = "macos"


class ELCLightingURLProvider(URLGetter):
    """Provides a download URL for ELC Lighting products from the downloads page."""

    description = __doc__
    input_variables: ClassVar[dict[str, dict[str, Any]]] = {
        "base_url": {
            "required": False,
            "description": f"Default is {DEFAULT_BASE_URL}.",
        },
        "product_name": {
            "required": False,
            "description": f"Options include {DEFAULT_PRODUCT_NAME}, dmxlanfix, fixturelibraryeditor, firmwareupdater, buddysetup, ac612editor, ac612usbdriver, triggereditor, showstorexlaneditor, usbupdate, sidekicktoointerface. Default is {DEFAULT_PRODUCT_NAME}.",
        },
        "platform": {
            "required": False,
            "description": f"One of: {DEFAULT_PLATFORM}, win. Default is {DEFAULT_PLATFORM}.",
        },
        "version": {
            "required": False,
            "description": "Provide the URL for a specific version. Provides the latest if not provided.",
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

    def main(self):
        # Use curl to fetch a URL and store the result in a variable.
        # Ideal for fetching structured data (JSON or XML), not ideal for storing large downloads
        base_url: str = self.env.get("base_url", DEFAULT_BASE_URL)
        product_name: str = self.env.get("product_name", DEFAULT_PRODUCT_NAME)
        platform: str = self.env.get("platform", DEFAULT_PLATFORM)
        version: str | None = self.env.get("version")

        # Download the source of the downloads page
        src_html: bytes = self.download(base_url)  # type: ignore

        # Extract the script block with id __NUXT_DATA__
        match: re.Match[str] | None = re.search(
            r'<script\b[^>]*\bid="__NUXT_DATA__"[^>]*>(.*?)</script>',
            src_html.decode("utf-8"),
            flags=re.DOTALL,
        )
        if not match:
            raise ProcessorError(
                "No match found in remote source for __NUXT_DATA__ regular expression."
            )

        # Interpret the script block as json, which translates the URLs
        data: list = json.loads(match.group(1))

        # Extract the URL elements that match the expected pattern
        product_urls = [
            x
            for x in data
            if isinstance(x, str)
            and x.startswith(
                f"https://downloads.elclighting.com/recources/software/{product_name}/{platform}/"
            )
        ]

        # Determine the version from each URL
        product_downloads: dict[str, str] = {}
        for product_url in product_urls:
            product_version: str = re.split(
                r"[ _]", Path(unquote(urlparse(product_url).path)).stem
            )[-1]
            if product_version in product_downloads:
                raise ProcessorError(f"Duplicate version {version} found in URLs.")
            product_downloads[product_version] = product_url

        # Determine the latest version
        if not version:
            version = max(product_downloads, key=LooseVersion)

        if version not in product_downloads:
            raise ProcessorError(f"Download URL for version {version} not found.")

        # Set the output_variables
        self.env["url"] = product_downloads[version]
        self.env["version"] = version

        self.output(f"Found {product_name} version {version}")
        self.output(f"Found URL {product_downloads[version]}")


if __name__ == "__main__":
    PROCESSOR = ELCLightingURLProvider()
    PROCESSOR.execute_shell()
