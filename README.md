# Spatial Inequality Index

<blockquote>
    Measure if *similar* individuals are being *similarly* treated.
</blockquote>

[![Publication](https://img.shields.io/badge/Publication-The%20Web%20Conference%202021-informational?logo=Google%20Scholar)](https://nunomota.github.io/assets/papers/www2021.pdf)
[![Documentation](https://img.shields.io/badge/Documentation-v1.0-orange?logo=Read%20the%20Docs)](https://nunomota.github.io/spatial-inequality/docs/)
[![Website](https://img.shields.io/badge/Website-Operational-green?logo=OpenStreetMap)](http://redistricting.mpi-sws.org)
[![Python](https://img.shields.io/badge/Python-v3.7+-blueviolet?logo=Python)](https://www.python.org/downloads/release/python-370/)

In this repository, we include all the necessary code to calculate the Spatial Inequality Index. This code was provided as part of our publication at The Web Conference 2021, [Fair Partitioning of Public Resources: Redrawing District Boundary to Minimize Spatial Inequality in School Funding](https://nunomota.github.io/assets/papers/www2021.pdf).

![Map](https://github.com/nunomota/spatial-inequality/blob/master/assets/redistricting_before_and_after.png?raw=true)

For anyone interested in using (or contributing to) our codebase, we provide complete [documentation](https://nunomota.github.io/spatial-inequality/docs/) of our `spatial_inequality` package. For anyone otherwise interested in visualizing the impact of our algorithm in school redistricting, we also provide an [interactive website](http://redistricting.mpi-sws.org).

## What is the Spatial Inequality Index?

The `Spatial Inequality Index`, as the name suggests, is an inequality index that measures statistical differences between individuals in a population. Whereas other inequality indices - like the [Gini Index](https://en.wikipedia.org/wiki/Gini_coefficient) - will compare every individual in a population with one another, the Spatial Inequality Index compares *similar* individuals (for some notion of *similarity*).

### How to calculate it?

Take a population of *N* individuals. For each individual *i* in the population, define their neighborhood *N<sub>i</sub>* (i.e., which other individuals should be considered as *similar*) and their benefit *y<sub>i</sub>* (i.e., how much of a given *resource* they have). The full index can then be calculated as such:

<p align="center">
<img width="400px" style="background-color:white !important;" src="https://github.com/nunomota/spatial-inequality/blob/master/assets/spatial_inequality_equation.png?raw=true">
</p>

The higher the difference observed between immediate neighbors, the higher the observed spatial inequality. You can find its (Python) implementation in both our [repository](https://github.com/nunomota/spatial-inequality/blob/master/spatial_inequality/auxiliary/inequality.py) and [documentation](https://nunomota.github.io/spatial-inequality/docs/auxiliary/inequality.html).

### When to use it?

In our study, we applied this concept to public schooling districts in the US. We considered (i) *individuals* as being districts, (ii) their *neighborhood* as their geographical neighbors and (iii) their *benefit* as the amount of funding (per-student) that they receive. Although we understand there are very valid reasons for different district to receive different amounts of funds, it still feels off that a school potentially meters away from being assigned to another district would get substantially lower/higher amount of funds than its immediate peers. By finding alternative districting strategies that minimize spatial inequality we prevent this from happening.

Besides our own use-case, however, the Spatial Inequality Index can be used any time one wants to measure if *similar* individuals are being *similarly* treated. For example, when recommender or add-delivery systems choose best-matching strategies between user profiles and a certain type of content, there are implicit notions of similarity. Similar users should be served similar type of content, so we can easily see this index as a benchmarking tool for such technologies. 
