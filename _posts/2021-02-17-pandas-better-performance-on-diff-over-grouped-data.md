---
layout: post
title: "Pandas: Better performance on `diff()` over grouped data"
author: "bhakyuz"
tags: ["pandas", "group-by", "diff", "performance"]
---

Recently, I needed to do small manipulation on a relatively big data frame. In this data frame, I had cumulated revenues per some dimensions/categories and I wanted to calculate discrete in other words non-cumulated revenues. Looks easy, right? At least, that is how I thought.

It is quite straightforward in `pandas` to get the difference of values in a series. `pd.Series.diff()` is already built for that. We can also do the same over groups that we have aggregated data on. Some [stackoverflow](https://stackoverflow.com/) threads mention that it is not handled so well from a performance perspective and it is relatively slow. ([1](https://stackoverflow.com/questions/20648346/computing-diffs-within-groups-of-a-dataframe), [2](https://stackoverflow.com/questions/33498061/pandas-groupby-apply-performing-slow), [3](https://stackoverflow.com/questions/50511144/pandas-diff-seriesgroupby-is-relatively-slow)). So I also learned my lesson when I get to get away easily from this problem. To sum up, it gets quite slow When data gets bigger.

## Sample data and initial approach

Let’s start easy and create a sample data frame to visualize it in a better way.

```py
def generate_sample(size=50, group=10):
    raw = pd.DataFrame({
        'order': np.arange(size),
        'a': np.random.randint(1,group,size=size),
        'b': np.random.randint(1,10,size=size)})
    return raw

ex1 = generate_sample()
#     order  a  b
# 0       0  9  7
# 1       1  5  1
# 2       2  5  3
# 3       3  9  8
# 4       4  7  9
# 5       5  4  6
# 6       6  4  3
# 7       7  6  1
# 8       8  8  4
# 9       9  3  2
# 10     10  3  2
# 11     11  7  3
# 12     12  4  6
# ...
```

Let's imagine, we want to group data for each `a` then subtract `b` values sequentially row by row. `order` provides us with extra information about the occurrence of the records. In a real-world example, a column such as `created_at` might replace `order`.

At first, I handled it quite nicely and it was easy to follow. Simply put, group data by `a` then get the diff of column `b`:

```py
def get_diff(df):
    raw = df.copy()
    # sort values to make sure that it respects occurence
    raw.sort_values(['a', 'order'], inplace=True)
    raw['c'] = raw.groupby('a')['b'].diff()
    return raw.sort_index()
```

Let's discover the results of sample data to verify it does what I wanted:

```py
res1 = get_diff(ex1)
#     order  a  b    c
# 0       0  9  7  NaN
# 1       1  5  1  NaN
# 2       2  5  3  2.0
# 3       3  9  8  1.0
# 4       4  7  9  NaN
# ...

# or let's see for group one only
res1.query('a==1')
    order  a  b    c
# 14     14  1  6  NaN
# 17     17  1  5 -1.0
# 31     31  1  7  2.0
# 48     48  1  6 -1.0
```

That is pretty much it, `NaN` for the first record as I cannot subtract it from and others do as I wanted. (`6-5=-1`; `7-5=2`; `6-7=1`) It looks all good and it runs smoothly.

## The problem with the simple approach

Even though, it is neat and runs smoothly equivalent of the above snippets shows poor performance. It increased the completion time of workflow by around 25% comparing to before where I did not have such a problem to solve.

## Alternative approach presenting better performance

I came up with a way easy but not as elegant solution. Instead of groping the data frame and calculating `diff`s over over groups, I handled it single `diff` operation. Here is the snippet:

```py
def get_diff_alternative(df):
    raw = df.copy()
    raw.sort_values(['a', 'order'], inplace=True)
    raw['is_first'] = (raw.a.shift(1) != raw.a)
    raw['c'] = raw.b.diff()
    raw['d'] = raw.c.where(~raw.is_first, np.nan)
    raw.drop(columns = 'is_first')
    return raw

res1_alternative = get_diff_alternative(ex1)
#     order  a  b    c
# 0       0  9  7  NaN
# 1       1  5  1  NaN
# 2       2  5  3  2.0
# 3       3  9  8  1.0
# 4       4  7  9  NaN
# ...

# compare two results after filling NaN
comp = res1_alternative.fillna(999)  == res1.fillna(999)
# True
```

The alternative solution does include a new column, calculating some virtual boolean then finally gets the difference only once instead of getting difference over groups.

## Impact on performance

In production, the alternative approach has shown significant improvement in performance (almost no additional time spent). While writing, this article I wanted to understand what is the reason behind it and what brought such difference.

### Small data frame with few groups

```py
ex2 = generate_sample(1000, 10)
timeit get_diff(ex2)
# 5.29 ms ± 330 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
timeit get_diff_alternative(ex2)
# 4.88 ms ± 305 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

ex3 = generate_sample(100000, 10)
timeit get_diff(ex3)
# 35.4 ms ± 312 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
timeit get_diff_alternative(ex3)
# 37.8 ms ± 742 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
```

So when data is small with only a few unique groups, the difference in performance is close to zero.

### Small data frame with many groups

```py
ex4 = generate_sample(1000, 500)
timeit get_diff(ex4)
# 78 ms ± 1.55 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
timeit get_diff_alternative(ex4)
# 4.41 ms ± 172 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
```

Now that data has a relatively larger number of unique groups, performance seems slightly better but the difference remains in a matter of microseconds.

### Middle-size data frame with many groups

```py
ex5 = generate_sample(1000000, 10000)
timeit get_diff(ex5)
# 2.41 s ± 45.6 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
timeit get_diff_alternative(ex5)
# 535 ms ± 5.23 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

Once we start having 1M rows with many groups(n/100), the improvement in the performance is quite noticeable.

### Big(?) data frame with many groups

Disclaimer: I don't mean fancy-fancy big-data here. Just more rows than my previous examples :)

```py
ex6 = generate_sample(10000000, 100000)
timeit get_diff(ex6)
30.8 s ± 377 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
timeit get_diff_alternative(ex6)
9.68 s ± 85 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

The alternative method looks much preferable on data with 10M rows with 100K unique groups. More than 3 times faster and differences are not negligible.

## Final thoughts

It seems like the main performance issue is about having many groups. As we are calculating `diff`s over each group, this indeed makes some sense.

So if you happen to have a dataset that is **big enough** where each group has a few data points/rows (in other words with a **large number of unique groups**) and you want to calculate discrete differences of elements over group, the alternative approach seems favored option even though it has relatively uglier syntax.

I guess similar approaches can be followed for operations other than `diff` as well:

- Percentage change of a column (`pct_change`)
- Cumulative operations on a column over group (`cumsum`, `cummax`, `cummin` e.g.)

That is it for now. Thanks for reading.
