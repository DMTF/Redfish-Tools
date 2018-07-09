---
title: Schema Documentation

search: true
---


# NetworkDeviceFunction 1.2.1

A Network Device Function represents a logical interface exposed by the network adapter.

|     |     |     |
| --- | --- | --- |
| **@odata.etag** | string<br><br>*read-only* | The current ETag of the resource. |
| **Actions** *(v1.1.1+)* {} | object | The available actions for this resource. |
| **AssignablePhysicalPorts** [ { | array<br><br>*read-only* | The array of physical port references that this network device function may be assigned to. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**@odata.id** | string<br><br>*read-only* | Link to a NetworkPort resource. See the Links section and the *NetworkPort* schema for details. |
| } ] |   |   |
| **BootMode** | string<br>(enum)<br><br>*read-write<br>(null)* | The boot mode configured for this network device function. *See BootMode in Property Details, below, for the possible values of this property.* |
| **Description** | string<br><br>*read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schema definitions. |
| **DeviceEnabled** | boolean<br><br>*read-write<br>(null)* | Whether the network device function is enabled. |
| **Ethernet** { | object<br><br>*<br>(null)* | Ethernet. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**MACAddress** | string<br><br>*read-write<br>(null)* | This is the currently configured MAC address of the (logical port) network device function. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**MTUSize** | number<br><br>*read-write<br>(null)* | The Maximum Transmission Unit (MTU) configured for this network device function. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PermanentMACAddress** | string<br><br>*read-only<br>(null)* | This is the permanent MAC address assigned to this network device function (physical function). |
| } |   |   |
| **FibreChannel** { | object<br><br>*<br>(null)* | Fibre Channel. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**AllowFIPVLANDiscovery** | boolean<br><br>*read-write<br>(null)* | Whether the FCoE Initialization Protocol (FIP) is used for populating the FCoE VLAN Id. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**BootTargets** [ { | array<br><br>*read-write* | An array of Fibre Channel boot targets configured for this network device function. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**BootPriority** | number<br><br>*read-write<br>(null)* | The relative priority for this entry in the boot targets array. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**LUNID** | string<br><br>*read-write<br>(null)* | The Logical Unit Number (LUN) ID to boot from on the device referred to by the corresponding WWPN. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**WWPN** | string<br><br>*read-write<br>(null)* | The World-Wide Port Name to boot from. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;} ] |   |   |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**FCoEActiveVLANId** | number<br><br>*read-only<br>(null)* | The active FCoE VLAN ID. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**FCoELocalVLANId** | number<br><br>*read-write<br>(null)* | The locally configured FCoE VLAN ID. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PermanentWWNN** | string<br><br>*read-only<br>(null)* | This is the permanent WWNN address assigned to this network device function (physical function). |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PermanentWWPN** | string<br><br>*read-only<br>(null)* | This is the permanent WWPN address assigned to this network device function (physical function). |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**WWNN** | string<br><br>*read-write<br>(null)* | This is the currently configured WWNN address of the network device function (physical function). |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**WWNSource** | string<br>(enum)<br><br>*read-write<br>(null)* | The configuration source of the WWNs for this connection (WWPN and WWNN). *See WWNSource in Property Details, below, for the possible values of this property.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**WWPN** | string<br><br>*read-write<br>(null)* | This is the currently configured WWPN address of the network device function (physical function). |
| } |   |   |
| **Id** | string<br><br>*read-only required* | Uniquely identifies the resource within the collection of like resources. |
| **iSCSIBoot** { | object<br><br>*<br>(null)* | iSCSI Boot. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**AuthenticationMethod** | string<br>(enum)<br><br>*read-write<br>(null)* | The iSCSI boot authentication method for this network device function. *See AuthenticationMethod in Property Details, below, for the possible values of this property.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**CHAPSecret** | string<br><br>*read-write<br>(null)* | The shared secret for CHAP authentication. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**CHAPUsername** | string<br><br>*read-write<br>(null)* | The username for CHAP authentication. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**InitiatorDefaultGateway** | string<br><br>*read-write<br>(null)* | The IPv6 or IPv4 iSCSI boot default gateway. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**InitiatorIPAddress** | string<br><br>*read-write<br>(null)* | The IPv6 or IPv4 address of the iSCSI initiator. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**InitiatorName** | string<br><br>*read-write<br>(null)* | The iSCSI initiator name. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**InitiatorNetmask** | string<br><br>*read-write<br>(null)* | The IPv6 or IPv4 netmask of the iSCSI boot initiator. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**IPAddressType** | string<br>(enum)<br><br>*read-write<br>(null)* | The type of IP address (IPv6 or IPv4) being populated in the iSCSIBoot IP address fields. *See IPAddressType in Property Details, below, for the possible values of this property.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**IPMaskDNSViaDHCP** | boolean<br><br>*read-write<br>(null)* | Whether the iSCSI boot initiator uses DHCP to obtain the iniator name, IP address, and netmask. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**MutualCHAPSecret** | string<br><br>*read-write<br>(null)* | The CHAP Secret for 2-way CHAP authentication. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**MutualCHAPUsername** | string<br><br>*read-write<br>(null)* | The CHAP Username for 2-way CHAP authentication. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PrimaryDNS** | string<br><br>*read-write<br>(null)* | The IPv6 or IPv4 address of the primary DNS server for the iSCSI boot initiator. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PrimaryLUN** | number<br><br>*read-write<br>(null)* | The logical unit number (LUN) for the primary iSCSI boot target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PrimaryTargetIPAddress** | string<br><br>*read-write<br>(null)* | The IP address (IPv6 or IPv4) for the primary iSCSI boot target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PrimaryTargetName** | string<br><br>*read-write<br>(null)* | The name of the iSCSI primary boot target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PrimaryTargetTCPPort** | number<br><br>*read-write<br>(null)* | The TCP port for the primary iSCSI boot target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PrimaryVLANEnable** | boolean<br><br>*read-write<br>(null)* | This indicates if the primary VLAN is enabled. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PrimaryVLANId** | number<br><br>*read-write<br>(null)* | The 802.1q VLAN ID to use for iSCSI boot from the primary target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**RouterAdvertisementEnabled** | boolean<br><br>*read-write<br>(null)* | Whether IPv6 router advertisement is enabled for the iSCSI boot target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**SecondaryDNS** | string<br><br>*read-write<br>(null)* | The IPv6 or IPv4 address of the secondary DNS server for the iSCSI boot initiator. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**SecondaryLUN** | number<br><br>*read-write<br>(null)* | The logical unit number (LUN) for the secondary iSCSI boot target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**SecondaryTargetIPAddress** | string<br><br>*read-write<br>(null)* | The IP address (IPv6 or IPv4) for the secondary iSCSI boot target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**SecondaryTargetName** | string<br><br>*read-write<br>(null)* | The name of the iSCSI secondary boot target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**SecondaryTargetTCPPort** | number<br><br>*read-write<br>(null)* | The TCP port for the secondary iSCSI boot target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**SecondaryVLANEnable** | boolean<br><br>*read-write<br>(null)* | This indicates if the secondary VLAN is enabled. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**SecondaryVLANId** | number<br><br>*read-write<br>(null)* | The 802.1q VLAN ID to use for iSCSI boot from the secondary target. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**TargetInfoViaDHCP** | boolean<br><br>*read-write<br>(null)* | Whether the iSCSI boot target name, LUN, IP address, and netmask should be obtained from DHCP. |
| } |   |   |
| **MaxVirtualFunctions** | number<br><br>*read-only<br>(null)* | The number of virtual functions (VFs) that are available for this Network Device Function. |
| **Name** | string<br><br>*read-only required* | The name of the resource or array element. |
| **NetDevFuncCapabilities** *(v1.0.2+)* [ ] | array (string<br>(enum))<br><br>*read-only<br>(null)* | Capabilities of this network device function. *See NetDevFuncCapabilities in Property Details, below, for the possible values of this property.* |
| **NetDevFuncType** *(v1.0.2+)* | string<br>(enum)<br><br>*read-write<br>(null)* | The configured capability of this network device function. *See NetDevFuncType in Property Details, below, for the possible values of this property.* |
| **Oem** {} | object | This is the manufacturer/provider specific extension moniker used to divide the Oem object into sections. See the *Resource* schema for details on this property. |
| **PhysicalPortAssignment** { | object | The physical port that this network device function is currently assigned to. See the *NetworkPort* schema for details on this property. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**@odata.id** | string<br><br>*read-only* | Link to a NetworkPort resource. See the Links section and the *NetworkPort* schema for details. |
| } |   |   |
| **Status** {} | object<br><br>*<br>(null)* | This type describes the status and health of a resource and its children. See the *Resource* schema for details on this property. |
| **VirtualFunctionsEnabled** | boolean<br><br>*read-only<br>(null)* | Whether Single Root I/O Virtualization (SR-IOV) Virual Functions (VFs) are enabled for this Network Device Function. |

## Property Details

### AuthenticationMethod:


The iSCSI boot authentication method for this network device function.

| string | Description |
| --- | --- |
| CHAP | iSCSI Challenge Handshake Authentication Protocol (CHAP) authentication is used. |
| MutualCHAP | iSCSI Mutual Challenge Handshake Authentication Protocol (CHAP) authentication is used. |
| None | No iSCSI authentication is used. |

### BootMode:


The boot mode configured for this network device function.

| string | Description |
| --- | --- |
| Disabled | Do not indicate to UEFI/BIOS that this device is bootable. |
| FibreChannel | Boot this device using the embedded Fibre Channel support and configuration.  Only applicable if the NetworkDeviceFunctionType is set to FibreChannel. |
| FibreChannelOverEthernet | Boot this device using the embedded Fibre Channel over Ethernet (FCoE) boot support and configuration.  Only applicable if the NetworkDeviceFunctionType is set to FibreChannelOverEthernet. |
| iSCSI | Boot this device using the embedded iSCSI boot support and configuration.  Only applicable if the NetworkDeviceFunctionType is set to iSCSI. |
| PXE | Boot this device using the embedded PXE support.  Only applicable if the NetworkDeviceFunctionType is set to Ethernet. |

### IPAddressType:


The type of IP address (IPv6 or IPv4) being populated in the iSCSIBoot IP address fields.

| string | Description |
| --- | --- |
| IPv4 | IPv4 addressing is used for all IP-fields in this object. |
| IPv6 | IPv6 addressing is used for all IP-fields in this object. |

### NetDevFuncCapabilities:


Capabilities of this network device function.

| string | Description |
| --- | --- |
| Disabled | Neither enumerated nor visible to the operating system. |
| Ethernet | Appears to the operating system as an Ethernet device. |
| FibreChannel | Appears to the operating system as a Fibre Channel device. |
| FibreChannelOverEthernet | Appears to the operating system as an FCoE device. |
| iSCSI | Appears to the operating system as an iSCSI device. |

### NetDevFuncType:


The configured capability of this network device function.

| string | Description |
| --- | --- |
| Disabled | Neither enumerated nor visible to the operating system. |
| Ethernet | Appears to the operating system as an Ethernet device. |
| FibreChannel | Appears to the operating system as a Fibre Channel device. |
| FibreChannelOverEthernet | Appears to the operating system as an FCoE device. |
| iSCSI | Appears to the operating system as an iSCSI device. |

### WWNSource:


The configuration source of the WWNs for this connection (WWPN and WWNN).

| string | Description |
| --- | --- |
| ConfiguredLocally | The set of FC/FCoE boot targets was applied locally through API or UI. |
| ProvidedByFabric | The set of FC/FCoE boot targets was applied by the Fibre Channel fabric. |


# NetworkDeviceFunctionCollection

|     |     |     |
| --- | --- | --- |
| **@odata.etag** | string<br><br>*read-only* | The current ETag of the resource. |
| **Description** | string<br><br>*read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schema definitions. |
| **Members** [ { | array<br><br>*read-only* | Contains the members of this collection. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**@odata.id** | string<br><br>*read-only* | Link to a NetworkDeviceFunction resource. See the Links section and the *NetworkDeviceFunction* schema for details. |
| } ] |   |   |
| **Name** | string<br><br>*read-only* | The name of the resource or array element. |
| **Oem** {} | object | This is the manufacturer/provider specific extension moniker used to divide the Oem object into sections. See the *Resource* schema for details on this property. |

# NetworkPort 1.1.0

A Network Port represents a discrete physical port capable of connecting to a network.

|     |     |     |
| --- | --- | --- |
| **Actions** *(v1.1+)* {} | object | The available actions for this resource. |
| **ActiveLinkTechnology** | string<br>(enum)<br><br>*read-write<br>(null)* | Network Port Active Link Technology. *See ActiveLinkTechnology in Property Details, below, for the possible values of this property.* |
| **AssociatedNetworkAddresses** [ ] | array (string, null)<br><br>*read-only* | The array of configured network addresses (MAC or WWN) that are associated with this Network Port, including the programmed address of the lowest numbered Network Device Function, the configured but not active address if applicable, the address for hardware port teaming, or other network addresses. |
| **Description** | string<br><br>*read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schema definitions. |
| **EEEEnabled** | boolean<br><br>*read-write<br>(null)* | Whether IEEE 802.3az Energy Efficient Ethernet (EEE) is enabled for this network port. |
| **FlowControlConfiguration** | string<br>(enum)<br><br>*read-write<br>(null)* | The locally configured 802.3x flow control setting for this network port. *See FlowControlConfiguration in Property Details, below, for the possible values of this property.* |
| **FlowControlStatus** | string<br>(enum)<br><br>*read-only<br>(null)* | The 802.3x flow control behavior negotiated with the link partner for this network port (Ethernet-only). *See FlowControlStatus in Property Details, below, for the possible values of this property.* |
| **Id** | string<br><br>*read-only required* | Uniquely identifies the resource within the collection of like resources. |
| **LinkStatus** | string<br>(enum)<br><br>*read-only<br>(null)* | The status of the link between this port and its link partner. *See LinkStatus in Property Details, below, for the possible values of this property.* |
| **Name** | string<br><br>*read-only required* | The name of the resource or array element. |
| **NetDevFuncMaxBWAlloc** [ { | array<br><br>*read-write* | The array of maximum bandwidth allocation percentages for the Network Device Functions associated with this port. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**MaxBWAllocPercent** | number<br><br>*read-write<br>(null)* | The maximum bandwidth allocation percentage allocated to the corresponding network device function instance. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**NetworkDeviceFunction** { | object | Contains the members of this collection. See the *NetworkDeviceFunction* schema for details on this property. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**@odata.id** | string<br><br>*read-only* | Link to a NetworkDeviceFunction resource. See the Links section and the *NetworkDeviceFunction* schema for details. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;} |   |   |
| } ] |   |   |
| **NetDevFuncMinBWAlloc** [ { | array<br><br>*read-write* | The array of minimum bandwidth allocation percentages for the Network Device Functions associated with this port. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**MinBWAllocPercent** | number<br><br>*read-write<br>(null)* | The minimum bandwidth allocation percentage allocated to the corresponding network device function instance. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**NetworkDeviceFunction** { | object | Contains the members of this collection. See the *NetworkDeviceFunction* schema for details on this property. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**@odata.id** | string<br><br>*read-only* | Link to a NetworkDeviceFunction resource. See the Links section and the *NetworkDeviceFunction* schema for details. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;} |   |   |
| } ] |   |   |
| **Oem** {} | object | This is the manufacturer/provider specific extension moniker used to divide the Oem object into sections. See the *Resource* schema for details on this property. |
| **PhysicalPortNumber** | string<br><br>*read-only<br>(null)* | The physical port number label for this port. |
| **PortMaximumMTU** | number<br><br>*read-only<br>(null)* | The largest maximum transmission unit (MTU) that can be configured for this network port. |
| **SignalDetected** | boolean<br><br>*read-only<br>(null)* | Whether or not the port has detected enough signal on enough lanes to establish link. |
| **Status** {} | object<br><br>*<br>(null)* | This type describes the status and health of a resource and its children. See the *Resource* schema for details on this property. |
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
