import os
import ephem
import numpy as np
from datetime import datetime, timezone
from functools import lru_cache
from typing import Union, List, Optional

from astropy.time import Time


DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


PROBABILITY_MAP_ALL = np.load(os.path.join(DATA, 'probability_map_all.npy'))
PROBABILITY_MAP_NONIO = np.load(os.path.join(DATA, 'probability_map_nonio.npy'))

REGIONS_MAP_IO = np.load(os.path.join(DATA, 'region_bitmask_io.npy'))
REGIONS_MAP_NONIO = np.load(os.path.join(DATA, 'region_bitmask_nonio.npy'))

REGIONS_BITS = { 1: 'A',
                 2: "A'",
                 4: 'A"',
                 8: 'B',
                16: "B'",
                32: 'C',
                64: 'D'
               }


def _date_to_date(date: Union[str,datetime,float,Time]) -> Time:
    """
    Take in either:
     * a string containing an ISO 8601 time
     * a datetime instance
     * a MJD value as a float
     * of an astropy.time.Time instance
    and convert it to an astro.time.Time instances in the UTC scale.
    """
    
    if isinstance(date, str):
        # Strings are ISO 8601
        orig_date = date
        date = orig_date.replace('/', '-')
        
        match = False
        for format in ('iso', 'isot'):
            try:
                date = Time(date, format=format, scale='utc')
                match = True
                break
            except ValueError:
                pass
                
        if not match:
            raise ValueError(f"Cannot parse '{orig_date}' as either an ISO or ISO-T time")
            
    elif isinstance(date, datetime):
        # datetimes can either be naive or timezone-aware
        if date.tzinfo is None:
            date = Time(date, format='datetime', scale='utc')
        else:
            utc_datetime = date.astimezone(timezone.utc)
            utc_naive = utc_datetime.replace(tzinfo=None)
            date = Time(utc_naive, format='datetime', scale='utc')
            
    elif isinstance(date, float):
        # floats are MJD values
        date = Time(date, format='mjd', scale='utc')
        
    elif isinstance(date, Time):
        # astropy.time.Times are what we want, just make sure we are UTC
        date = date.utc
        
    else:
        raise TypeError("Unknown input type for date")
        
    return date


@lru_cache(maxsize=8)
def get_jupiter_cml(date: Union[str,datetime,float,Time]) -> float:
    """
    Given a date and time compute the central meridian longitude of system III
    and return that value in degrees.
    """
    
    # Get the JD
    date = _date_to_date(date)
    jd = date.jd
    
    # From https://www.projectpluto.com/grs_form.htm
    jup_mean = (jd - 2455636.938) * 360. / 4332.89709
    eqn_center = 5.55 * np.sin( np.deg2rad(jup_mean) )
    angle = (jd - 2451870.628) * 360. / 398.884 - eqn_center
    correction = 11 * np.sin( np.deg2rad(angle) ) \
                 + 5 * np.cos( np.deg2rad(angle) ) \
                 - 1.25 * np.cos( np.deg2rad(jup_mean) ) - eqn_center
    
    # -eqn_center seems to be needed to get values closer to what is shown
    # at https://jupiter-probability-tool.obspm.fr/
    cml = 138.41 + 870.4535567*jd + correction - eqn_center
    return cml % 360


@lru_cache(maxsize=8)
def get_io_phase(date: Union[str,datetime,float,Time]) -> float:
    """
    Given a date and time compute the phase of Io and return that value in
    degrees.
    """
    
    # Get the date and convert it to pyephem format
    date = _date_to_date(date)
    date = ephem.Date(date.iso)
    
    # Figure out where Io is
    io = ephem.Io()
    io.compute(date)
    
    phase = np.rad2deg(np.arctan2(io.x, -io.z))
    return phase % 360


@lru_cache(maxsize=8)
def get_ganymede_phase(date: Union[str,datetime,float,Time]) -> float:
    """
    Given a date and time compute the phase of Ganymede and return that value in
    degrees.
    """
    
    # Get the date and convert it to pyephem format
    date = _date_to_date(date)
    date = ephem.Date(date.iso)
    
    # Figure out where Ganymede is
    ga = ephem.Ganymede()
    ga.compute(date)
    
    phase = np.rad2deg(np.arctan2(ga.x, -ga.z))
    return phase % 360


@lru_cache(maxsize=8)
def get_dam_probability(date: Union[str,datetime,float,Time], emission_type: str='all') -> float:
    """
    Given a date and time compute the probability (0 to 100%) of decametric
    emission from Jupiter using Figure 1 of Zarka et al. 2018, A&A, 618, A84.
    The `emission_type` keyword allows you to select all emission (all) or
    non-Io emission (non-io).
    """
    
    if emission_type not in ('all', 'non-io'):
        raise ValueError(f"Uknown emission type selection '{emission_type}'")
        
    # This right here is why we decorate things with lru_cache
    # Get the CML and Io phase
    date = _date_to_date(date)
    cml = get_jupiter_cml(date)
    iphase = get_io_phase(date)
    gphase = get_ganymede_phase(date)
    
    # Sort out what to do
    if emission_type == 'all':
        map = PROBABILITY_MAP_ALL
        phase = iphase
    else:
        map = PROBABILITY_MAP_NONIO
        phase = gphase
    
    # Convert those to pixel coordiantes in the probablity map
    x = int(round(cml / 360 * (map.shape[0] - 1)))
    y = int(round((1 - phase / 360) * (map.shape[1] - 1)))
    
    # The probability map is slight higher resolution than the smoothed data in
    # Zarka et al. so take the median of a small window around the closest pixel
    return np.median(map[y-1:y+2, x-1:x+2])


def get_dam_regions(date: Union[str,datetime,float,Time], emission_type='io') -> List[str]:
    """
    Given a date and time determine what type of decamatric emission is likely
    using Figure 1 of Zarka et al. 2018, A&A, 618, A84.  The `emission_type`
    keyword allows you to select Io emission (io), non-Io emission (non-io), or
    both (all)
    
    .. note::  Probabilities of less than 10% for Io and 5% for non-Io are
               ignored.
    """
    
    if emission_type not in ('io', 'non-io', 'all'):
        raise ValueError(f"Uknown emission type selection '{emission_type}'")
        
    # Get the CML, Io phase, and emission probability
    date = _date_to_date(date)
    cml = get_jupiter_cml(date)
    iphase = get_io_phase(date)
    gphase = get_ganymede_phase(date)
    aprob = get_dam_probability(date, emission_type='all')
    nprob = get_dam_probability(date, emission_type='non-io')
    
    if emission_type == 'io' and aprob < 10:
        # If the "all" probability is too low (<10%) return an empty list
        return []
    elif emission_type == 'non-io' and nprob < 5:
        # If the non-Io probability is too low (<5%) return an empty list
        return []
    elif emission_type == 'all' and aprob < 5:
        return []
        
    regions = []
    for etype,phase,map in zip(('Io', 'non-Io'), (iphase, gphase), (REGIONS_MAP_IO, REGIONS_MAP_NONIO)):
        if emission_type == 'io' and etype != 'Io':
            continue
        elif emission_type == 'non-io' and etype != 'non-Io':
            continue
            
        # Something might happen so convert to pixel coordinates in the regions
        # bitmask map
        x = int(round(cml / 360 * (map.shape[0] - 1)))
        y = int(round((1 - phase / 360) * (map.shape[1] - 1)))
        
        # As with the probabilities, these regions are slightly higher resolution
        # than Zarka et al. so take the median of a small region
        bitmask = np.median(map[y-1:y+2, x-1:x+2])
        bitmask = int(round(bitmask))
        
        # Decode the bitmask
        for bit,label in REGIONS_BITS.items():
            if bitmask & bit:
                regions.append(f"{etype} {label}")
                
    # If after all that there isn't anything in regions, we must be in a
    # unlabeled non-Io emision region
    if len(regions) == 0:
        regions.append('non-Io')
        
    return regions
