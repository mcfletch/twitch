"""Renderer for a Twitch node (Quake III style BSP map)"""
from __future__ import absolute_import
import logging,numpy, sys
log = logging.getLogger( __name__ )
from . import brushmodel
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo
from OpenGLContext.scenegraph import imagetexture
from OpenGLContext import texture

CUBE_NAME_MAP = dict([
    ('rt','+x'),
    ('lf','-x'),
    ('ft','-z'),
    ('bk','+z'),
    ('up','+y'),
    ('dn','-y'),
])
CUBE_VERTICES =  numpy.array([
    -100.0,  100.0,  100.0,
    -100.0, -100.0,  100.0,
    100.0, -100.0,  100.0,
    100.0,  100.0,  100.0,
    -100.0,  100.0, -100.0,
    -100.0, -100.0, -100.0,
    100.0, -100.0, -100.0,
    100.0,  100.0, -100.0,
],'f')
CUBE_INDICES = numpy.array([
    3,2,1,0,
    0,1,5,4,
    7,6,2,3,
    4,5,6,7,
    4,7,3,0,
    1,2,6,5,
],'H')

def create_cube_texture( images ):
    tex = texture.CubeTexture( )
    translated_images = {}
    for key,img in images.items():
        if key in CUBE_NAME_MAP:
            translated_images[CUBE_NAME_MAP[key]] = img 
    tex.fromPIL( translated_images )
    
    return tex, cube_vert_vbo, cube_index_vbo, shader, vertex, matrix

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
            if getattr( self, prop ):
                self.nodraw = True
    def compile_textures( self ):
        if not self.sky:
            for id,map in self.images.items():
                self.textures[id] = imagetexture.ImageTexture()
                self.textures[id].setImage( map )
    def render( self, visible=True, lit=False, mode=None ):
        pass
    def disable( self ):
        pass
        
    def render_sky( self, mode=None ):
        """Render the sky in Q3-like fashion"""
        # bind N texture units to our textures 
        # render a single quad in front of us
        # on each point, sample correct texture
        glDepthMask( GL_FALSE ) 
        if 'cube' not in self.textures:
            self.textures['cube'] = create_cube_texture( self.images )
        texture, cube_vert_vbo, cube_index_vbo, shader, vertex, mvp_matrix = self.textures['cube']
        with texture:
            # we don't currently have it handy...
            with shader:
                glEnableVertexAttribArray(vertex);
                with cube_vert_vbo:
                    glVertexAttribPointer(vertex, 3, GL_FLOAT, GL_FALSE, 0, cube_vert_vbo);
                    glUniformMatrix4fv(mvp_matrix,1,GL_FALSE,mode.modelproj)
                    with cube_index_vbo:
                        glDrawElements(GL_QUADS, len(CUBE_INDICES), GL_UNSIGNED_SHORT, cube_index_vbo)
                glDisableVertexAttribArray(vertex);
        glDepthMask( GL_TRUE ) 
        
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
