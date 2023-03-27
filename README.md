This Anki add-on adds a new browser column that allows sorting by the sort field in a more alphabetic order than the default one for non-latin text.

See the following posts for details about the problem the add-on tries to solve:

https://forums.ankiweb.net/t/sorting-should-produce-a-more-alphabetical-order/21621

https://forums.ankiweb.net/t/sort-field-in-alphabetic-order-problem/28687

## Technical details

The add-on uses the `unicase` SQLite collation added by Anki, which does Unicode case-folding using the [unicase crate](https://crates.io/crates/unicase).

## TODO

It appears that we can produce an order more similar to the expected alphabetic order for some languages using [Unicode collation algorithm](https://en.wikipedia.org/wiki/Unicode_collation_algorithm). Maybe we should explore this option and contribute to the discussion about a possible native option in Anki.
