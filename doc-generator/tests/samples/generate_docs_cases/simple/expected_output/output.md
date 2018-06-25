---
title: Schema Documentation

search: true
---


# NetworkPort 1.1.0

A Network Port represents a discrete physical port capable of connecting to a network.

|     |     |     |
| --- | --- | --- |
| **Actions** *(v1.1+)* {} | object<br><br>*read-write* | The available actions for this resource. |
| **ActiveLinkTechnology** | string<br>(enum)<br><br>*read-write<br>(null)* | Network Port Active Link Technology. *See ActiveLinkTechnology in Property Details, below, for the possible values of this property.* |
| **AssociatedNetworkAddresses** [ ] | array (string, null)<br><br>*read-only* | The array of configured network addresses (MAC or WWN) that are associated with this Network Port, including the programmed address of the lowest numbered Network Device Function, the configured but not active address if applicable, the address for hardware port teaming, or other network addresses. |
| **Description** | <br><br>*read-only<br>(null)* |  |
| **EEEEnabled** | boolean<br><br>*read-write<br>(null)* | Whether IEEE 802.3az Energy Efficient Ethernet (EEE) is enabled for this network port. |
| **FlowControlConfiguration** | string<br>(enum)<br><br>*read-write<br>(null)* | The locally configured 802.3x flow control setting for this network port. *See FlowControlConfiguration in Property Details, below, for the possible values of this property.* |
| **FlowControlStatus** | string<br>(enum)<br><br>*read-only<br>(null)* | The 802.3x flow control behavior negotiated with the link partner for this network port (Ethernet-only). *See FlowControlStatus in Property Details, below, for the possible values of this property.* |
| **Id** | <br><br>*read-only* |  |
| **LinkStatus** | string<br>(enum)<br><br>*read-only<br>(null)* | The status of the link between this port and its link partner. *See LinkStatus in Property Details, below, for the possible values of this property.* |
| **Name** | <br><br>*read-only* |  |
| **NetDevFuncMaxBWAlloc** [ { | array<br><br>*read-write* | The array of maximum bandwidth allocation percentages for the Network Device Functions associated with this port. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**MaxBWAllocPercent** | number<br><br>*read-write<br>(null)* | The maximum bandwidth allocation percentage allocated to the corresponding network device function instance. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**NetworkDeviceFunction** | <br><br>*read-only* | Contains the members of this collection. |
| } ] |   |   |
| **NetDevFuncMinBWAlloc** [ { | array<br><br>*read-write* | The array of minimum bandwidth allocation percentages for the Network Device Functions associated with this port. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**MinBWAllocPercent** | number<br><br>*read-write<br>(null)* | The minimum bandwidth allocation percentage allocated to the corresponding network device function instance. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**NetworkDeviceFunction** | <br><br>*read-only* | Contains the members of this collection. |
| } ] |   |   |
| **Oem** | <br><br>*read-write* | This is the manufacturer/provider specific extension moniker used to divide the Oem object into sections. |
| **PhysicalPortNumber** | string<br><br>*read-only<br>(null)* | The physical port number label for this port. |
| **PortMaximumMTU** | number<br><br>*read-only<br>(null)* | The largest maximum transmission unit (MTU) that can be configured for this network port. |
| **SignalDetected** | boolean<br><br>*read-only<br>(null)* | Whether or not the port has detected enough signal on enough lanes to establish link. |
| **Status** | <br><br>*read-write<br>(null)* |  |
| **SupportedEthernetCapabilities** [ ] | array (string<br>(enum))<br><br>*read-only<br>(null)* | The set of Ethernet capabilities that this port supports. *See SupportedEthernetCapabilities in Property Details, below, for the possible values of this property.* |
| **SupportedLinkCapabilities** [ { | array<br><br>*read-write* | The self-described link capabilities of this port. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**LinkNetworkTechnology** | string<br>(enum)<br><br>*read-only<br>(null)* | The self-described link network technology capabilities of this port. *See LinkNetworkTechnology in Property Details, below, for the possible values of this property.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**LinkSpeedMbps** | number<br><br>*read-only<br>(null)* | The speed of the link in Mbps when this link network technology is active. |
| } ] |   |   |
| **WakeOnLANEnabled** | boolean<br><br>*read-write<br>(null)* | Whether Wake on LAN (WoL) is enabled for this network port. |

## Property Details

### ActiveLinkTechnology:


Network Port Active Link Technology.

| string | Description |
| --- | --- |
| Ethernet | The port is capable of connecting to an Ethernet network. |
| FibreChannel | The port is capable of connecting to a Fibre Channel network. |
| InfiniBand | The port is capable of connecting to an InfiniBand network. |

### FlowControlConfiguration:


The locally configured 802.3x flow control setting for this network port.

| string | Description |
| --- | --- |
| None | No IEEE 802.3x flow control is enabled on this port. |
| RX | IEEE 802.3x flow control may be initiated by the link partner. |
| TX | IEEE 802.3x flow control may be initiated by this station. |
| TX_RX | IEEE 802.3x flow control may be initiated by this station or the link partner. |

### FlowControlStatus:


The 802.3x flow control behavior negotiated with the link partner for this network port (Ethernet-only).

| string | Description |
| --- | --- |
| None | No IEEE 802.3x flow control is enabled on this port. |
| RX | IEEE 802.3x flow control may be initiated by the link partner. |
| TX | IEEE 802.3x flow control may be initiated by this station. |
| TX_RX | IEEE 802.3x flow control may be initiated by this station or the link partner. |

### LinkNetworkTechnology:


The self-described link network technology capabilities of this port.

| string | Description |
| --- | --- |
| Ethernet | The port is capable of connecting to an Ethernet network. |
| FibreChannel | The port is capable of connecting to a Fibre Channel network. |
| InfiniBand | The port is capable of connecting to an InfiniBand network. |

### LinkStatus:


The status of the link between this port and its link partner.

| string | Description |
| --- | --- |
| Down | The port is enabled but link is down. |
| Up | The port is enabled and link is good (up). |

### SupportedEthernetCapabilities:


The set of Ethernet capabilities that this port supports.

| string | Description |
| --- | --- |
| EEE | IEEE 802.3az Energy Efficient Ethernet (EEE) is supported on this port. |
| WakeOnLAN | Wake on LAN (WoL) is supported on this port. |
