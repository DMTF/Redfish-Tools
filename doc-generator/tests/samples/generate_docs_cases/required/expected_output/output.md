---
title: Schema Documentation

search: true
---


# RequiredTest 1.0.0

This schema contains required and requiredOnCreate properties.

|     |     |     |
| --- | --- | --- |
| **Description** | string<br><br>*read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schema definitions. |
| **EntryType** | string<br>(enum)<br><br>*read-only required on create* | This is the type of log entry. *See EntryType in Property Details, below, for the possible values of this property.* |
| **HostWatchdogTimer** { | object<br><br>*read-write* | This object describes the Host Watchdog Timer functionality for this system. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**FunctionEnabled** | boolean<br><br>*read-write required<br>(null)* | This indicates if the Host Watchdog Timer functionality has been enabled. Additional host-based software is necessary to activate the timer function. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Oem** {} | object<br><br>*read-write* | Oem extension object. See the *Resource* schema for details on this property. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Status** {} | object<br><br>*read-write* | This type describes the status and health of a resource and its children. See the *Resource* schema for details on this property. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**TimeoutAction** | <br><br>*read-write required<br>(null)* | This property indicates the action to perform when the Watchdog Timer reaches its timeout value. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**WarningAction** | <br><br>*read-write<br>(null)* | This property indicates the action to perform when the Watchdog Timer is close (typically 3-10 seconds) to reaching its timeout value. |
| } |   |   |
| **Id** | string<br><br>*read-only required* | Uniquely identifies the resource within the collection of like resources. |
| **Name** | string<br><br>*read-only required* | The name of the resource or array element. |

## Property Details

### EntryType:


This is the type of log entry.

| string | Description |
| --- | --- |
| Event | Contains a Redfish-defined message (event). |
| Oem | Contains an entry in an OEM-defined format. |
| SEL | Contains a legacy IPMI System Event Log (SEL) entry. |
