#!/usr/bin/env python3

import argparse


import argparse
from datetime import datetime

import jdep
import jdep.plot

from matplotlib import pyplot as plt


def main(args):
    etype1, etype2 = 'all', 'io'
    if args.non_io:
        etype1, etype2 = 'non-io', 'non-io'
        
    # Probability map
    fig = jdep.plot.plot_dam_probability(emission_type=etype1)
    
    # Location of Jupiter on this probability map
    jdep.plot.plot_jupiter_location(fig, f"{args.date} 00:00:00", marker='s')
    jdep.plot.plot_jupiter_location(fig, f"{args.date} 00:15:00",
                                    date2=f"{args.date} 23:59:59",marker='o')
    
    # Emission regions and their labels
    if not args.no_regions:
        jdep.plot.plot_emission_regions(fig, emission_type=etype2)
        
    ax = fig.gca()
    ax.set_title(f"Emission Probability for {args.date}")
    plt.show()

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='plot the probability of Jovain decametric emission on particular UTC date',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('date', type=str,
                        help='UTC date as either YYYY/MM/DD or YYYY-MM-DD')
    parser.add_argument('--non-io', action='store_true',
                        help='only plot non-Io emission')
    parser.add_argument('--no-regions', action='store_true',
                        help='do not mark emission regions')
    args = parser.parse_args()
    main(args)
