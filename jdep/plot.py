import numpy as np
from scipy.ndimage import label as ndlabel
from typing import Union, Optional, List

from astropy.time import TimeDelta

from .dam import PROBABILITY_MAP_ALL, PROBABILITY_MAP_NONIO, REGIONS_MAP_IO, REGIONS_MAP_NONIO, REGIONS_BITS
from .dam import _date_to_date, get_jupiter_cml, get_io_phase

from matplotlib.figure import Figure
from matplotlib.backend_bases import FigureManagerBase
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib import pyplot as plt

# class PhaseFigure(Figure):
#     """
#     Wrapper around matplotlib.figure.Figure that is satellite phase-aware.
#     """
# 
#     _satellite = 'io'
# 
#     @property
#     def satellite(self):
#         return self._satellite
# 
#     @satellite.setter
#     def satellite(self, satellite):
#         if satellite not in ('io', 'ganymede'):
#             raise ValueError(f"Unknown satellite '{satellite}'")
#         self._satellite = satellite


# # Register the custom figure class with matplotlib
# def phase_figure_factory(*args, **kwargs):
#     # Create a new PhaseFigure instance
#     fig = PhaseFigure(*args, **kwargs)
# 
#     # Complete setup that plt.figure() would normally do
#     if kwargs.get('tight_layout', False):
#         fig.set_tight_layout(True)
# 
#     return fig

# Replace plt.figure with our factory
#plt._figure_original = plt.figure  # Store the original for later if needed
#plt.figure = phase_figure_factory


def plot_dam_probability(fig: Optional[Figure]=None, emission_type: str='all',
                         cmap: Optional[str]=None) -> Figure:
    """
    Plot the full 2D probability map as a function of central meridian longitude
    and satelite phase.  The `emission_type` keyword allows you to select all
    emission (all) or non-Io emission (non-io).
    """
    
    if emission_type not in ('all', 'non-io'):
        raise ValueError(f"Uknown emission type selection '{emission_type}'")
        
    if fig is None:
        fig = plt.figure()
    ax = fig.gca()
    
    if emission_type == 'all':
        fig.satellite = 'io'
        c = ax.imshow(PROBABILITY_MAP_ALL, vmin=0, vmax=60, extent=(0,360,0,360), cmap=cmap)
        ax.set_ylabel('Io Phase [$^\circ$]')
    else:
        fig.satellite = 'ganymede'
        c = ax.imshow(PROBABILITY_MAP_NONIO, vmin=0, vmax=15, extent=(0,360,0,360), cmap=cmap)
        ax.set_ylabel('Ganymede Phase [$^\circ$]')
    fig.colorbar(c, ax=ax, label='Probability')
    ax.set_xlabel('CML (System III) [$^\circ$]')
    
    return fig


def plot_jupiter_location(fig: Figure, date: Union[str,'datetime',float,'Time'],
                          date2: Optional[Union[str,'datetime',float,'Time']]=None,
                          marker='o', color='white'):
    """
    Given a figure created by plot_dam_probability() and a date/time, plot the
    location of Jupiter in the CML/satelite phase space.
    
    If date2 is also provided then a series of markers are plotted at 15 minute
    intervals between date and date2.
    """
    
    if date2 is None:
        date2 = date
        
    if fig.satellite == 'io':
        get_phase_func = get_io_phase
    else:
        get_phase_func = get_ganymede_phase
        
    cml = []
    phase = []
    d = _date_to_date(date)
    d1 = _date_to_date(date2)
    while d <= d1:
        cml.append(get_jupiter_cml(d))
        phase.append(get_phase_func(d))
        if len(cml) > 1:
            if abs(cml[-1] - cml[-2]) > 180 or abs(phase[-1] - phase[-2]) > 180:
                cml.insert(len(cml)-1, np.nan)
                phase.insert(len(phase)-1, np.nan)        
        d += TimeDelta(900, format='sec')
        
    ax = fig.gca()
    if len(cml) == 1:
        ax.scatter(cml, phase, marker=marker, color=color)
    else:
        ax.plot(cml, phase, linestyle='-', marker=marker, color=color)


def _find_edges(map: np.ndarray) -> np.ndarray:
    """
    Find the edge of a region in a binary mask and return a list of coordinates
    that define the edge.
    """
    
    edges = np.zeros_like(map)
    ni, nj = map.shape
    nz = np.where(map)
    for (i, j) in zip(*nz):
        if map[i, j] == 1 and (
            (i > 0 and map[i-1, j] == 0) or 
            (i < ni-1 and map[i+1, j] == 0) or 
            (j > 0 and map[i, j-1] == 0) or 
            (j < nj-1 and map[i, j+1] == 0)
        ):
            edges[i, j] = 1
            
    edges = np.where(edges)
    edgesi, edgesj = list(edges[0]), list(edges[1])
    path = []
    while edgesi:
        if len(path) == 0:
            ei, ej = edgesi[0], edgesj[0]
            path.append([ei,ej])
            del edgesi[0]
            del edgesj[0]
        else:
            dist2 = (path[-1][0] - edgesi)**2 + (path[-1][1] - edgesj)**2
            closest = np.argmin(dist2)
            if dist2[closest] > 300:
                path.append([np.nan, np.nan])
            ei, ej = edgesi[closest], edgesj[closest]
            path.append([ei,ej])
            del edgesi[closest]
            del edgesj[closest]
            
    path = np.array(path)
    path = path / map.shape[0] * 360
    path[:,0] = 360 - path[:,0]
    
    return path


def plot_emission_regions(fig: Optional[Figure]=None, emission_type: str='io',
                          color: str='white', linewidth: int=1,
                          label: bool=True) -> Figure:
    """
    Plot and optionally label the emission regions 2D emission probability map.
    The type of emission to be plotted is controlled by the `emission_type`
    keyword that accepts 'io' and 'non-io'.
    """
    
    if emission_type not in ('io', 'non-io'):
        raise ValueError(f"Uknown emission type selection '{emission_type}'")
        
    if fig is None:
        fig = plt.figure()
    elif emission_type == 'io' and fig.satellite != 'io':
        raise RuntimeError(f"Cannot plot Io emission regions on figure with Ganymedge phase")
    elif emission_type == 'non-io' and fig.satellite != 'ganymede':
        raise RuntimeError(f"Cannot plot non-Io emission regions on figure with Io phase")
    ax = fig.gca()
    
    if emission_type == 'io':
        regions_map = REGIONS_MAP_IO
        linestyles = {"A'": '--',
                      'A"': '--',
                      "B'": ':',
                      'D': '--'
                     }
        labels = {'A':  (240, 280),
                  "A'": (180, 170),
                  'A"': (330, 200),
                  'B':  ( 50,  60),
                  "B'": (190,  60),
                  'C':  ( 15, 270),
                  'D':  ( 60, 130)
                 }
        labels_c = (320, 270)
    else:
        regions_map = REGIONS_MAP_NONIO
        linestyles = {}
        labels = {'A':  (300, 180), 
                  'B':  (120, 110),
                  "B'": (180,  50),
                  'C':  ( 15, 270),
                  'D':  (100, 200)
                 }
        labels_c = (340, 270)
        
    for bit,label in REGIONS_BITS.items():
        map = (regions_map & bit) > 0
        if not map.any():
            continue
            
        edges = _find_edges(map)
        
        try:
            ls = linestyles[label]
        except KeyError:
            ls = '-'
            
        ax.plot(edges[:,1], edges[:,0], linestyle=ls, color=color, linewidth=linewidth)
        ax.text(*labels[label], label, color=color)
        if label == 'C':
            ax.text(*labels_c, label, color=color)
            
    return fig
