from typing import List, Union


class PCIBus(object):
    def __init__(self, data: str):
        self._data = data
        self.primary: Union[str, None] = None
        self.secondary: Union[str, None] = None
        self.subordinate: Union[str, None] = None
        self.sec_latency: Union[str, None] = None

        for entry in self._data.split(','):
            name = entry.split('=')[0].strip()
            if name == 'primary':
                self.primary = entry.split('=')[1].strip().upper()
            if name == 'secondary':
                self.secondary = entry.split('=')[1].strip().upper()
            if name == 'subordinate':
                self.subordinate = entry.split('=')[1].strip().upper()
            if name == 'sec-latency':
                self.sec_latency = entry.split('=')[1].strip().upper()


class PCILink(object):
    """
    Class placeholder for PCI device link parameters.
    """

    def __init__(self, lnkcap: str, lnksta: str) -> None:
        self.port = int(lnkcap.split(',')[0].split('#')[1])
        self.max_speed = lnkcap.split(',')[1].split(' ')[2]
        self.max_width = lnkcap.split(',')[2].split(' ')[2]

        self.speed = lnksta.split(',')[0].split(' ')[1]
        self.width = lnksta.split(',')[1].split(' ')[2]


class PCIDevice(object):
    """
    Mapper Class for PCI device.
    """

    def __init__(self, data: List[str]) -> None:
        self.data = data
        self.pci_address = self.data[0].split(' ')[0].strip()
        self.type = self.data[0].replace((self.pci_address + ' '), '').split(':')[0].strip()
        self.name = self.data[0].replace((self.pci_address + ' '), '').split(':')[1].strip()

        self.addr_dom = self.pci_address.split(':')[0].upper()
        self.addr_bus = self.pci_address.split(':')[1].upper()
        self.addr_num = self.pci_address.split(':')[2].split('.')[0].upper()
        self.addr_fun = self.pci_address.split(':')[2].split('.')[1].upper()

        self.control: Union[str, None] = None
        self.status: Union[str, None] = None
        self.capabilities: List[str] = []

        self.latency: Union[str, None] = None
        self.numa_node: Union[str, None] = None
        self.bus: Union[str, None] = None
        self.io_behind_bridge: Union[str, None] = None
        self.memory_behind_bridge: Union[str, None] = None
        self.prefetchable_memory_behind_bridge: Union[str, None] = None
        self.secondary_status: Union[str, None] = None
        self.bridge_ctl: Union[str, None] = None
        self.flags: Union[str, None] = None
        self.devcap: Union[str, None] = None
        self.devcap2: Union[str, None] = None
        self.devctl: Union[str, None] = None
        self.devctl2: Union[str, None] = None
        self.devsta: Union[str, None] = None
        self.lnkcap: Union[str, None] = None
        self.lnkctl: Union[str, None] = None
        self.lnkctl2: Union[str, None] = None
        self.lnksta: Union[str, None] = None
        self.lnksta2: Union[str, None] = None
        self.rootctl: Union[str, None] = None
        self.rootcap: Union[str, None] = None
        self.rootsta: Union[str, None] = None
        self.atomic_ops_cap: Union[str, None] = None
        self.atomic_ops_ctl: Union[str, None] = None
        self.transmit_margin: Union[str, None] = None
        self.compliance_deemphasis: Union[str, None] = None
        self.uesta: Union[str, None] = None
        self.uemsk: Union[str, None] = None
        self.uesvrt: Union[str, None] = None
        self.cesta: Union[str, None] = None
        self.cemsk: Union[str, None] = None
        self.aercap: Union[str, None] = None
        self.header_log: Union[str, None] = None
        self.root_cmd: Union[str, None] = None
        self.error_src: Union[str, None] = None
        self.interrupt: Union[str, None] = None
        self.address: Union[str, None] = None
        self.kernel_driver_in_use: Union[str, None] = None

        self.pci_link: Union[PCILink, None] = None
        self.pci_bus: Union[PCIBus, None] = None

        for entry in self.data[3:len(self.data) + 1]:
            name = entry.split(':')[0].replace(' ', '').replace('/', '').replace('[', '').replace(']', '').replace('-', '').lower()
            content = entry.replace(entry.split(':')[0] + ':', '').strip()

            if name != 'capabilities':
                is_assigned = False
                for field in self.__dict__.keys():
                    if field.replace('_', '') == name and getattr(self, field) is None:
                        setattr(self, field, content)
                        is_assigned = True

                if is_assigned is False:
                    setattr(self, 'aux_' + name, content)

            elif name == 'capabilities':
                self.capabilities.append(content)

            elif name == 'bus':
                self.bus = PCIBus(data=content)

        if self.lnkcap is not None and self.lnksta is not None:
            self.pci_link = PCILink(self.lnkcap, self.lnksta)

        if self.bus is not None:
            self.pci_bus = PCIBus(self.bus)

    def match(self, **kwargs) -> bool:
        result = True
        for key, value in kwargs.items():
            if key in self.__dir__() and result is not False:
                if type(value) is str and value.startswith('*') and type(getattr(self, key)) is str:
                    result = (value.replace('*', '').upper() in getattr(self, key).upper())
                else:
                    result = (value == getattr(self, key))
            else:
                result = False
        return result

    def _check_capabilities(self, value: str) -> bool:
        result = False
        for line in self.capabilities:
            if value in line:
                result = True
        return result

    @property
    def device_serial_number(self) -> Union[str, None]:
        result = None
        for line in self.capabilities:
            if 'Device Serial Number' in line:
                result = line.split('Device Serial Number')[-1].strip()
        return result

    @property
    def subsystem(self) -> Union[str, None]:
        result = None
        for line in self.capabilities:
            if 'Subsystem:' in line:
                result = line.split('Subsystem:')[-1].strip()
        return result

    @property
    def is_host_bridge(self) -> bool:
        return self.type == 'Host bridge'

    @property
    def is_root_port(self) -> bool:
        return self._check_capabilities(value='Root Port')

    @property
    def is_downstream(self) -> bool:
        return self._check_capabilities(value='Downstream Port') and self.type == 'PCI bridge'

    @property
    def is_upstream(self) -> bool:
        return self._check_capabilities(value='Upstream Port') and self.type == 'PCI bridge'

    @property
    def is_endpoint(self) -> bool:
        return not self.is_host_bridge and not self.is_root_port and not self.is_upstream and not self.is_downstream

    def __str__(self):
        if self.pci_link is not None:
            link = '[{width}/{max_width}][{speed}/{max_speed}]'.format(
                width=self.pci_link.width, max_width=self.pci_link.max_width, speed=self.pci_link.speed, max_speed=self.pci_link.max_speed)
        else:
            link = ''
        return '{address} {type} {name} {link}'.format(address=self.pci_address, type=self.type, name=self.name, link=link)


# noinspection PyBroadException
class PCIParser(object):
    def __init__(self, data: List[List[str]]) -> None:
        self.data = data
        self.devices: List[PCIDevice] = []
        self.process_data(data=self.data)

    def process_data(self, data: List[List[str]]) -> None:
        for entry in data:
            result = self.parce_single_device(data=entry)
            if result is not None:
                self.devices.append(PCIDevice(data=result))

    @staticmethod
    def parce_single_device(data: List[str]) -> Union[List[str], None]:
        result = None
        if data is not None:
            temp_list = []
            line_counter = 0
            for line in data:
                line = line.replace('\t', '').replace('\r', '').replace('\n', '')
                if len(line) > 4 and 'pcilib:' not in line:
                    temp_list.append(line)
                    if ':' not in line and 'lspci' not in line:
                        temp_list[(line_counter - 1):(line_counter + 1)] = [' '.join(temp_list[(line_counter - 1):(line_counter + 1)])]
                    else:
                        line_counter += 1

            if len(temp_list) != 0:
                result = temp_list
        return result
