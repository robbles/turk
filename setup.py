__author__="Rob O'Dwyer"
__date__ ="$Nov 11, 2009 5:34:40 PM$"

from setuptools import setup,find_packages

setup (
  name = 'Turk',
  version = '0.1',
  packages = find_packages(),

  # Declare your packages' dependencies here, for eg:
  install_requires=['foo>=3'],

  # Fill in these to make your Egg ready for upload to
  # PyPI
  author = 'rob',
  author_email = '',

  summary = 'Just another Python package for the cheese shop',
  url = '',
  license = '',
  long_description= 'Long description of the package',

  # could also include long_description, download_url, classifiers, etc.

  
)
