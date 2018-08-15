A limited set of schemas for testing of OpenAPI support (URIs).

These files were copied directly from the DMTF/Redfish repo at a
certain point in time, with the following modifications made:

 * In LogEntryCollection.json, the uris have been changed ("Entries"
   replaced by "STUBCollection") so that tests can match either the
   Collection uris or the LogEntry uris without fear of false
   positive.
