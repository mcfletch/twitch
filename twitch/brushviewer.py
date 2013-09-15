"""Renderer for a Twitch node (Quake III style BSP map)"""
import logging,numpy, sys
log = logging.getLogger( __name__ )
from twitch import brushmodel
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo
from OpenGLContext.scenegraph import imagetexture
from OpenGLContext import texture

CUBE_NAME_MAP = dict([
    ('rt',GL_TEXTURE_CUBE_MAP_POSITIVE_X),
    ('lf',GL_TEXTURE_CUBE_MAP_NEGATIVE_X),
    ('ft',GL_TEXTURE_CUBE_MAP_NEGATIVE_Z),
    ('bk',GL_TEXTURE_CUBE_MAP_POSITIVE_Z),
    ('up',GL_TEXTURE_CUBE_MAP_POSITIVE_Y),
    ('dn',GL_TEXTURE_CUBE_MAP_NEGATIVE_Y),
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
    tex = glGenTextures(1)
    glBindTexture( GL_TEXTURE_CUBE_MAP, tex )
    glPixelStorei(GL_UNPACK_ALIGNMENT,1)
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_NEAREST); 
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE);
    # TODO: validate that all images are the same size, format, etc...
    our_images = dict([(x,images[x]) for x in CUBE_NAME_MAP.keys()])
    assert len(our_images) == 6, our_images
    if len([i for i in our_images if i]) != 6:
        log.error( """Null/unloaded images in background""" )
        return None
    sample = our_images['ft']
    components, format = texture.getLengthFormat( sample )
    x,y = sample.size[0], sample.size[1]
    for key,img in our_images.items():
        glTexImage2D(
            CUBE_NAME_MAP[key], 0, components, x, y, 0, format, GL_UNSIGNED_BYTE, 
            img.tostring("raw", img.mode, 0, -1)
        )
    cube_vert_vbo = vbo.VBO( CUBE_VERTICES )
    cube_index_vbo = vbo.VBO( CUBE_INDICES, target=GL_ELEMENT_ARRAY_BUFFER )
    shader = shaders.compileProgram(
        shaders.compileShader(
            '''#version 330
in vec3 vertex;
out vec3 texCoord;
uniform mat4 mvp_matrix;

void main() {
    gl_Position = mvp_matrix * vec4( vertex, 1.0);
    texCoord = vertex;
}''', GL_VERTEX_SHADER ),
        shaders.compileShader(
            '''#version 330
in vec3 texCoord;
out vec4 fragColor;
uniform samplerCube cube_map;

void main( ) {
    fragColor = texture(cube_map, texCoord);
}''', GL_FRAGMENT_SHADER ),
    )
    vertex = glGetAttribLocation( shader, 'vertex' )
    matrix = glGetUniformLocation( shader, 'mvp_matrix' )
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
        glBindTexture( GL_TEXTURE_CUBE_MAP, texture )
        glEnable(GL_TEXTURE_CUBE_MAP)
        # we don't currently have it handy...
        with shader:
            glEnableVertexAttribArray(vertex);
            with cube_vert_vbo:
                glVertexAttribPointer(vertex, 3, GL_FLOAT, GL_FALSE, 0, cube_vert_vbo);
                glUniformMatrix4fv(mvp_matrix,1,GL_FALSE,mode.modelproj)
                with cube_index_vbo:
                    glDrawElements(GL_QUADS, len(CUBE_INDICES), GL_UNSIGNED_SHORT, cube_index_vbo)
            glDisableVertexAttribArray(vertex);
        glDisable( GL_TEXTURE_CUBE_MAP )
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
