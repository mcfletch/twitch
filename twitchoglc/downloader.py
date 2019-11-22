"""Utility to pull a pk3 file from the internet and unpack it for viewing"""
import requests
import os, shutil, logging, glob
from six.moves import urllib_parse
from . import pk3
log = logging.getLogger(__name__)

def pull_pk3(url, force=False):
    key = pk3.key(url)
    directory = pk3.unpack_directory(key)
    bsps = sorted(glob.glob(os.path.join(directory,'maps/*.bsp')))
    if (not bsps) or force:
        source = os.path.join(directory,'source-file')
        url_file = os.path.join(directory,'.url')
        if force or not os.path.exists(source):
            log.info("Downloading target pk3: %r", url)
            parsed = urllib_parse.urlparse(url)
            if parsed.scheme not in ('http','https'):
                raise ValueError('Currently only http/https is supported')
            response = requests.get(url)
            response.raise_for_status()
            try:
                download_file = source
                with open(download_file,'wb') as fh:
                    for chunk in response.iter_content(1024*256):
                        fh.write(chunk)
                with open(url_file,'w') as fh:
                    fh.write(url)
                return pk3.unpack(download_file, directory)
            except Exception as err:
                log.error("Failure downloading, removing the cache directory: %s",err) 
                shutil.rmtree(directory)
                raise
        else:
            log.info("Unpacking the existing source: %r", source)
            return pk3.unpack(source,directory)
            # shutil.rmtree(directory)
    if len(bsps) > 1:
        log.warning('More than one bsp in %s, using arbitrary choice', url)
    return bsps[0]
            
    
def get_options():
    import argparse 
    parser = argparse.ArgumentParser(
        description='Download PK3 files from the internet and unpack locally'
    )
    parser.add_argument(
        '-f','--force',
        help='Force re-download and unpack of the resource',
        default=False,
        action='store_true',
    )
    parser.add_argument(
        'url',help='The http/https url to download to the local cache',
    )

    return parser
def main():
    logging.basicConfig(level=logging.DEBUG)
    options = get_options().parse_args()
    bsp = pull_pk3(options.url,force=options.force)
    log.info("Downloaded to %s", bsp)