import os
import glob
import shutil

from setuptools import setup, find_namespace_packages

setup(name                 = "jdep",
      version              = "0.1.0",
      description          = "Jovian Decametric Emission Prediction",
      long_description     = "Estimate pobability of Jovan decametric emission using results from Zarka et al. 2018, A&A, 618, A84.",
      author               = "J. Dowell",
      author_email         = "jdowell@unm.edu",
      license              = 'GPL',
      classifiers          = ['Development Status :: 4 - Beta',
                              'Intended Audience :: Science/Research',
                              'License :: OSI Approved :: GNU General Public License (GPL)',
                              'Topic :: Scientific/Engineering :: Astronomy'],
      packages             = find_namespace_packages(),
      scripts              = glob.glob('scripts/*.py'),
      include_package_data = True,
      python_requires      = '>=3.8',
      install_requires     = ['numpy', 'scipy', 'astropy', 'ephem', 'matplotlib'],
      zip_safe             = False
)
