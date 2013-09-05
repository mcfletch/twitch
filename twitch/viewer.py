"""Renderer for a Twitch node (Quake III style BSP map)"""
import OpenGL
#OpenGL.FULL_LOGGING = True
import logging,numpy, sys
from OpenGLContext import testingcontext
from twitch import bsp
from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGLContext.scenegraph import imagetexture
BaseContext = testingcontext.getInteractive()

class Brush( bsp.Brush ):
    """Sub-class with rendering functionality for Brushes"""
    def __init__( self, *args, **named ):
        super(Brush,self).__init__(*args,**named)
        self.textures = {}
    def compile_textures( self ):
        for id,map in self.images.items():
            self.textures[id] = imagetexture.ImageTexture()
            self.textures[id].setImage( map )
    def enable( self ):
        pass 
    def disable( self ):
        pass

class TwitchContext( BaseContext ):
    def OnInit( self ):
        # TODO: Quake maps actually have a different coordinate system from 
        # VRML-97 style (such as OpenGLContext), should rotate it...
        self.twitch = bsp.load( sys.argv[1], brush_class=Brush )
        self.simple_vertices = vbo.VBO( self.twitch.vertices )
        self.simple_indices = vbo.VBO( self.twitch.simple_faces, target=GL_ELEMENT_ARRAY_BUFFER )
        vertices,indices = self.twitch.patch_faces
        if indices is not None:
            self.patch_vertices = vbo.VBO( vertices )
            self.patch_indices = vbo.VBO( indices, target=GL_ELEMENT_ARRAY_BUFFER )
        else:
            self.patch_indices = None
        # Construct a big lightmap data-set...
        self.textures = {}
        for id,image in self.twitch.load_textures():
            if image is None:
                pass
            elif isinstance( image, bsp.Brush ):
                self.textures[id] = image
                
            else:
                texture = imagetexture.ImageTexture()
                texture.setImage( image ) # we don't want to trigger redraws, so skip that...
                self.textures[id] = texture 
        # default near is far too close for 8 units/foot quake model size
        self.platform.setFrustum( near = 30, far=50000 )
        self.movementManager.STEPDISTANCE = 50
    def set_cull( self, newmode,current ):
        if newmode == current:
            return newmode 
        if newmode == 'front':
            if current == 'none':
                glEnable(GL_CULL_FACE)
            glCullFace( GL_FRONT )
        elif newmode == 'back':
            if current == 'none':
                glEnable(GL_CULL_FACE)
            glCullFace( GL_BACK )
        else:
            glDisable( GL_CULL_FACE )
        return newmode
        
    def Render( self, mode = None):
        """Render the geometry for the scene."""
        BaseContext.Render( self, mode )
        glRotatef( -90, 1.0,0,0 )
        #glScalef( .01, .01, .01 )
        if not mode.visible:
            return
        glEnable(GL_LIGHTING)
        glEnable( GL_COLOR_MATERIAL )
        cull = self.set_cull( 'front', 'none' )
        self.simple_vertices.bind()
        try:
            glEnableClientState( GL_VERTEX_ARRAY )
            glEnableClientState( GL_COLOR_ARRAY )
            glEnableClientState( GL_NORMAL_ARRAY )
            glEnableClientState( GL_TEXTURE_COORD_ARRAY )
            glVertexPointer(
                3,GL_FLOAT,
                self.simple_vertices.itemsize, # compound structure
                self.simple_vertices,
            )
            glTexCoordPointer(
                2,
                GL_FLOAT,
                self.simple_vertices.itemsize,
                self.simple_indices + 12,
            )
            glNormalPointer(
                GL_FLOAT,
                self.simple_vertices.itemsize,
                self.simple_vertices + 28,
            )
            glColorPointer(
                4,GL_UNSIGNED_BYTE,
                self.simple_vertices.itemsize,
                self.simple_vertices + 40,
            )
            self.simple_indices.bind()
            current = 0
            try:
                for id,stop in self.twitch.texture_set:
                    texture = self.textures.get( id )
                    if not getattr(texture,'nodraw',None):
                        if isinstance( texture, bsp.Brush ):
                            # scripted brush can have lots and lots of details...
                            cull = self.set_cull( texture.cull, cull )
                            texture.enable()
                        elif texture:
                            cull = self.set_cull( 'front', cull )
                            texture.render(
                                visible = mode.visible,
                                lit = False,
                                mode = mode,
                            )
                        glDrawElements( 
                            GL_TRIANGLES, 
                            int(stop)-current, 
                            GL_UNSIGNED_INT, 
                            self.simple_indices+(current*self.simple_indices.itemsize)
                        )
                        if isinstance( texture, bsp.Brush ):
                            # scripted brush can have lots and lots of details...
                            texture.disable()
                    current = int(stop)
            finally:
                self.simple_indices.unbind()
        finally:
            self.simple_vertices.unbind()
            glDisableClientState( GL_COLOR_ARRAY )
        if self.patch_indices is not None:
            glEnable( GL_LIGHTING )
            #glEnable( GL_CULL_FACE )
            try:
                self.patch_vertices.bind()
                glEnable( GL_LIGHTING )
                glEnableClientState( GL_VERTEX_ARRAY )
                glEnableClientState( GL_NORMAL_ARRAY )
                glEnableClientState( GL_TEXTURE_COORD_ARRAY )
                stride = self.patch_vertices.itemsize * self.patch_vertices.shape[-1]
                glVertexPointer(
                    3,GL_FLOAT,
                    stride,
                    self.patch_vertices,
                )
                glNormalPointer(
                    GL_FLOAT,
                    stride,
                    self.patch_vertices + (3*self.patch_vertices.itemsize),
                )
                glTexCoordPointer(
                    3,GL_FLOAT,
                    stride,
                    self.patch_vertices + (6*self.patch_vertices.itemsize),
                )
                try:
                    self.patch_indices.bind()
                    glDrawElements( 
                        GL_TRIANGLES, 
                        len(self.patch_indices), 
                        GL_UNSIGNED_INT, 
                        self.patch_indices, 
                    )
                finally:
                    self.patch_indices.unbind()
            finally:
                self.patch_vertices.unbind()
        #self.OnQuit( None )

def main():
    logging.basicConfig( level = logging.WARN )
    TwitchContext.ContextMainLoop()
