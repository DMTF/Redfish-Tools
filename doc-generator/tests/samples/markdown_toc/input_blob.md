---
title: Schema Documentation

search: true
---

# Sample Text for TOC Generation

This file contains text similar to what the doc generator would produce. (Albeit much trimmed.)

# Schema Documentation

## NetworkDeviceFunction 1.3.2

|     |     |
| --- | --- |
| **Version** | *v1.3* |
| **Release** | 2018.2 |
### Description

A Network Device Function represents a logical interface exposed by the network adapter.


### Properties

|Property     |Type     |Attributes   |Notes     |
| --- | --- | --- | --- |
| **@odata.etag** | string | *read-only* | The current ETag of the resource. |
| **Actions** *(v1.1+)* {} | object |  | The available actions for this resource. |
| **AssignablePhysicalPorts** [ { | array |  | The array of physical port references that this network device function may be assigned to. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**@odata.id** | string<br>(URI) | *read-only* | The unique identifier for a resource. |
| } ] |   |   |
| **BootMode** | string<br>(enum) | *read-write<br>(null)* | The boot mode configured for this network device function. *For the possible property values, see BootMode in Property details.* |
| **Description** | string | *read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schema definitions. |
| **DeviceEnabled** | boolean | *read-write<br>(null)* | Whether the network device function is enabled. |

### Property details

#### AuthenticationMethod:

The iSCSI boot authentication method for this network device function.

| string | Description |
| --- | --- |
| CHAP | iSCSI Challenge Handshake Authentication Protocol (CHAP) authentication is used. |
| MutualCHAP | iSCSI Mutual Challenge Handshake Authentication Protocol (CHAP) authentication is used. |
| None | No iSCSI authentication is used. |

#### BootMode:

The boot mode configured for this network device function.

| string | Description |
| --- | --- |
| Disabled | Do not indicate to UEFI/BIOS that this device is bootable. |
| FibreChannel | Boot this device using the embedded Fibre Channel support and configuration.  Only applicable if the NetworkDeviceFunctionType is set to FibreChannel. |
| FibreChannelOverEthernet | Boot this device using the embedded Fibre Channel over Ethernet (FCoE) boot support and configuration.  Only applicable if the NetworkDeviceFunctionType is set to FibreChannelOverEthernet. |
| iSCSI | Boot this device using the embedded iSCSI boot support and configuration.  Only applicable if the NetworkDeviceFunctionType is set to iSCSI. |
| PXE | Boot this device using the embedded PXE support.  Only applicable if the NetworkDeviceFunctionType is set to Ethernet. |


## NetworkDeviceFunctionCollection


### Properties

|Property     |Type     |Attributes   |Notes     |
| --- | --- | --- | --- |
| **@odata.etag** | string | *read-only* | The current ETag of the resource. |
| **Description** | string | *read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schema definitions. |
| **Members** [ { | array |  | Contains the members of this collection. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**@odata.id** | string<br>(URI) | *read-only* | The unique identifier for a resource. |
| } ] |   |   |
| **Name** | string | *read-only* | The name of the resource or array element. |
| **Oem** {} | object |  | This is the manufacturer/provider specific extension moniker used to divide the Oem object into sections. See the *redfish.dmtf.org/schemas/v1/Resource.json* schema for details on this property. |

## NetworkPort 1.1.0

### Description

A Network Port represents a discrete physical port capable of connecting to a network.


### Properties

|Property     |Type     |Attributes   |Notes     |
| --- | --- | --- | --- |
| **Actions** {} | object |  | The available actions for this resource. |
| **ActiveLinkTechnology** | string<br>(enum) | *read-write<br>(null)* | Network Port Active Link Technology. *For the possible property values, see ActiveLinkTechnology in Property details.* |
| **AssociatedNetworkAddresses** [ ] | array (string, null) | *read-only* | The array of configured network addresses (MAC or WWN) that are associated with this Network Port, including the programmed address of the lowest numbered Network Device Function, the configured but not active address if applicable, the address for hardware port teaming, or other network addresses. |
| **Description** | string | *read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schem