---
layout: post
title: "Minimal clickhouse setup with minio for local dev"
author: "bhakyuz"
tags: ["clickhouse", "minio", "data-eng"]
---

## Minimal clickhouse setup with minio for local dev

Recently I was testing clickhouse for a potential migration. First thing first, I've to do some tests on my local machine to see if there is a fit etc. 

For some reason, it took me more time than I initially thought. 

I wanted to share quickly my learnings in this [repo](https://github.com/bhakyuz/clickhouse-minio-minimal-setup). You can clone the repo and test it yourself while reading.  

## Get everything running

As simple as running docker compose command:
```sh
docker-compose up -d
docker-compose ps
```

3 services should be running:
- Clickhouse
- minio
- minio-client (Without this, I could not make it work for connecting to minio service)

In some other repos, I've seen the use of `storage.xml` for `clickhouse-server/config.d`. For this particular setup it's not needed as everything tested works without it. 

## Local Minio

One can go to the browser to see the content stored in [minio bucket](http://127.1.1.1:8012/) (similar to AWS s3). Credentials to connect are `minio` and `minio123`. 

You'll notice that a bucket named `test` is created and there are already some csv files uploaded there for testing purpose.   


## Clickhouse explorations

We can connect to clickhouse client via docker-compose command
```sh
docker-compose exec clickhouse clickhouse-client
```

### Simple query
Once there, we can run simple commands such:
```sql
:) select 1;

SELECT 1

Query id: 00601a0c-f908-40da-9deb-ae15a4a7447d

   ┌─1─┐
1. │ 1 │
   └───┘

1 row in set. Elapsed: 0.001 sec. 
```

### Reading data from s3/minio

In most of the cases, we want to load some data to our analytics database. One of the common method is to read/load from s3. We can do so inside clickhouse directly. And good news is that we don't even have to create a table or so. 

Please notice that a shorter version of [sample dataset aapl_stock.csv](https://datasets-documentation.s3.eu-west-3.amazonaws.com/aapl_stock.csv) is already loaded into our minio bucket. 

```sql
SELECT *
FROM s3('http://minio:9001/test/sample.csv', 'minio', 'minio123', 'CSV')

Query id: 5ce3c6df-3df4-45b7-92fe-47d559f086c3

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

11 rows in set. Elapsed: 0.021 sec. 

```


### Reading data from s3/minio with 'smart' path

Secondly I've realized that while reading from some s3 paths that are built with some naming choices in mind. Clickhouse adds some additional columns into dataset without much of asking:

```sql
SELECT *
FROM s3('http://minio:9001/test/sample/date=2025-10-12/sample.csv', 'minio', 'minio123', 'CSV')

Query id: 5a64386d-936b-4bc6-906d-791be1c50e23

    ┌───────Date─┬────Open─┬────High─┬─────Low─┬───Close─┬───Volume─┬─OpenInt─┬───────date─┐
 1. │ 1984-09-07 │ 0.42388 │ 0.42902 │ 0.41874 │ 0.42388 │ 23220030 │       0 │ 2025-10-12 │
 2. │ 1984-09-10 │ 0.42388 │ 0.42516 │ 0.41366 │ 0.42134 │ 18022532 │       0 │ 2025-10-12 │
 3. │ 1984-09-11 │ 0.42516 │ 0.43668 │ 0.42516 │ 0.42902 │ 42498199 │       0 │ 2025-10-12 │
 4. │ 1984-09-12 │ 0.42902 │ 0.43157 │ 0.41618 │ 0.41618 │ 37125801 │       0 │ 2025-10-12 │
 5. │ 1984-09-13 │ 0.43927 │ 0.44052 │ 0.43927 │ 0.43927 │ 57822062 │       0 │ 2025-10-12 │
 6. │ 1984-09-14 │ 0.44052 │ 0.45589 │ 0.44052 │ 0.44566 │ 68847968 │       0 │ 2025-10-12 │
 7. │ 1984-09-17 │ 0.45718 │ 0.46357 │ 0.45718 │ 0.45718 │ 53755262 │       0 │ 2025-10-12 │
 8. │ 1984-09-18 │ 0.45718 │ 0.46103 │ 0.44052 │ 0.44052 │ 27136886 │       0 │ 2025-10-12 │
 9. │ 1984-09-19 │ 0.44052 │ 0.44566 │ 0.43157 │ 0.43157 │ 29641922 │       0 │ 2025-10-12 │
10. │ 1984-09-20 │ 0.43286 │ 0.43668 │ 0.43286 │ 0.43286 │ 18453585 │       0 │ 2025-10-12 │
11. │ 1984-09-21 │ 0.43286 │ 0.44566 │ 0.42388 │ 0.42902 │ 27842780 │       0 │ 2025-10-12 │
    └────────────┴─────────┴─────────┴─────────┴─────────┴──────────┴─────────┴────────────┘

11 rows in set. Elapsed: 0.006 sec. 
```

Notice that `date` column is directly coming from the s3 path (e.g. `date=2025-10-12`). 

I believe in many cases this can be useful. But it would be good to enable/disable this in the query which I could not figure out yet how. 

Additonally we can also read data with wildcards such as:

```sql
 select * from s3('http://minio:9001/test/sample/*/*.csv',
                  'minio',
                  'minio123', 'CSV');
```

The resuls of the query will be as same as the previous as we've only one csv file in sample directory. 

Small tip: `q` command will take us out of clickhouse-client to our terminal. 

Thanks for reading. 
