This example consists of the NetworkPort schema plus supporting
schemas, with some properties deleted so there's no need to traverse
further.

The only reason for this is to have a catch-all test for much of what
typically appears in a schema. It probably should be removed if/when
sufficient more-targeted tests are in place.

Note that the "expected output" may not reflect what we'd want in
"typical output," because the configuration used is minimal. For a
specific example, this output does not exclude Collections.
