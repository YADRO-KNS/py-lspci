# py-lspci
[![Actions Status](https://github.com/YADRO-KNS/py-lspci/workflows/Python%20application/badge.svg)](https://github.com/YADRO-KNS/py-lspci/actions)
![PyPI - Status](https://img.shields.io/pypi/status/py-lspci.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/py-lspci.svg)
![PyPI](https://img.shields.io/pypi/v/py-lspci.svg)
![PyPI - License](https://img.shields.io/pypi/l/py-lspci.svg)

----
py-lspci – parser for lspci output on remote or local UNIX machines. 
This package provides convenient interface to interact with lspci output in form of Python objects.

## Getting Started

### Prerequisites

py-lspci requires python 3.6 or newer versions to run. 
Also targets that you could interact with py-lspci must have [pciutils](http://mj.ucw.cz/sw/pciutils/) installed 
on them.

### Installing 

Cloning project from git repository
```bash
git clone https://github.com/YADRO-KNS/py-lspci.git
```

Installing from PyPi
```bash
pip3 install py-lspci
```

## Examples 

### Connection
First we have to establish connection to our target as user with sudo privileges:
```python
import pylspci

scanner = pylspci.ScannerPCI(ip='192.168.1.1', username='admin', password='pa$$w0rd')
```
In cases if we targeting local machine we need to provide user password if user isn't root:
```python
import pylspci

scanner = pylspci.ScannerPCI(ip='127.0.0.1', password='pa$$w0rd')
```
### Select
With *ScannerPCI* object now we can write requests to get data from lspci output, main tool to do that is 
**select** method, that will return *PCISelect* iterator object.
```
>>> scanner.select()
<pylspci.pci_scanner.PCISelect object at 0x7fa1dcda3940>
```
Select will return all PCI devices that matches select request.
```
>>> scanner.select().count()
22
>>> scanner.select(pci_address='0000:00:00.0').count()
1
```
For broad select requests you could use asterisk:
```
>>> scanner.select(type='Bridge').count()
0
>>> scanner.select(type='*Bridge').count()
10
```
Use multiple keyword arguments to specify search. 
You could search by any attributes or properties of *PCIDevice* class.:
```
>>> scanner.select(type='*Bridge', is_upstream=True).count()
1
```
With *PCISelect* object you could loop over PCI devices that matches search parameters:
```
>>> for device in scanner.select(is_downstream=True):
...     print(device)
...
0000:08:00.0 PCI bridge Intel Corporation JHL6240 Thunderbolt 3 Bridge [x4/x4][2.5GT/s/2.5GT/s]
0000:08:01.0 PCI bridge Intel Corporation JHL6240 Thunderbolt 3 Bridge [x4/x4][2.5GT/s/2.5GT/s]
0000:08:02.0 PCI bridge Intel Corporation JHL6240 Thunderbolt 3 Bridge [x4/x4][2.5GT/s/2.5GT/s]
```
Also you can chain your select requests:
```
>>> scanner.select(type='PCI bridge').count()
8
>>> scanner.select(type='PCI bridge').select(is_upstream=True).count()
1
```
### Get
Another search method is **get**. Basically it is the same select that will return first matching object
 instead of list of objects or will raise exception in case if there was no matches.
```
>>> print(scanner.get(type='*Host'))
0000:07:00.0 PCI bridge Intel Corporation [x2/x2][8GT/s/8GT/s]
>>> print(scanner.get(type='*Host', is_upstream=True))
Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File "/home/sergey/PycharmProjects/py-lspci/pylspci/pci_scanner.py", line 98, in get
    if parent.is_host_bridge:
pylspci.pci_scanner.DoesNotExist: Unable to find PCI Device matching: {'type': '*Host', 'is_upstream': True}
```
### Get Connected
Another tool is **get_connected** method of Scanner, that returns *PCISelect* with all devices connected to passed device.
For Host Bridge it will return all devices in Root Complex. For Upstream of PCI Bridge - all Downstreams. 
For Downstream or Root Ports - all connected Upstreams or Endpoints. End for Endpoints it will return empty list.

```
>>> scanner.get_connected(scanner.get(type='*Host')).count()
14
```
py-lspci uses cached value of lspci output, in case if you need to refresh that data, use *force_rescan* argument, 
for any of mentioned methods.
```
>>> scanner.select(force_rescan=True)
```
### PCI rescan procedure
Last but not least method of *ScannerPCI* is **pci_rescan** that causes full rescan of PCI bus on target machine.
Be careful with this one, because not all distros support proper PCI rescan.

## Versioning

We use [SemVer](http://semver.org/) for versioning.

## Authors

* **[Sergey Parshin](https://github.com/shooshp)** 

See also the list of [contributors](https://github.com/YADRO-KNS/py-lspci/graphs/contributors) who participated in this project.

## License
The code is available as open source under the terms of the [MIT License](LICENSE).