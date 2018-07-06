Examples of "required" and "requiredOnCreate" properties.

From Enhancements round 6:

  Add “required” and “required on create” to ‘Read/Write’ column for
  properties required by the schema.  This is indicated by the
  presence of a “required” array property in the JSON schema.  Note
  that both of these terms are rare in schema, and mostly apply to the
  common properties (@odata.id/type/context, Id, Name, Members).  An
  example of “required” appears in “ServiceRoot” (Links) and
  “LogEntry” (LogType) and example of “requiredOnCreate” appears in
  “ManagerAccount”.
