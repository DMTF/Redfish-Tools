---
title: Schema Documentation

search: true
---


# RequiredTest 1.0.0

This schema contains required and requiredOnCreate properties.

|     |     |     |
| --- | --- | --- |
| **Description** | string<br><br>*read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schema definitions. |
| **EntryType** | string<br>(enum)<br><br>*read-only*<br>required on create | This is the type of log entry. *See EntryType in Property Details, below, for the possible values of this property.* |
| **Id** | string<br><br>*read-only*<br>required | Uniquely identifies the resource within the collection of like resources. |
| **Name** | string<br><br>*read-only*<br>required | The name of the resource or array element. |

## Property Details

### EntryType:


This is the type of log entry.

| string | Description |
| --- | --- |
| Event | Contains a Redfish-defined message (event). |
| Oem | Contains an entry in an OEM-defined format. |
| SEL | Contains a legacy IPMI System Event Log (SEL) entry. |
