# FRAGMENT FOLLOWS



## Properties

|Property     |Type     |Notes     |
| --- | --- | --- |
| **@odata.context** | string<br>(URI)<br><br>*read-only* | The URL to a metadata document with a fragment that describes the data, which is typically rooted at the top-level singleton or collection.  Technically, the metadata document has to only define, or reference, any of the types that it directly uses, and different payloads could reference different metadata documents. However, because this property provides a root URL for resolving a relative reference, such as `@odata.id`, the API returns the canonical metadata document. |
| **@odata.etag** | string<br><br>*read-only* | The current ETag for the Resource. |
| **@odata.id** | string<br>(URI)<br><br>*read-only required* | The unique ID for the Resource. |
| **@odata.type** | string<br><br>*read-only required* | The type of a resource. |
| **Description** | string<br><br>*read-only* | The human-readable description for the Resource. |
| **Id** | string<br><br>*read-only* | The ID that uniquely identifies the Resource within the collection that contains it.  This value is unique within a collection. |
| **Name** | string<br><br>*read-only required* | The human-readable moniker for a Resource.  The type is string.  The value is NOT necessarily unique across Resource instances within a collection. |
| **Oem** {} | object | The manufacturer- or provider-specific extension moniker that divides the `Oem` object into sections. |
