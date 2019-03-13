MessageRegistry/Messages is a rich example of a property defined by patternProperties.

In this example, I have not specified omitting the
"^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\\.[a-zA-Z_][a-zA-Z0-9_.]+$"
property, because it provides a good example of a property that would
be output incorrectly if it goes through markdown-to-html conversion.
