"""Renderer for a Twitch node (Quake III style BSP map)"""
from __future__ import absolute_import
import OpenGL
#OpenGL.FULL_LOGGING = True
import logging,numpy, sys, threading
from OpenGLContext import testingcontext
from twitch import maprender
from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGLContext.scenegraph import imagetexture, shape, transform
from OpenGLContext.scenegraph.text import text
from OpenGLContext import texture
BaseContext = testingcontext.getInteractive()

class TwitchContext( BaseContext ):

    def __init__(self, *args, **named):
        self.target = named.pop('target')
        super(TwitchContext,self).__init__(*args,**named)

    def OnInit( self ):
        self.renderer = maprender.Map( self.target )
        threading.Thread( target=self.LoadAndRefresh ).start()
        # default near is far too close for 8 units/foot quake model size
        self.platform.setFrustum( near = 30, far=50000 )
        self.movementManager.STEPDISTANCE = 50

    def LoadAndRefresh( self ):
        self.renderer.load()
        self.triggerRedraw( False )
    def Render( self, mode = None):
        """Render the geometry for the scene."""
        BaseContext.Render( self, mode )
        if not mode.visible:
            return
        if self.renderer.loaded:
            glRotatef( -90, 1.0,0,0 )
            #glScalef( .01, .01, .01 )
            self.renderer.Render(mode)

def get_options():
    import argparse 
    parser = argparse.ArgumentParser(
        description='Renders a Quake III Style .pk3 file using OpenGLContext'
    )
    parser.add_argument(
        'target',help='A .bsp (or .pk3) file to (unpack and) parse',
    )
    return parser


def main():
    logging.basicConfig( level = logging.INFO )
    options = get_options().parse_args()
    if options.target.startswith('http://') or options.target.startswith('https://'):
        from . import downloader
        target = downloader.pull_pk3(options.target)
    else:
        target = options.target 
    TwitchContext.ContextMainLoop(target=target)
