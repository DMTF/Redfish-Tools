

## RequiredTest 1.0.0

<a name="requiredtest"></a>

### Description

This schema contains required and requiredOnCreate properties.


### Properties

|Property     |Type     |Attributes   |Notes     |
| :--- | :--- | :--- | :--------------------- |
| **Description** | string | *read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schema definitions. |
| **EntryType** | string<br>(enum) | *read-only required on create* | This is the type of log entry. *For the possible property values, see [EntryType](#requiredtest-entrytype) in Property details.* |
| **HostWatchdogTimer** { | object |  | This object describes the Host Watchdog Timer functionality for this system. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**FunctionEnabled** | boolean | *read-write required<br>(null)* | This indicates if the Host Watchdog Timer functionality has been enabled. Additional host-based software is necessary to activate the timer function. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Oem** {} | object |  | Oem extension object. See the *[Resource](http://redfish.dmtf.org/schemas/v1/Resource.json)* schema for details on this property. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Status** {} | object |  | This type describes the status and health of a resource and its children. See the *[Resource](http://redfish.dmtf.org/schemas/v1/Resource.json)* schema for details on this property. |
| } |   |   |
| **Id** | string | *read-only required* | Uniquely identifies the resource within the collection of like resources. |
| **Name** | string | *read-only required* | The name of the resource or array element. |

### Property details

#### EntryType

<a name="requiredtest-entrytype"></a>

This is the type of log entry.

| string | Description |
| :--- | :------------ |
| Event | Contains a Redfish-defined message (event). |
| Oem | Contains an entry in an OEM-defined format. |
| SEL | Contains a legacy IPMI System Event Log (SEL) entry. |