import re
from typing import Union, List, TextIO

from .consoles import SSHConsole, LocalConsole
from .pci_parser import PCIParser, PCIDevice


class DoesNotExist(Exception):
    def __init__(self, **kwargs):
        self.arguments = kwargs

    def __str__(self):
        return 'Unable to find PCI Device matching: {query}'.format(query=str(self.arguments))


class PCISelect(object):
    def __init__(self, devices: List[PCIDevice]):
        self._devices = devices
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._devices):
            self._index = 0
            raise StopIteration
        else:
            self._index += 1
            return self._devices[(self._index - 1)]

    def count(self) -> int:
        return len(self._devices)

    def select(self, **kwargs) -> 'PCISelect':
        if len(kwargs.items()) != 0:
            return PCISelect(devices=[d for d in self._devices if d.match(**kwargs)])
        else:
            return PCISelect(devices=self._devices)

    def get(self, **kwargs) -> Union[PCIDevice, None]:
        result = self.select(**kwargs)
        if result.count() != 0:
            return next(result)
        else:
            raise DoesNotExist(**kwargs)


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

    def select(self, force_rescan: bool = False, **kwargs) -> PCISelect:
        return PCISelect(devices=self._get_pci(force_rescan=force_rescan)).select(**kwargs)

    def get(self, force_rescan: bool = False, **kwargs) -> Union[PCIDevice, None]:
        return self.select(force_rescan=force_rescan).get(**kwargs)

    def get_connected(self, parent: PCIDevice, force_rescan: bool = False) -> PCISelect:
        if parent.is_host_bridge:
            return PCISelect(devices=[d for d in self.select(force_rescan=force_rescan, addr_dom=parent.addr_dom, addr_bus=parent.addr_bus) if d != parent])
        elif parent.is_root_port or parent.is_downstream:
            return PCISelect(devices=[d for d in self.select(force_rescan=force_rescan, addr_dom=parent.addr_dom, addr_bus=parent.pci_bus.secondary)])
        elif parent.is_upstream:
            return PCISelect(devices=[d for d in self.select(force_rescan=force_rescan, is_downstream=True) if d.pci_bus.primary == parent.pci_bus.secondary])
        else:
            return PCISelect(devices=[])
