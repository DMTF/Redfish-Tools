# Table Numbering README
> last modified: 10 November 2020

## Problem

1. ISO submissions require that all tables and figures be both uniquely identified, and referenced in the body of the document. For example:

    See [Table 3](#table_3) for a summary of ISO issues.

    Table 3: Summary of ISO Issues
    |Col 1 | Col 2|
    |-----|-------|
    |foo | bar |

2. The existing doc generator doesn't produce content in a linear stream, so on-the-fly numbering was not an option

## Solution

Routines were added to create:
- a standardized reference from the text to a table
- a standardized table caption
- a set of substitution tokens for table numbering
  - TBL_NN: The current table number
  - TBL_NN++: The next table number (i.e., pre-increment)

An awk routine (table_number.awk) was added to the Swordfish documentation scripts to replace the tokens with actual table numbers, once a full set of md source files had been generated. It also handles some document variable substitutions, and a numbering sequence for figures, though those are not directly related to the ISO issue.
