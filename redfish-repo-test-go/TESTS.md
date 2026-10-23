# Tests Run by `repotest`

This document describes the validation tests that the `repotest` executable performs on a Redfish repository. The runtime entry point is `cmd/repotest/main.go`; it loads the repository configuration and calls `src/testing/main.go` (`CreateTestsFromConfig`) to build a `testsuite.TestMain` containing the test lists below.

The tool runs six independent test lists. CSDL is always run first; Mockups and DSP2046 depend on the parsed CSDL cache. JSON Schema, Markdown, and Message Registry run in parallel with those lists. Use the `--pedantic` flag to enable additional strict checks where noted.

---

## CSDL

Source: `src/testing/csdl/main.go`

For every `.xml` file in the configured `csdlDir` (or the single `.xml` file when run in single-file mode), the tool creates a suite and runs the following tests against the parsed CSDL graph:

- **Valid Syntax** (`ParseTest`): Parses the CSDL XML file, resolves local references, and builds the in-memory type map and searcher.
- **Units are valid** (`ValidateUnits`): Every `Measures.Unit` annotation contains a measurement string that is valid according to the UCUM-based unit utilities.
- **Schemas have permissions** (`SchemasHavePermissions`): Every non-ComplexType property in non-`RedfishExtensions` schemas has an `OData.Permissions` annotation either directly or via its base type. (previous test was called "Complex Types Should Not Have Permissions" which was a bit misleading.)
- **Descriptions are valid** (`DescriptionChecks`): `OData.Description` and `OData.LongDescription` strings end with a period, contain no misspellings (via `golangci/misspell`), and long descriptions do not use the word "must".
- **Schemas are valid** (`SchemaTest`):
  - Schemas are not empty unless listed in `allow.allowedBareSchemas`.
  - Schema namespace names are not plural (with `allow.pluralSchema` exceptions).
  - Versioned namespaces are no more than one version ahead of the published DMTF schema list.
  - Actions and their parameters have `Description` and `LongDescription`.
  - Each schema declares an owning entity and a valid `Redfish.Release` annotation (except in errata namespaces or allow-listed schemas).
- **Entities are valid** (`EntityChecks`):
  - Entity names are not plural (with `allow.pluralEntity` exceptions).
  - Base types exist.
  - Entities that should have `Actions` property do so (with `allow.noActions` exceptions).
  - Entities have `Description` and `LongDescription`.
  - Base `Resource`/`ResourceCollection` entities contain insert/update/delete restriction annotations.
  - Base resources are listed in the privilege registry.
  - Entities marked updatable have writable properties, and entities with writable properties are marked updatable.
  - Non-Collection types cannot be Insertable.
- **Complex types are valid** (`ComplexTypeChecks`): Complex type names are not plural, base types are valid, and non-abstract complex types have both descriptions.
- **Annotations are valid** (`AnnotationChecks`): Every annotation term is either a known hard-coded term or resolves to a defined CSDL term.
- **Enums are valid** (`EnumChecks`): Enum member names are PascalCased (with `allow.nonPascalEnums` exceptions).
- **Properties are valid** (`PropertyChecks`):
  - Property and navigation property names are PascalCased (with `allow.nonPascalProperties` exceptions).
  - Properties have `Description` and `LongDescription` (except `Name`, `Id`, and `Description`).
  - `Measures.Unit` annotations are reflected in the property name.
  - Property types are known primitive, enum, complex, or type-definition references.
  - Collection navigation properties are not nullable.
- **Actions are valid** (`ActionChecks`): Actions and their parameters have descriptions, `IsBound` is true, and a target binding parameter (`.Actions` or `.OemActions`) is present.
- **References are valid** (`ReferenceCheck`): Every `edmx:Reference` URI uses an allowed prefix, and each included namespace is actually used in the file. A fixed allow-list permits common unused vocabularies.
- **URIs are valid** (`URIChecks`): Unversioned schemas contain a `Redfish.Uris` annotation (except `allow.noURISchemas`).

### Pedantic CSDL checks

When `--pedantic` is enabled, two extra tests are added per CSDL file:

- **Descriptions are valid (pedantic)** (`DescriptionPendantic`): Every period in `OData.Description` and `OData.LongDescription` is followed by two spaces or is at end of string.
- **References are valid (pedantic)** (`ReferenceCheckPedantic`): Same reference check as above, but no unused-reference allow-list is applied.

---

## Mockups

Source: `src/testing/mockup/main.go`

For every directory under the configured `mockupDir`, the tool creates a suite and runs:

- **All files are UTF8 and JSON** (`Mockup.Load`): Walks the mockup directory, reads every JSON file, validates it is valid UTF-8, and parses it as a JSON object.
- **Copyrights are valid** (`CopyrightTest`): Every non-example JSON file has a `@Redfish.Copyright` field that matches the configured copyright regular expression (allow-listed paths excepted).
- **File Root Types are valid** (`FileTypesAreValid`): Every JSON file declares an `@odata.type` that resolves to a known CSDL type in the parsed type map. Error response files and excluded paths are skipped.
- **File Content matches type** (`ContentMatchesType`):
  - `@odata.id` matches the file path if the mockup is internally consistent.
  - `@odata.context` is sane for the file type (or `/redfish/v1/$metadata` for `odata`).
  - `@odata.etag` is a valid ETag string if present.
  - `Members@odata.count` matches the `Members` array length (except when paginated).
  - `@odata.nextLink` is valid and points to the same path with query parameters.
  - Navigation links point to real files and the target type matches the declared property type.
  - Each property value is valid for its CSDL type (booleans, decimals/integers with min/max, strings with `Validation.Pattern`/`OData.IsURL`/IPv6 format, `Edm.DateTimeOffset`, `Edm.Duration`, `Edm.Guid`, arrays, complex types, enums).
- **Explorer config is present and sane** (`ExplorerTest`): For mockup directories whose name contains "public", the file `/redfish/v1/explorer_config.json` exists with valid `name`, `description`, and `navlinks` that reference real mockup paths.

---

## DSP2046

Source: `src/testing/dsp2046/main.go`

This list depends on the CSDL cache and scans the `DSP2046-examples` directory under the configured `mockupDir`. For each CSDL file, it creates a suite and runs:

- **Entities have DSP2046 examples**: Every non-abstract, non-collection, non-`ReferenceableMember` entity type in the CSDL has a matching example JSON file.
- **Actions have DSP2046 request and response examples**: Every action has a request example if it accepts more than the binding parameter, and a response example if it declares a return type. Conversely, response examples without a return type are reported.

---

## JSON Schema

Source: `src/testing/jsonschema/main.go`

For the configured `jsonSchemaDir` (or a single `.json` file), the tool creates one or more suites and runs:

- **All files are UTF8 and JSON**: Each JSON schema file is valid UTF-8 and parses as JSON.
- **All files have required $schema**: Each non-core schema file declares a `$schema` value. Files whose name contains `1.0` must use the old-style DMTF schema URI; other valid Redfish schema files must use `http://redfish.dmtf.org/schemas/v1/<filename>`. Core files (`redfish-schema.1.0.0.json`, `odata.4.0.0.json`, and files recognized as the base Redfish schema) are exempt.

---

## Markdown

Source: `src/testing/markdown/main.go`

For every `.md` file matched by the `markdownGlobs` patterns (or a single `.md` file), the tool creates a suite and runs:

- **Parses as Markdown**: The file is readable and parses as Markdown using Goldmark with the Pandoc extension.
- **Validate examples**: Every fenced JSON code block parses as valid JSON (ellipsis placeholders are stripped before parsing).
- **Validate links**: Every internal `#anchor` link points to an existing heading or raw HTML anchor. When no exact anchor is found, a fuzzy suggestion is reported.

---

## Message Registry

Source: `src/testing/registry/main.go`

For every `.json` file in the configured `messageRegistryDir` (privilege registry files are skipped), the tool creates a suite and runs:

- **Valid UTF8 and JSON**: The file is valid UTF-8 and parses as a JSON object.
- **Filename and Data match**: The file name equals `<RegistryPrefix>.<RegistryVersion>.json` from the file contents.

---

## Configuration-Driven Inputs

`cmd/repotest/main.go` reads `config.yaml` (and any extra `--config` files) to locate the directories above. The relevant keys are:

- `csdlDir` -- CSDL XML files.
- `mockupDir` -- mockup JSON directories and the `DSP2046-examples` folder.
- `jsonSchemaDir` -- JSON schema files.
- `markdownGlobs` -- Markdown file globs.
- `messageRegistryDir` -- message registry JSON files.
- `allow.*` -- allow lists that suppress specific errors.

Use `--pedantic` to enable the additional CSDL description-spacing and unused-reference checks. Use `--gcc` or `--go` to change the output message format.
