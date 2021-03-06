# Country Row Migrator

A database migration utility for the updated user country storage.
![Example Console Log](https://user-images.githubusercontent.com/36131887/174663844-633ff769-cf2b-4b9b-8886-012a91d923b6.png)

### Pre-setup

Firstly, you will have to run the query below to add the `country` column to your database.

```sql
ALTER TABLE `users` ADD `country` VARCHAR(2) NOT NULL DEFAULT 'XX' AFTER `ban_reason`;
```

Then, you open the `main.go` file in an editor of choice, setting the SQL credentials to your database.

### Setting up the migrator.
Then, you must set up the migrator before you are able to run it.

Run this command to install the required go modules for the migrator to run.
```sh
go get
```

### Running the migrator
Finally, you are now able to run the migrator using the command
```sh
go run .
```

This will immediately start the migration utility.
