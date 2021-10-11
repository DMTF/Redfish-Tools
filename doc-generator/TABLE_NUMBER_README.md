# Table numbering README

> last modified: 10 November 2020

[[Redfish doc generator README]](README.md#redfish-doc-generator "README.md#redfish-doc-generator")

## Problem

* ISO submissions require that all tables and figures be both uniquely identified, and referenced in the body of the document. For example:

    See [Table 3](#table_3) for a summary of ISO issues.

    Table 3: Summary of ISO issues
    |Col 1 | Col 2|
    |-----|-------|
    |foo | bar |

* The existing `doc_generator.py` does not produce content in a linear stream so on-the-fly numbering was not an option.

## Solution

Routines were added to create:

- A standardized reference from the text to a table.
- A standardized table caption.
- A set of substitution tokens for table numbering:
    - TBL_NN: The current table number
    - TBL_NN++: The next table number, such as pre-increment

An awk routine (`table_number.awk`) was added to the Swordfish documentation tools to replace the tokens with actual table numbers, once a full set of md source files had been generated. It also handles some document variable substitutions, and a numbering sequence for figures, though those are not directly related to the ISO issue.
