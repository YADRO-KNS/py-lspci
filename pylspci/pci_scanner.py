import re
from typing import Union, List, TextIO

from .consoles import SSHConsole, LocalConsole
from .pci_parser import PCIParser, PCIDevice


class DoesNotExist(Exception):
    def __init__(self, **kwargs):
        self.arguments = kwargs

    def __str__(self):
        return 'Unable to find PCI Device matching: {query}'.format(query=str(self.arguments))


# noinspection PyBroadException
class ScannerPCI(object):
    def __init__(self, ip: str, username: str = None, password: str = None, port: int = 22, logfile: TextIO = None):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.logfile = logfile
        self._parser: Union[PCIParser, None] = None
        self._console: Union[SSHConsole, LocalConsole, None] = None

    def _get_console(self) -> Union[SSHConsole, LocalConsole]:
        if self._console is None:
            if self.ip == '127.0.0.1' or self.ip == 'localhost':
                self._console = LocalConsole(
                    password=self.password,
                    logfile=self.logfile
                )
            else:
                self._console = SSHConsole(
                    ip=self.ip,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    logfile=self.logfile
                )
        return self._console

    def _get_pci_addresses(self) -> List[str]:
        """
        Get all PCI addresses from target machine device
        :return: List of PCI addresses
        """
        result: List[str] = []
        try:
            command = "lspci -D | grep -o -e '[0-9A-Za-z]\{4\}:[0-9A-Za-z]\{2\}:[0-9A-Za-z]\{2\}.[0-9A-Za-z]\{1\}' | sed $'s/[^[:print:]]//g'"
            reply = self._get_console().run_command(command=command, sudo=True)
            for line in reply:
                if bool(re.match(r"""[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}.[0-9a-fA-F]""", line)):
                    result.append(line)
        except Exception as error:
            print(error)
        finally:
            return result

    def _scan_single_pci_device(self, address: str) -> Union[List[str], None]:
        """
        Scan PCI device
        :param address: Address target to scan
        :return: PCI device data or Nothing
        """
        result = None
        try:
            command = 'lspci -s {address} -D -vv'.format(address=address)
            result = self._get_console().run_command(command=command, sudo=True)
        except Exception as error:
            print(error)
        finally:
            return result

    def _get_pci(self, force_rescan: bool = False) -> List[PCIDevice]:
        if self._parser is None or force_rescan is True:
            self._parser = PCIParser(data=[self._scan_single_pci_device(address=address) for address in self._get_pci_addresses()])
        return self._parser.devices

    def pci_rescan(self) -> None:
        self._get_console().run_command(command="sh -c 'echo 1 > /sys/bus/pci/rescan'", sudo=True)

    def select(self, force_rescan: bool = False, **kwargs) -> List[PCIDevice]:
        if len(kwargs.items()) != 0:
            return [d for d in self._get_pci(force_rescan=force_rescan) if d.match(**kwargs)]
        else:
            return self._get_pci(force_rescan=force_rescan)

    def get(self, force_rescan: bool = False, **kwargs):
        result = self.select(force_rescan=force_rescan, **kwargs)
        if len(result) != 0:
            return result[0]
        else:
            raise DoesNotExist(**kwargs)

    def get_connected(self, parent: PCIDevice, force_rescan: bool = False) -> List[PCIDevice]:
        if parent.is_host_bridge:
            return [d for d in self._get_pci(force_rescan=force_rescan) if d.addr_dom == parent.addr_dom and d.addr_bus == parent.addr_bus and d != parent]
        elif parent.is_root_port or parent.is_downstream:
            return [d for d in self._get_pci(force_rescan=force_rescan) if d.addr_dom == parent.addr_dom and d.addr_bus == parent.pci_bus.secondary]
        elif parent.is_upstream:
            return [d for d in self._get_pci(force_rescan=force_rescan) if d.is_downstream and d.pci_bus.primary == parent.pci_bus.secondary]
        else:
            return []
