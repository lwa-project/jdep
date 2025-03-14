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
        
    times, probs = [], []
    for i in range(24*4):
        t = f"{args.date} {i//4:02d}:{i%4 * 15:02d}:00"
        times.append(t)
        probs.append(jdep.get_dam_probability(t, emission_type=etype1))
        
    if etype1 == 'all':
        probs_to_keep = 30
    else:
        probs_to_keep = 10
        
    any_found = False
    for t,p in zip(times, probs):
        if p >= probs_to_keep:
            regions = jdep.get_dam_regions(t, emission_type=etype2)
            print(f"{t} with {p:.0f}% from {', '.join(regions)}")
            any_found = True
    if not any_found:
        print(f"Nothing found with an emission probability above {probs_to_keep:.0f}%")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='find times with the highest probabilities of Jovain decametric emission on particular UTC date',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('date', type=str,
                        help='UTC date as either YYYY/MM/DD or YYYY-MM-DD')
    parser.add_argument('--non-io', action='store_true',
                        help='only plot non-Io emission')
    args = parser.parse_args()
    main(args)
