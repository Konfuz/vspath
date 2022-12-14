# vspath
a pathfinder for vintagestory

Work in Progress.

## Usage
Import at least one datasource, `points_of_interest.tsv` from automaps local files, or
[translocators_lines.geojson](https://aurafurymap.ga/translocators_lines.geojson) from the [aurafury webmap](https://aurafurymap.ga/)

Refer to commandline documentation with `./vspath.py -h`


## Known Issues

* Performance at long-distances is poor and leads to suboptimal results

## Temp
```
INFO:root:0.0% Progress
DEBUG:root:best distance 31000 with 4 waypoints. Took 0.80s
DEBUG:root:best distance 30535 with 4 waypoints. Took 0.80s
DEBUG:root:best distance 30180 with 4 waypoints. Took 0.80s
DEBUG:root:best distance 29822 with 4 waypoints. Took 0.80s
DEBUG:root:best distance 28798 with 4 waypoints. Took 0.80s
DEBUG:root:best distance 26296 with 4 waypoints. Took 0.80s
DEBUG:root:best distance 25923 with 4 waypoints. Took 0.80s
DEBUG:root:best distance 25434 with 4 waypoints. Took 0.80s
DEBUG:root:best distance 24601 with 4 waypoints. Took 0.80s
DEBUG:root:best distance 22471 with 5 waypoints. Took 0.80s
DEBUG:root:best distance 22066 with 7 waypoints. Took 0.80s
DEBUG:root:best distance 20858 with 7 waypoints. Took 0.81s
DEBUG:root:best distance 20750 with 8 waypoints. Took 0.99s
DEBUG:root:best distance 19784 with 8 waypoints. Took 1.02s
DEBUG:root:best distance 19492 with 8 waypoints. Took 1.64s
DEBUG:root:best distance 19381 with 9 waypoints. Took 2.18s
INFO:root:1.6129032258064515% Progress
INFO:root:3.225806451612903% Progress
DEBUG:root:best distance 18481 with 7 waypoints. Took 9.93s
DEBUG:root:best distance 18373 with 8 waypoints. Took 10.11s
DEBUG:root:best distance 17407 with 8 waypoints. Took 10.14s
INFO:root:4.838709677419354% Progress
INFO:root:6.451612903225806% Progress
DEBUG:root:best distance 17369 with 7 waypoints. Took 17.08s
DEBUG:root:best distance 17296 with 8 waypoints. Took 19.67s
INFO:root:8.064516129032258% Progress
INFO:root:9.677419354838708% Progress
INFO:root:11.29032258064516% Progress
INFO:root:12.903225806451612% Progress
DEBUG:root:best distance 16462 with 7 waypoints. Took 29.47s
DEBUG:root:best distance 16297 with 11 waypoints. Took 34.83s
INFO:root:14.516129032258064% Progress
DEBUG:root:best distance 15958 with 6 waypoints. Took 58.35s
DEBUG:root:best distance 15945 with 6 waypoints. Took 58.35s
DEBUG:root:best distance 15373 with 6 waypoints. Took 58.35s
DEBUG:root:best distance 14784 with 8 waypoints. Took 58.35s
DEBUG:root:best distance 13760 with 8 waypoints. Took 58.36s
DEBUG:root:best distance 13377 with 8 waypoints. Took 58.38s
DEBUG:root:best distance 13011 with 8 waypoints. Took 59.30s
DEBUG:root:best distance 12938 with 9 waypoints. Took 61.83s
INFO:root:16.129032258064516% Progress
INFO:root:17.741935483870968% Progress
INFO:root:19.354838709677416% Progress
INFO:root:20.96774193548387% Progress
DEBUG:root:best distance 12692 with 8 waypoints. Took 76.47s
DEBUG:root:best distance 12309 with 8 waypoints. Took 76.49s
DEBUG:root:best distance 11415 with 8 waypoints. Took 77.45s
DEBUG:root:best distance 11342 with 9 waypoints. Took 79.13s
INFO:root:22.58064516129032% Progress
INFO:root:24.193548387096772% Progress
INFO:root:25.806451612903224% Progress
INFO:root:27.419354838709676% Progress
INFO:root:29.032258064516128% Progress
DEBUG:root:best distance 11176 with 8 waypoints. Took 93.40s
DEBUG:root:best distance 11103 with 9 waypoints. Took 95.07s
INFO:root:30.64516129032258% Progress
DEBUG:root:best distance 11041 with 9 waypoints. Took 110.34s
DEBUG:root:best distance 10557 with 8 waypoints. Took 110.91s
DEBUG:root:best distance 10484 with 9 waypoints. Took 112.17s
INFO:root:32.25806451612903% Progress
INFO:root:33.87096774193548% Progress
INFO:root:35.483870967741936% Progress
INFO:root:37.096774193548384% Progress
DEBUG:root:best distance 10381 with 8 waypoints. Took 127.37s
DEBUG:root:best distance 10285 with 8 waypoints. Took 127.37s
DEBUG:root:best distance 10234 with 8 waypoints. Took 166.51s
INFO:root:38.70967741935483% Progress
INFO:root:40.32258064516129% Progress
DEBUG:root:best distance 10218 with 12 waypoints. Took 225.73s
INFO:root:41.93548387096774% Progress
INFO:root:43.54838709677419% Progress
INFO:root:45.16129032258064% Progress
INFO:root:46.774193548387096% Progress
INFO:root:48.387096774193544% Progress
INFO:root:50.0% Progress
DEBUG:root:best distance 10147 with 9 waypoints. Took 253.79s
DEBUG:root:best distance 10074 with 10 waypoints. Took 256.23s
DEBUG:root:best distance 9957 with 8 waypoints. Took 265.54s
DEBUG:root:best distance 9231 with 9 waypoints. Took 265.87s
DEBUG:root:best distance 9172 with 7 waypoints. Took 265.92s
DEBUG:root:best distance 8955 with 7 waypoints. Took 265.92s
DEBUG:root:best distance 8859 with 7 waypoints. Took 265.92s
DEBUG:root:best distance 8817 with 9 waypoints. Took 275.29s
DEBUG:root:best distance 8815 with 9 waypoints. Took 275.42s
DEBUG:root:best distance 8477 with 9 waypoints. Took 345.88s
DEBUG:root:best distance 8471 with 10 waypoints. Took 346.46s
DEBUG:root:best distance 7403 with 9 waypoints. Took 346.96s
DEBUG:root:best distance 7330 with 10 waypoints. Took 349.17s
DEBUG:root:best distance 6200 with 9 waypoints. Took 349.70s
DEBUG:root:best distance 6058 with 9 waypoints. Took 349.78s
INFO:root:51.61290322580645% Progress
INFO:root:53.2258064516129% Progress
INFO:root:54.83870967741935% Progress
DEBUG:root:best distance 6055 with 10 waypoints. Took 400.24s
DEBUG:root:best distance 4925 with 9 waypoints. Took 400.71s
DEBUG:root:best distance 4783 with 9 waypoints. Took 400.86s
INFO:root:56.4516129032258% Progress
INFO:root:58.064516129032256% Progress
INFO:root:59.677419354838705% Progress
INFO:root:61.29032258064516% Progress
INFO:root:62.90322580645161% Progress
INFO:root:64.51612903225806% Progress
INFO:root:66.12903225806451% Progress
INFO:root:67.74193548387096% Progress
INFO:root:69.35483870967741% Progress
INFO:root:70.96774193548387% Progress
INFO:root:72.58064516129032% Progress
INFO:root:74.19354838709677% Progress
INFO:root:75.80645161290322% Progress
INFO:root:77.41935483870967% Progress
INFO:root:79.03225806451613% Progress
INFO:root:80.64516129032258% Progress
INFO:root:82.25806451612902% Progress
INFO:root:83.87096774193547% Progress
INFO:root:85.48387096774194% Progress
INFO:root:87.09677419354838% Progress
INFO:root:88.70967741935483% Progress
INFO:root:90.32258064516128% Progress
INFO:root:91.93548387096773% Progress
INFO:root:93.54838709677419% Progress
INFO:root:95.16129032258064% Progress
INFO:root:96.77419354838709% Progress
INFO:root:98.38709677419354% Progress
Route is optimal!
Did 755154 Investigations
You are starting at (-19481, 20536)
Move 122m W to (-19585, 20518) and Teleport to (-13736, 13385)
Move 314m E to (-13457, 13350) and Teleport to (-7131, 5505)
Move 444m S to (-7074, 5892) and Teleport to (-290, 4463)
Move 296m NE to (-155, 4302) and Teleport to (7808, 3487)
Move 744m W to (7185, 3366) and Teleport to (13616, 6712)
Move 213m ENE to (13750, 6633) and Teleport to (11287, 9947)
Move 501m SSW to (11179, 10340) and Teleport to (13104, 15253)
Move 2149m E to your destination (15000, 15000).
The route is 4.78km long and uses 7 hops.
```
