"""Renderer for a Twitch node (Quake III style BSP map)"""
import logging,numpy, sys
from twitch import brushmodel
from OpenGL.GL import *
from OpenGLContext.scenegraph import imagetexture
from OpenGLContext import texture

class Brush( brushmodel.Brush ):
    """Sub-class with rendering functionality for Brushes"""
    sky = False
    
    NO_DRAW_PROPERTIES = [
        'nodraw',
        'areaportal',
        'clusterportal',
        'donotenter',
    ]
    def __init__( self, *args, **named ):
        super(Brush,self).__init__(*args,**named)
        self.textures = {}
        for prop in self.NO_DRAW_PROPERTIES:
            getattr( self, prop )
            self.nodraw = True
        if 'cull' in self.surface_params:
            self.cull = self.surface_params['cull']
    def compile_textures( self ):
        for id,map in self.images.items():
            self.textures[id] = imagetexture.ImageTexture()
            self.textures[id].setImage( map )
    def render( self, visible=True, lit=False, mode=None ):
        pass
#        if self.suites:
#            for suite in self.suites:
#                if suite.
    def disable( self ):
        pass
class Lightmap( object ):
    texture = None
    def __init__( self, id, data ):
        self.id = id 
        self.data = data 
    def render( self, visible=True, lit=False, mode=None ):
        glActiveTexture( GL_TEXTURE1 )
        if not self.texture:
            self.texture = texture.Texture(format=GL_RGB)
            self.texture.store( 3, GL_RGB, 128,128, self.data )
        self.texture()
