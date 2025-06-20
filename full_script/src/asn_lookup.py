import os
import httpx
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import logging
logger = logging.getLogger(__name__)


class AsnLookup(ABC):
    """
    Abstract base class for ASN (Autonomous System Number) lookup providers.
    """

    @abstractmethod
    async def lookup_asn(self, asn: str) -> List[str]:
        """
        Lookup the IP prefixes associated with a given ASN.

        Args:
            asn (str): The ASN (e.g., "AS15169") to look up.

        Returns:
            List[str]: A list of IP prefixes associated with the ASN.
        """
        pass


def validate_asn(asn: str) -> str:
    """
    Validate that the ASN string starts with "AS" and has a minimum length.

    Args:
        asn (str): The ASN string to validate.

    Returns:
        str: The validated ASN string.

    Raises:
        ValueError: If the ASN is not in a valid format.
    """
    if not asn.startswith("AS") or len(asn) < 3:
        raise ValueError("Invalid ASN format")
    return asn


class HackerTargetAPI(AsnLookup):
    """
    Concrete implementation of AsnLookup using HackerTarget's API.
    """

    def __init__(self):
        """
        Create a new instance of HackerTargetAPI.
        """
        pass

    async def lookup_asn(self, asn: str) -> List[str]:
        """
        Query the HackerTarget API for IP prefixes associated with the given ASN.

        Args:
            asn (str): The ASN to look up.

        Returns:
            List[str]: A list of IP prefixes.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        url = f"https://api.hackertarget.com/aslookup/?q={asn}"
        logger.info(f"Requesting IP prefixes via {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

        lines = response.text.strip().splitlines()
        ip_prefixes = [line for line in lines[1:] if ':' not in line]
        if ip_prefixes[0] and ip_prefixes[0].startswith("No"):
            logger.error(f"Unable to find ip prefixes for {asn}, 'https://api.hackertarget.com/aslookup/?q={asn}'")
            exit(-1)
        logger.info(f"Found {len(ip_prefixes)} IP prefixes")
        return ip_prefixes


def read_ip_prefixes_from_file(path: Path) -> List[str]:
    """
    Read cached IP prefixes from a file.

    Args:
        path (Path): The path to the cache file.

    Returns:
        List[str]: A list of IP prefixes.

    Raises:
        IOError: If reading the file fails.
    """
    with open(path, mode='r') as f:
        contents = f.read()

    ip_prefixes = contents.strip().splitlines()
    logger.info("Using cached version of the IP prefixes")
    logger.info(f"Found {len(ip_prefixes)} IP prefixes")
    return ip_prefixes


class CachedAsnLookup:
    """
    An ASN lookup client that caches results to avoid redundant API calls.
    """

    def __init__(self, api: AsnLookup, cache_dir: str = "./cache/asn"):
        """
        Initialize a CachedAsnLookup instance.

        Args:
            api (AsnLookup): The ASN lookup provider to use.
            cache_dir (str): The directory to store cached results.
        """
        self.cache_dir = cache_dir
        self.api = api

    async def lookup_asn(self, asn: str) -> str:
        """
        Lookup an ASN, using a cached version if available.

        Args:
            asn (str): The ASN to look up.

        Returns:
            str: The path to the cached or newly saved file.

        Raises:
            Exception: If the lookup or file operations fail.
        """
        logger.info(f"Looking up {asn} for IP prefixes")
        os.makedirs(self.cache_dir, exist_ok=True)

        cache_path = Path(self.cache_dir) / f"{asn}.txt"
        if cache_path.exists():
            read_ip_prefixes_from_file(cache_path)
            return str(cache_path)

        result = await self.api.lookup_asn(asn)
        with open(cache_path, mode='w') as f:
            f.write("\n".join(result))

        return str(cache_path)
