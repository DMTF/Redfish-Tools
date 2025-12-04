

## IntegerTest 1.0.0

<a name="integertest"></a>

### Description

This schema contains one or more properties of type integer.


### Properties

|Property     |Type     |Attributes   |Notes     |
| :--- | :--- | :--- | :--------------------- |
| **Description** | string | *read-only<br>(null)* | Provides a description of this resource and is used for commonality  in the schema definitions. |
| **Links** |  | *read-write* | Contains references to other resources that are related to this resource. |
| **Name** | string | *read-only required* | The name of the resource or array element. |
| **ProcessorSummary** { | object |  | This object describes the central processors of the system in general detail. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Count** | integer | *read-only<br>(null)* | The number of physical processors in the system. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**LogicalProcessorCount** | integer | *read-only<br>(null)* | The number of logical processors in the system. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Model** | string | *read-only<br>(null)* | The processor model for the primary or majority of processors in this system. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Status** {} | object |  | This type describes the status and health of a resource and its children. See the *[Resource](http://redfish.dmtf.org/schemas/v1/Resource.json)* schema for details on this property. |
| } |   |   |