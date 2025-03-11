# jdep
[![GHA](https://github.com/lwa-project/jdep/actions/workflows/main.yml/badge.svg)](https://github.com/lwa-project/jdep/actions/workflows/main.yml)

jdep (Jovian Decametric Emission Probability) is a Python wrapper around Figure 1
of [Zarka et al. (2018, A&A, 618, A84)](https://www.aanda.org/articles/aa/full_html/2018/10/aa33586-18/aa33586-18.html)
that is designed to make it easier to find when Jupiter might be emission below
40 MHz and determine which emission regions (Io or non-Io) are likely.

jdep has access to:
 * a probability map of *any* decametric emission as a function of Jupiter's
   central meridian longitude (CML) and Io phase
 * a region bit mask for Io events as a function of CML and Io phase
 * a probability map of non-Io emission as a function of CML and the phase of
   Ganymede

## Usage:
To get the probability of any emission on a given date/time:
```
import jdep
jdep.get_get_dam_probability('2025/3/10 00:00:00', emission_type='all')
```
or you can limit it to non-Io emission with:
```
jdep.get_get_dam_probability('2025/3/10 00:00:00', emission_type='non-io')
```

When there is emission likely (>10% for any emission; >5% for non-Io emission)
you can also get a list of likely emission regions with:
```
jdep.get_dam_regions('2025/3/10 00:00:00', emission_type='all')
```

jdep also includes a few plotting tools to help visualize the data in the `jdep.plot`
module.  To plot the 2D probability map for any emission and label Jupiter's
location in CML-Io phase space:
```
import jdep.plot
from matplotlib import pyplot as plt
fig = jdep.plot.plot_dam_probability(emission_type='all')
jdep.plot.plot_jupiter_location(fig, '2025/3/10 00:00:00')
plt.show()
```

## Caveats
These have been extracted from Figure 1 of Zarka et al. using either
`jdep.backend.extract_map` for the probability maps or the interactive
`jdep.backend.define_regions` for the bit masks.  Since these were extracted
from a published figure rather than the underlying data there are a few things
to keep in mind:
 1. The probability range is approximate.  Figure 1(a) has a maximum probability
    of ~65.3% and 1(b) 17%[^1].
 2. Interpolation was used to estimate the probability values hidden under the
    region outlines and labels in the figures.
 3. The extracted regions of Io and non-Io emission are done using an interactive
    tool and do not have the exact same boundaries as the outlines in the figure.
    
In addition the `jdpe.get_jupter_cml()` function does not exactly match what you
get for the CML from [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/app.html).
From my testing the values are within +/- 1 degree over the period of Jan 2000
to Dec 2075.
    
[^1]: These two values are slightly higher than the maximum marking in the
      respective colorbars.  I assumed that the tick mark for the label
      corresponded to the bottom of the label as in the case for the 0% label.
