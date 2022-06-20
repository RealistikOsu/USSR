# Country Field Migrator

This is big bottleneck of ripple and this tool aims to fix it.

If you are using new fresh database schema from `extras/db.sql` you don't need to run it
but if you use existing database, you'll need to run
```sql
ALTER TABLE `users` ADD `country` VARCHAR(2) NOT NULL DEFAULT 'XX' AFTER `country`;
```
this query before running the migrator.

## How to run?
You just have to edit `main.go` upper variables
and run these 2 commands

```sh
go get
```
this will get all dependences it needs

```sh
go run .
```
this will run the migrator itself