---
layout: post
title: "Pandas: Group and aggregate when some data is missing"
author: "bhakyuz"
tags: ["pandas", "group-by", "missing-data"]
---

While crunching data, now and then we group data based on certain variables(usually dimensions) and generate some summarized variables(usually metrics).

`pandas` usually works quite nicely but in some cases, results are not exactly as we expect. I'll be focusing on grouping and aggregating when there are some missing values in our dataset.

To make a good example let's start with the perfect case e.g. everything works as we have imagined.

```py
raw = pd.DataFrame({
    'a':[1,2,2,3,3,3,4,4,4,4,5,5,5,5,5],
    'b':[1,1,1,1,1,1,1,1,1,1,2,2,2,2,2],
    'c':[1,1,1,1,1,1,1,1,1,1,2,2,2,2,2],
})
# group by a,b and get the sum of c
summarized = raw.groupby(['a','b']).agg('sum').reset_index()
summarized
#    a  b  c
# 0  1  1  1
# 1  2  1  2
# 2  3  1  3
# 3  4  1  4
# 4  5  2  5
```

## Summarizing data with missing values

Now that we know it is working well for 'clean' data, let's see how it looks for almost the same data with some missing values.

### Missing values on metrics

When missing data is on the columns that we want to aggregate some values(e.g. metrics), it usually works fine.

```py
raw2 = pd.DataFrame({
    'a':[1,2,2,3,3,3,4,4,4,4,5,5,5,5,5],
    'b':[1,1,1,1,1,1,1,1,1,1,2,2,2,2,2],
    'c':[np.nan,np.nan,1,1,1,1,1,1,1,1,2,2,2,2,2],
})

# group by a,b and get the sum of c
summarized2 = raw2.groupby(['a','b']).agg('sum').reset_index()
summarized2
#    a  b     c
# 0  1  1   0.0
# 1  2  1   1.0
# 2  3  1   3.0
# 3  4  1   4.0
# 4  5  2  10.0
```

We just need to make sure our aggregator function (`sum` in our example) is handling correctly missing values. In the following example, our second group also has `NaN` as our revised `sum` function is handling `NaN` values differently.

```py
summarized2_2 = raw2.groupby(['a','b']).agg(lambda x: x.sum(skipna=False)).reset_index()
summarized2_2
#    a  b     c
# 0  1  1   NaN
# 1  2  1   NaN
# 2  3  1   3.0
# 3  4  1   4.0
# 4  5  2  10.0
```

### Missing values on dimensions

When the missing values are on the dimension that we grouping data by, we come across a more surprising issue. Dimensions that includes any missing values are silently dropped.

```py
raw3 = pd.DataFrame({
    'a':[1,2,2,3,3,3,4,4,4,4,5,5,5,5,5],
    'b':[np.nan,1,1,1,1,1,1,1,1,1,2,2,2,2,2],
    'c':[1.1,1.1,1,1,1,1,1,1,1,1,2,2,2,2,2],
})

# group again by a,b and get the sum of c
summarized3 = raw3.groupby(['a','b']).agg('sum').reset_index()
print(summarized3)
summarized3
   a    b     c
0  2  1.0   2.1
1  3  1.0   3.0
2  4  1.0   4.0
3  5  2.0  10.0
```

After summarizing data, our first group (`(1, np.nan)`) is disappeared (4 rows in the last case vs. 5 rows in previous summarized data). If we don't pay enough attention or if we are not aware that some values might be missing in the raw data, this might cost us quite expensive. The final results might even be empty.

To overcome the issue, we can fill first `NaN` values then put replace them again as `NaN` as in the following example.

```py
summarized3_2 = raw3.fillna('something').groupby(['a','b']).agg('sum').reset_index().replace('something', np.nan)
summarized3_2
```

Notice that the above findings occur while working with pandas 1.1.0. A new parameter is added in `groupby` method as `dropna`. This seems to solve the problem at its root.

## What other problems?

I have also been having some troubles with the indexes while I was trying to group by on empty data frames. I wanted to provide some hints about that, too but I could not constantly reproduce the errors. So nothing to add for no now about that. It might be the topic of another post.

For information above examples are done with pandas 1.0.5:

```py
import pandas as pd
pd.show_versions()
# INSTALLED VERSIONS
# ------------------
# commit           : None
# python           : 3.8.7.final.0

# pandas           : 1.0.5
# numpy            : 1.20.1
```

Thanks for reading.

(last edited on 2021/02/15)
