#!/usr/bin/env python
"""Installs twitchoglc using setuptools

Run:
    python setup.py install
to install the package from the source archive.
"""
from __future__ import absolute_import
try:
    from setuptools import setup
except ImportError as err:
    from distutils.core import setup
import sys, os
sys.path.insert(0, '.' )

def find_version( ):
    for line in open( os.path.join(
        'twitchoglc','__init__.py',
    )):
        if line.strip().startswith( '__version__' ):
            return eval(line.strip().split('=')[1].strip())
    raise RuntimeError( """No __version__ = 'string' in __init__.py""" )

version = find_version()

def is_package( path ):
    return os.path.isfile( os.path.join( path, '__init__.py' ))
def find_packages( root ):
    """Find all packages under this directory"""
    for path, directories, files in os.walk( root ):
        if is_package( path ):
            yield path.replace( '/','.' )

if __name__ == "__main__":
    ### Now the actual set up call
    setup (
        name = "twitchoglc",
        version = version,
        description = "Quake-style PK3/BSP(3) file loader",
        author = "Mike C. Fletcher",
        author_email = "mcfletch@users.sourceforge.net",
        url = "https://github.com/mcfletch/twitch",
        license = "BSD",

        packages = list(find_packages('twitchoglc')),
        # need to add executable scripts too...
        options = {
            'sdist': {
                'formats':['gztar'],
            },
            'bdist_wheel':{
                'universal': True,
            }
        },
        # non python files of examples
        install_requires=[
            'six',
            'OpenGLContext',
            'numpy',
            'pillow',
            'simpleparse',
        ],
        entry_points={
          'console_scripts':
              [
                'twitch-parse-bsp = twitchoglc.bsp:main',
                'twitch-viewer = twitchoglc.viewer:main',
                'twitch-downloader = twitchoglc.downloader:main',
            ]
        },
        classifiers= [
            """License :: OSI Approved :: BSD License""",
            """Programming Language :: Python :: 2""",
            """Programming Language :: Python :: 3""",
            """Topic :: Software Development :: Libraries :: Python Modules""",
            """Topic :: Multimedia :: Graphics :: 3D Rendering""",
            """Intended Audience :: Developers""",
            """Environment :: X11 Applications""",
            """Environment :: Win32 (MS Windows)""",
        ],
        download_url="http://pypi.python.org/pypi/OpenGLContext_twitch",
        keywords= 'PyOpenGL,OpenGL,Context,OpenGLContext,render,3D,TrueType,text,scenegraph',
    )
