#!/usr/bin/env python
"""Installs twitch using setuptools

Run:
    python setup.py install
to install the package from the source archive.
"""
try:
	from setuptools import setup
except ImportError, err:
    from distutils.core import setup
import sys, os
sys.path.insert(0, '.' )

def find_version( ):
    for line in open( os.path.join(
        'twitch','__init__.py',
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
    extraArguments = {
        'classifiers': [
            """License :: OSI Approved :: BSD License""",
            """Programming Language :: Python""",
            """Topic :: Software Development :: Libraries :: Python Modules""",
            """Topic :: Multimedia :: Graphics :: 3D Rendering""",
            """Intended Audience :: Developers""",
            """Environment :: X11 Applications""",
            """Environment :: Win32 (MS Windows)""",
        ],
        'download_url': "http://pypi.python.org/pypi/Twitch",
        'keywords': 'PyOpenGL,OpenGL,Context,OpenGLContext,render,3D,TrueType,text,VRML,VRML97,scenegraph',
        'platforms': ['Win32','Linux','OS-X','Posix'],
    }
    ### Now the actual set up call
    setup (
        name = "Twitch",
        version = version,
        description = "Quake-style PK3/BSP(3) file loader",
        author = "Mike C. Fletcher",
        author_email = "mcfletch@users.sourceforge.net",
        url = "https://launchpad.net/twitch",
        license = "BSD",

        packages = list(find_packages('twitch')),
        # need to add executable scripts too...
        options = {
            'sdist': {
                'formats':['gztar','zip'],
            }
        },
        # non python files of examples      
        **extraArguments
    )
