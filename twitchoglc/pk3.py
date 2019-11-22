"""Unpack .pk3 files for rendering

pk3 files generally look like this:

    maps/X.bsp
    textures/*/*.tga
    levelshots/*.jpg
"""
from __future__ import absolute_import
try:
    unicode 
except NameError:
    unicode = str
import os, zipfile, tempfile, hashlib

def escape_path( fn ):
    throwaway_directory = '/tmp/junk/though/'
    test_fn = os.path.normpath( 
        os.path.join( throwaway_directory, fn )
    )
    return os.path.relpath( test_fn, throwaway_directory ).startswith( '../' )

def scan_for_escape_paths( zipfile ):
    """Scan zipfile's ZipInfo for paths that would escape the unpack directory
    """
    for info in zipfile.infolist():
        if escape_path( info.filename ):
            raise IOError( "Potentially malicious zip entry found (references file outside directory), aborting")
        yield info

def key( url ):
    """Trivial mechanism to hash URL into a unique key"""
    return hashlib.sha1( 
        url.encode('utf8') if isinstance(url,unicode) else url 
    ).hexdigest()

def unpack_directory( key=None ):
    """Calculate and create the unpacking directory for the given key
    """
    if key:
        path = os.path.join( os.path.expanduser( '~/.cache/twitch/maps' ), key )
        if not os.path.exists( path ):
            os.makedirs( path )
    else:
        path = tempfile.mkdtemp( prefix='twitch', suffix='pk3' )
    return path
        
def unpack( pk3, directory, no_recurse=False ):
    """Unpack a .pk3 file into directory for loading

    directory = key( download_url )
    bsp_file = unpack( filename, directory )
    
    returns bsp_file (absolute path location)
    """
    bsps = []
    pk3s = []
    zip = zipfile.ZipFile( pk3, mode='r' )
    for info in scan_for_escape_paths( zip ):
        if os.path.splitext( info.filename )[1].lower() == '.bsp':
            bsps.append( os.path.join( directory, info.filename) )
        elif os.path.splitext( info.filename )[1].lower() == '.pk3':
            pk3s.append( os.path.join( directory, info.filename) )
    if pk3s and not no_recurse:
        zip.extractall(directory)
        bsp = None
        for pk3 in pk3s:
            return unpack(pk3, directory, no_recurse=True)
    if not bsps:
        raise IOError( """Did not find any .bsp files in the .pk3 file""" )
    elif len( bsps ) > 1:
        raise IOError( """Found %s .bsp files, don't know how to handle that yet"""%( len(bsps)))
    zip.extractall( directory )
    return bsps[0]


