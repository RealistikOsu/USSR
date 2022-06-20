## What is this?
This is a tools for updating older USSR databases (pre-20/6/22) to the schema used by modern USSR.
This migrations utility is responsible for moving user country data from the `users_stats` table to the `users` table and much more.
This changes resolves a consistency error within the schema alongisde improving the performance of some queries which require the country alongside
user data.

Every folder has their custom readme so you won't get confused running it.

## Requirements.

This migration utilities requires `golang >= 1.17` as it is written with performance in mind.