---
title: Schema Documentation

search: true
---


# IntegerTest 1.0.0

This schema contains one or more properties of type integer.

|     |     |     |
| --- | --- | --- |
| **Description** | string<br><br>*read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schema definitions. |
| **Links** | <br><br>*read-write* | Contains references to other resources that are related to this resource. |
| **Name** | string<br><br>*read-only required* | The name of the resource or array element. |
| **ProcessorSummary** { | object | This object describes the central processors of the system in general detail. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**(pattern)** |  | ^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message|Privileges)\.[a-zA-Z_][a-zA-Z0-9_.]+$ |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Count** | integer<br><br>*read-only<br>(null)* | The number of physical processors in the system. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**LogicalProcessorCount** | integer<br><br>*read-only<br>(null)* | The number of logical processors in the system. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Model** | string<br><br>*read-only<br>(null)* | The processor model for the primary or majority of processors in this system. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Status** {} | object | This type describes the status and health of a resource and its children. See the *Resource* schema for details on this property. |
| } |   |   |
