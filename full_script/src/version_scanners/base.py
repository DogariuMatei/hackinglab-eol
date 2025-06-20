from abc import ABC, abstractmethod

class VersionScanner(ABC):
    @abstractmethod
    def scan_versions(self, ips_file: str) -> str:
        """
        Scans versions for a given IP list.

        Args:
            ips_file (str): Path to the file containing IP addresses.

        Returns:
            str: the output file path
        """
        pass
