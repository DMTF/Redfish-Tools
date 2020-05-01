# Profile URI Mapping

Map profile URIs to local files. You may omit the protocol (e.g., https://) from the URI.
The doc generator will use the local files when specified and otherwise
follow the full URI, including data from remote files if possible.

Registry URI Mapping may be specified in the same way, with the heading "Registry URI Mapping".

## Local-repo: redfish.dmtf.org/profiles ../Redfish-Tools/doc-generator/sample_inputs

# Keyword Configuration

Keywords and their values as bullet points with name:value paris in the "Keyword Configuration" section, as shown here. Keywords are not case-sensitive.

At present, we support:

omit_version_in_headers, boolean. Default false. If false, schema sections in the generated documentation will be headed by schema name and version number. If true, only the schema name will appear in the heading.

add_toc, boolean. Default false. Add a Table of Contents (relevant for HTML output only)

- omit_version_in_headers: false
- add_toc: true

Note: you can specify the location of the TOC, presumably in the Introduction section, by placing the text [add_toc] where you want the Table of Contents substituted in. By default, the TOC will be placed at the top of the HTML output.

# Units Translation

String-replacement for "units" values. Case-sensitive. Any units not matched will be output as-is.

| Value            | Replacement      |
| ---------------- | ---------------- |
| s                | seconds          |
| Mb/s             | Mbits/second     |
| By               | Bytes            |
| Cel              | Celsius          |
| MiBy             | mebibytes        |
| W                | Watts            |
| V                | Volts            |
| mW               | milliWatts       |
| m                | meters           |




# Introduction

# Sample Profile-focused Document

[add_toc]
