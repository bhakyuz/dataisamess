---
layout: post
title: "Clickhouse bug while reading csv from a S3 path containing white space"
author: "bhakyuz"
tags: ["clickhouse", "bug"]
---

These days, I've been testing clickhouse for potential as I've previously mentioned in my blog. While overall, I'm very content with it, I'm also encountering some issues that I wanted to document here too. 

First issue I've come accross was not so easy to spot at first point. But with some exploration I was able to figure out that it was about s3 paths.  

As usual, everything is available in this [repo](https://github.com/bhakyuz/clickhouse-minio-minimal-setup) and you can reproduce it for yourself. 

## Same CSV within two distinct paths

I've create a CSV file with exactly same contecnt in two distinct paths in my s3 bucket:
- `test/sample.csv`
- `test/folder with whitespace/sample.csv`

I'm expecting to be able to read the data correctly independently of its path. But unfortunately, clickhouse always returns an error when there is a white space within the path. 

## Reading from regular directory

Let's read it from the first path to begin with: 

```sql
SELECT *
FROM s3('http://minio:9001/test/sample.csv', 'minio', 'minio123', 'CSV')

Query id: a6575024-8932-4e3d-a677-48bd06ea1841

    ┌───────Date─┬────Open─┬────High─┬─────Low─┬───Close─┬───Volume─┬─OpenInt─┐
 1. │ 1984-09-07 │ 0.42388 │ 0.42902 │ 0.41874 │ 0.42388 │ 23220030 │       0 │
 2. │ 1984-09-10 │ 0.42388 │ 0.42516 │ 0.41366 │ 0.42134 │ 18022532 │       0 │
 3. │ 1984-09-11 │ 0.42516 │ 0.43668 │ 0.42516 │ 0.42902 │ 42498199 │       0 │
 4. │ 1984-09-12 │ 0.42902 │ 0.43157 │ 0.41618 │ 0.41618 │ 37125801 │       0 │
 5. │ 1984-09-13 │ 0.43927 │ 0.44052 │ 0.43927 │ 0.43927 │ 57822062 │       0 │
 6. │ 1984-09-14 │ 0.44052 │ 0.45589 │ 0.44052 │ 0.44566 │ 68847968 │       0 │
 7. │ 1984-09-17 │ 0.45718 │ 0.46357 │ 0.45718 │ 0.45718 │ 53755262 │       0 │
 8. │ 1984-09-18 │ 0.45718 │ 0.46103 │ 0.44052 │ 0.44052 │ 27136886 │       0 │
 9. │ 1984-09-19 │ 0.44052 │ 0.44566 │ 0.43157 │ 0.43157 │ 29641922 │       0 │
10. │ 1984-09-20 │ 0.43286 │ 0.43668 │ 0.43286 │ 0.43286 │ 18453585 │       0 │
11. │ 1984-09-21 │ 0.43286 │ 0.44566 │ 0.42388 │ 0.42902 │ 27842780 │       0 │
    └────────────┴─────────┴─────────┴─────────┴─────────┴──────────┴─────────┘

11 rows in set. Elapsed: 0.006 sec. 
```


## Reading from a directory containing white space

Now reading the very same file from path containing whitespaces fires an error:

```sql
SELECT *
FROM s3('http://minio:9001/test/folder with whitespace/sample.csv', 'minio', 'minio123', 'CSV')

Query id: f468d93a-aa59-49db-9a0c-e8c20be11f54


Elapsed: 0.004 sec. 

Received exception from server (version 25.8.10):
Code: 1000. DB::Exception: Received from localhost:9000. DB::Exception: Bad URI syntax: URI contains invalid characters. (POCO_EXCEPTION)
```


## To conclude

I've created my very [first issue](https://github.com/ClickHouse/ClickHouse/issues/88936) in clickhouse repo to contribute. I've seen that similar issue was [reported](https://github.com/ClickHouse/ClickHouse/issues/54345) and supposedly fixed previously. Hopefully in no time, this will get fixed. 

In our current setup at TM, we have had some s3 urls like the one in the example. Ideally, we should be able to load into clickhouse independently but if not we might need re-visit the paths that we create in our s3 buckets.   
