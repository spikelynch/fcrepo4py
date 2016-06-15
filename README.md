fcrepo4.py
==========

A simple Python 3 (not Python 2!) interface to Fedora Commons 4.

## Install

To install:
* Get yourself into a Python 3 virtual environment
* Get the library and install it:

    git clone https://codeine.research.uts.edu.au/eresearch/fcrepo4py.git

    cd fcrepo4py
  
    python setup.py install
  
## Usage

Sample usage:

    import fcrepo4

    repo = fcrepo4.Repository(config='config.yml)

    container = repo.get(path)
    b = container.add_binary(source='file.jpg')
    
## Sample code

See this [sample script to upload spreadsheet data to Fedora 4](https://github.com/ptsefton/spreadsheet-to-fedora-commons-4).
