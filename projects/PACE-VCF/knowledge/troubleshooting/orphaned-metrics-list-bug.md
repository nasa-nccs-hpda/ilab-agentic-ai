# Troubleshooting: 40 metrics silently excluded from extraction

## Symptom

A metrics-validation notebook's comparison set was missing roughly 40
metrics that should have been present -- with no error, warning, or
indication that anything was wrong. The metrics simply never showed up in
the extracted output.

## Confirmed cause

A Python list literal defining the metrics to extract was closed
prematurely with a `]` after 22 items. Immediately after it, ~40 more items
sat in what looked like a continuation of the same list but was actually a
second, separate, bare list literal -- syntactically valid Python, but never
assigned to a variable. Python evaluates and silently discards an
unassigned expression statement, so this second block simply did nothing:
no `SyntaxError`, no `NameError`, just quietly dead code sitting in the
middle of an otherwise-working cell.

## Resolution

Removed the premature `]`, merging the two list fragments into one correctly
assigned list of ~62 items (later grown further to match a companion
notebook's comparison set, bringing total extraction to 78 metrics).

## How to catch this class of bug

A long list literal that is silently truncated this way produces no runtime
signal at all -- the cell "works." The only reliable check is comparing the
*count* of items actually extracted against an independent expectation (a
companion notebook's metric count, a manually maintained total, or a
print statement immediately after the list definition reporting
`len(METRICS_LIST)`). Don't trust that "the cell ran without error" means
"the cell did what the code appears to do" for any list/dict literal split
across many lines.
