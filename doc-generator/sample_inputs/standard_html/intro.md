<p align="right">
  <img src="http://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180>
</p>
<p align="right">Document Identifier: <span class="dsp">DSP2046</span></p>
<p align="right">Date: 2018-8-10</p>
<p align="right">Version: <span class="version">2018.2</span></p>
<br><br><br>
<h1 class="title">Redfish Resource and Schema Guide</h1>
<br><br><br><br><br>
<br><br>
<br><br>
<b><p>Document Class: Informative</p>
<p>Document Status: <span class="status">Published</span></p>
<p>Document Language: en-US</p></b>
<br>
   <p>Copyright Notice</p>
    <p>Copyright &copy; 2016-2021 DMTF. All rights reserved.
<br><br>
  <p>DMTF is a not-for-profit association of industry members dedicated to promoting enterprise and systems management and interoperability. Members and non-members may reproduce DMTF specifications and documents, provided that correct attribution is given. As DMTF specifications may be revised from time to time, the particular version and release date should always be noted.</p>
  <p>Implementation of certain elements of this standard or proposed standard may be subject to third party patent rights, including provisional patent rights (herein "patent rights"). DMTF makes no representations to users of the standard as to the existence of such rights, and is not responsible to recognize, disclose, or identify any or all such third party patent right, owners or claimants, nor for any incomplete or inaccurate identification or disclosure of such rights, owners or claimants. DMTF shall have no liability to any party, in any manner or circumstance, under any legal theory whatsoever, for failure to recognize, disclose, or identify any such third party patent rights, or for such party's reliance on the standard or incorporation thereof in its product, protocols or testing procedures. DMTF shall have no liability to any party implementing such standard, whether such implementation is foreseeable or not, nor to any patent owner or claimant, and shall have no liability or responsibility for costs or losses incurred if a standard is withdrawn or modified after publication, and shall be indemnified and held harmless by any party implementing the standard from any and all claims of infringement by a patent owner for such implementations.</p>
  <p>For information about patents held by third-parties which have notified the DMTF that, in their opinion, such patent may relate to or impact implementations of DMTF standards, visit <a href="http://www.dmtf.org/about/policies/disclosures.php">http://www.dmtf.org/about/policies/disclosures.php</a>.</p>
  <p>This document's normative language is English. Translation into other languages is permitted.</p>
  <br>

# Contents
[add_toc]


# Overview

The Redfish standard comprises a set of specifications maintained by the Redfish Forum, a working group within the DMTF. The standard defines a protocol that uses RESTful interfaces to provide access to data and operations associated with the management of systems and networks. One of the strengths of the Redfish protocol is that it works with a wide range of servers: from stand-alone servers to rack-mount and bladed environments to large-scale data centers and cloud environments.

The Redfish standard addresses several key issues for infrastructures that require scalability. Large infrastructures often consist of many simple servers of different makes and types. This hyperscale usage model requires a new approach to systems management. The Redfish Scalable Platforms Management ("Redfish") protocol addresses these needs by providing a standard protocol based on out-of-band systems management.

With the above goals in mind, the Redfish protocol was designed as an open industry standard to meet scalability requirements in multivendor deployments. It easily integrates with commonly used tools, using RESTful interfaces to perform operations and using JSON and OData formats for data payloads.

## Who should read this document?

This document is useful to people who want to understand how to use the Redfish API. This includes application developers who want to create client-side software to communicate with a Redfish service, and other consumers of the API.

## Where can I find more information?

The following web sites provide more information about the Redfish standard:

* **Redfish Developer Hub:**  <a href="http://redfish.dmtf.org" title="http://redfish.dmtf.org">http://redfish.dmtf.org</a> Resources for developers building applications using Redfish. Contains an interactive schema explorer, hosted schema and other links.
* **Redfish User Forum:**  <a href="http://www.redfishforum.com" title="http://www.redfishforum.com">http://www.redfishforum.com</a> User forum monitored by DMTF Redfish personnel to answer questions about any Redfish-related topics:
* **DMTF Github Repositories:**  <a href="http://www.github.com/DMTF" title="http://www.github.com/DMTF">http://www.github.com/DMTF</a> Open source tools and libraries for working with the Redfish API.
* **Redfish Standards:**  <a href="http://www.dmtf.org/standards/redfish" title="http://www.dmtf.org/standards/redfish">http://www.dmtf.org/standards/redfish</a>  Schemas, specs, mockups, white papers, FAQ, educational material and more.
* **DMTF Redfish Forum** (Working group that maintains the Redfish standard):  <a href="http://www.dmtf.org/standards/spmf" title="http://www.dmtf.org/standards/spmf">http://www.dmtf.org/standards/spmf</a> Companies involved, upcoming schedules and future work, charter, and information about joining.

# Using this guide

Every Redfish API response consists of a JSON payload containing properties that are strictly defined by a schema for that resource. The schema defining a particular resource can be determined from the value of the "@odata.type" property returned in every Redfish response. This guide details the definitions for every Redfish standard schema.

Each schema section contains:

* The name, current version and description of the schema.
* A listing of the possible URIs where resources defined by this schema can appear in a Redfish Service (v1.6 or later). See [URI listings](#uri-listings) below for more information.
* A table defining each property with additional details for those properties when needed.
* A listing of the available Actions defined for the schema.
* An example JSON payload for a resource using the schema.

<br>
The property-level details include:

| Column | Purpose |
|--------|---------|
| Property name | Case-sensitive name of the JSON property as it appears in the JSON payload. For properties added to the schema after the initial v1.0.0 release, the version that the property was added appears in parenthesis. Deprecated properties are indicated along with the version where the deprecation occurred. |
| Type | JSON data types for the property. The type is boolean, number, string, or object. String types that use defined enumerations state `"(enum)"`. Number types state their units, where used. |
| Attributes | Indicates whether the property is read-only or read-write, if supported by the implementation, and whether the service might return a `null` value if the value of the property is temporarily unavailable. |
| Description | Description of the property, as copied directly from the schema `Description` definition. |

## URI listings

The *Redfish Specification* v1.6.0 added mandatory support for the *OpenAPI Specification* v3.0. As part of this support, the URIs for every Redfish resource are defined to appear at known, fixed locations. Resource collections also appear at fixed locations, with the members of each collection appearing at URIs constructed by using a fixed path structure, with appropriate path segments equal to the value of `Id` properties of members along the path.

Support for v1.6.0 and OpenAPI can be determined by comparing the value of the "RedfishVersion" property in the Service Root (`\redfish\v1\`).  Services reporting a value of `1.6.0` or higher, such as `1.6.1` or `1.7.0`, adhere to the URI definitions shown.

The URI listings do not apply to Redfish services reporting support of *Specification* versions earlier than v1.6.0.  For those services, clients must use the hypermedia features of the API to discover links from the service root to each resource.  While services typically match the URIs listed in this document for many of their resources, this practice is not guaranteed and result in errors.

# Common properties

## Properties defined for all Redfish schemas

The following properties are defined for inclusion in every Redfish schema, and therefore may be encountered in any response payload. They are documented here to avoid repetition in the *Reference Guide* property tables. Note that several of these properties are payload annotations, but are listed here as they are required for all Redfish resources.

#include_fragment ./docs/DSP2046/CommonPropertySchema.json#/definitions/CommonProperties/properties

## Frequently used properties

In addition, the following properties are frequently defined in Redfish schemas. Their definition and usage is the same throughout the Redfish data model.

#include_fragment ./docs/DSP2046/CommonPropertySchema.json#/definitions/FrequentProperties/properties

## Payload annotations

A service uses payload annotations to provide additional information about a property or object. Redfish limits usage of these annotations to OData core terms, Redfish extensions, or Redfish messages.

### Property-level annotations

A payload annotation for a single property takes the form of an additional property named `Property@Schema.Term`.

where

* `Property` is the JSON property being annotated.
* `Schema` is the schema file where the definition for the annotation is located.
* `Term` is the name of the annotation.

| Term                       | Usage |
| ----                       | ----- |
| `@Redfish.AllowableValues` | Indicates to the client the different string values the service accepts for a given action parameter. |
| `@Message.ExtendedInfo`    | Allows the service to provide a set of Message structures for a given property to indicate additional information; this can be useful when a property is `null` due to an error condition, and the service wants to convey why the property is `null`. |
| `@odata.count`             | Can be used on properties that are arrays in order to indicate their size so that a client does not need to count the array members. |

In the following example, the `ResetType` property is annotated with the `AllowableValues` term, which is defined in the `Redfish` schema, which is an alias for `RedfishExtensions`. 

This annotation indicates to the client that the service supports the `On` and `ForceOff` values for `ResetType`.

```json
{
   "ResetType@Redfish.AllowableValues": ["On", "ForceOff"],
   ...
}
```

### Resource or object-level annotations

A payload annotation for an entire resource or a JSON object takes the form of `@Schema.Term`.

where

* `Namespace` is the schema file where the definition is located.
* `Term` is the name of the Annotation.

These payload annotations provide further information about the object itself.

| Term                    | Usage |
| ----                    | ----- |
| `@Redfish.Settings`     | Gives the client a reference to the resource that represents the future property settings to be applied to this object |
| `@Redfish.ActionInfo`   | Used on actions to provide the client a reference to an ActionInfo resource, which gives detailed information about a given action's parameters |
| `@Message.ExtendedInfo` | Allows the service to provide a set of Message structures for a given object to indicate additional information; this can be useful when an error condition is reached, and the service wants to convey what error was encountered |
| `@odata.id`             | Provides the unique URI for a given resource |
| `@odata.type`           | Provides the type definition of the object in the format of `#Namespace.Type`, where `Namespace` is the Namespace in the CSDL file where the definition is found and `Type` is the name of the ComplexType or EntityType element found in the Namespace |
| `@odata.context`        | Provides an OData client with a descriptor for the content of the payload; in Redfish, this is simply always going to be `/redfish/v1/$metadata#Namespace.Entity`, where `Namespace` is the unversioned Namespace in the CSDL file where the definition is found and `Entity` is the name of the EntityType element being used |

In the example below, the object is being annotated with the `ActionInfo` term, which is defined in the `Redfish` schema (an alias for RedfishExtensions).  This is used to indicate to the client that it can find more information about the given action, in this case `#ComputerSystem.Reset`, at the URI `/redfish/v1/Systems/1/ResetActionInfo`.

```json
{
   "#ComputerSystem.Reset": {
      "target": "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
      "@Redfish.ActionInfo": "/redfish/v1/Systems/1/ResetActionInfo"
   },
   ...
}
```

# Common objects

The following JSON objects are frequently defined in Redfish schemas.  Like the individual common properties listed above, these objects share a common definition which is shown here to avoid repetition in the Reference Guide property tables.

[insert_common_objects]

# Resource collections

A core concept in Redfish is a collection of resources. A collection is a group of like resources where the number of instances in the group can shrink or grow depending on the scope of the Redfish Service or the configuration of the devices being managed. Every resource that is a resource collection has the same set of supported properties, and all contain `Collection` in the name of their schema.  Every resource linked in the `Members` array within a resource collection has the same resource type (same schema with the same major version, but can vary in minor or errata schema versions, which are all compatible).

The properties of a resource collection are as follows:

#include_fragment ./docs/DSP2046/CommonPropertySchema.json#/definitions/Collection/properties

As shown in the following example, a Redfish service may provide management functionality for several computer systems, and therefore a `ComputerSystemCollection` resource is provided. 

This example shows a service with four `ComputerSystem` instances, or members.

~~~json
{
   "@odata.type": "#ComputerSystemCollection.ComputerSystemCollection",
   "Name": "Computer System Collection",
   "Members@odata.count": 4,
   "Members": [{
      "@odata.id": "/redfish/v1/Systems/529QB9450R6"
   }, {
      "@odata.id": "/redfish/v1/Systems/529QB9451R6"
   }, {
      "@odata.id": "/redfish/v1/Systems/529QB9452R6"
   }, {
      "@odata.id": "/redfish/v1/Systems/529QB9453R6"
   }],
   "@odata.context": "/redfish/v1/$metadata#ComputerSystemCollection.ComputerSystemCollection",
   "@odata.id": "/redfish/v1/Systems"
}
~~~

## Resource collection URIs (Redfish v1.6+)

The following table lists the Redfish-defined resource collections and the URIs where they can appear.

> **Note:** The URIs listed are valid for Redfish services conforming to the *Redfish Specification* v1.6.0 or later.  Services built on earlier versions of the *Specification* may use different URIs that must be discovered by following the links from the service root (`/redfish/v1/`).

[insert_collections]

# Reference Guide

DMTF's [Redfish doc generator](#redfish-documentation-generator) generated this guide by merging supplemental text with the contents the DMTF Redfish Schema bundle DSP8010 version 2018.2.
