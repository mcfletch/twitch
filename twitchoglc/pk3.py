"""Unpack .pk3 files for rendering

pk3 files generally look like this:

    maps/X.bsp
    textures/*/*.tga
    levelshots/*.jpg
"""
from __future__ import absolute_import
from fnmatch import fnmatch

try:
    unicode
except NameError:
    unicode = str
import os, zipfile, tempfile, hashlib

MAPS_DIR = os.path.expanduser("~/.cache/twitch/maps")


def escape_path(fn):
    throwaway_directory = "/tmp/junk/though/"
    test_fn = os.path.normpath(os.path.join(throwaway_directory, fn))
    return os.path.relpath(test_fn, throwaway_directory).startswith("../")


def scan_for_escape_paths(zipfile):
    """Scan zipfile's ZipInfo for paths that would escape the unpack directory"""
    for info in zipfile.infolist():
        if escape_path(info.filename):
            raise IOError(
                "Potentially malicious zip entry found (references file outside directory), aborting"
            )
        yield info


def key(url):
    """Trivial mechanism to hash URL into a unique key"""
    return hashlib.sha1(
        url.encode("utf8") if isinstance(url, unicode) else url
    ).hexdigest()


def unpack_directory(key=None):
    """Calculate and create the unpacking directory for the given key"""
    if key:
        path = os.path.join(MAPS_DIR, key)
        if not os.path.exists(path):
            os.makedirs(path)
    else:
        path = tempfile.mkdtemp(prefix="twitch", suffix="pk3")
    return path


def bsp_by_pattern(bsps, pattern):
    for bsp in sorted(bsps):
        if fnmatch(os.path.basename(bsp), pattern):
            return bsp
    return None


def unpack(pk3, directory, no_recurse=False, resources=False, bsp_name=None):
    """Unpack a .pk3 file into directory for loading

    directory = key( download_url )
    bsp_file = unpack( filename, directory )

    returns bsp_file (absolute path location)
    """
    bsps = []
    pk3s = []
    zip = zipfile.ZipFile(pk3, mode="r")
    for info in scan_for_escape_paths(zip):
        if os.path.splitext(info.filename)[1].lower() == ".bsp":
            bsps.append(os.path.join(directory, info.filename))
        elif os.path.splitext(info.filename)[1].lower() == ".pk3":
            pk3s.append(os.path.join(directory, info.filename))
    if pk3s and not no_recurse:
        zip.extractall(directory)
        bsp = None
        for pk3 in pk3s:
            return unpack(pk3, directory, no_recurse=True, resources=resources)
    if (not resources) and not bsps:
        raise IOError("""Did not find any .bsp files in the .pk3 file""")
    elif (not resources) and len(bsps) > 1:

        def available_bsps():
            return ", ".join(sorted([os.path.basename(x) for x in bsps]))

        if bsp_name:
            bsp = bsp_by_pattern(bsps, bsp_name)
            if not bsp:
                raise IOError(
                    "Did not find bsp matching %r, found:\n\t%s"
                    % (bsp_name, available_bsps())
                )
            bsps = [bsp]
        else:
            raise IOError(
                """Found %s .bsp files, specify the bsp_name to load from the pk3 file: \n\t%s"""
                % (len(bsps), available_bsps())
            )
    zip.extractall(directory)
    return bsps[0] if bsps else None
