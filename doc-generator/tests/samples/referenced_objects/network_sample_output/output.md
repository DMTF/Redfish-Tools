# Oem

Oem extension object.

|     |     |     |
| --- | --- | --- |
| **(pattern)** |  | [A-Za-z0-9_.:]+, ^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\.[a-zA-Z_][a-zA-Z0-9_.]+$ |

# Status

This type describes the status and health of a resource and its children.

|     |     |     |
| --- | --- | --- |
| **(pattern)** |  | ^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\.[a-zA-Z_][a-zA-Z0-9_.]+$ |
| **Health** | string<br>(enum)<br><br>*read-only<br>(null)* | This represents the health state of this resource in the absence of its dependent resources. *See Health in Property Details, below, for the possible values of this property.* |
| **HealthRollup** | string<br>(enum)<br><br>*read-only<br>(null)* | This represents the overall health state from the view of this resource. *See HealthRollup in Property Details, below, for the possible values of this property.* |
| **Oem** { | object | Oem extension object. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**(pattern)** |  | [A-Za-z0-9_.:]+, ^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\.[a-zA-Z_][a-zA-Z0-9_.]+$ |
| } |   |   |
| **State** | string<br>(enum)<br><br>*read-only<br>(null)* | This indicates the known state of the resource, such as if it is enabled. *See State in Property Details, below, for the possible values of this property.* |

## Property Details

### Health:


This represents the health state of this resource in the absence of its dependent resources.

| string | Description |
| --- | --- |
| Critical | A critical condition exists that requires immediate attention. |
| OK | Normal. |
| Warning | A condition exists that requires attention. |

### HealthRollup:


This represents the overall health state from the view of this resource.

| string | Description |
| --- | --- |
| Critical | A critical condition exists that requires immediate attention. |
| OK | Normal. |
| Warning | A condition exists that requires attention. |

### State:


This indicates the known state of the resource, such as if it is enabled.

| string | Description |
| --- | --- |
| Absent | This function or resource is not present or not detected. |
| Deferring | The element will not process any commands but will queue new requests. |
| Disabled | This function or resource has been disabled. |
| Enabled | This function or resource has been enabled. |
| InTest | This function or resource is undergoing testing. |
| Quiesced | The element is enabled but only processes a restricted set of commands. |
| StandbyOffline | This function or resource is enabled, but awaiting an external action to activate it. |
| StandbySpare | This function or resource is part of a redundancy set and is awaiting a failover or other external action to activate it. |
| Starting | This function or resource is starting. |
| UnavailableOffline | This function or resource is present but cannot be used. |
| Updating | The element is updating and may be unavailable or degraded. |
