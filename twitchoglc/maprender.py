"""Low-level renderer for Q3 style BSP maps"""
from __future__ import absolute_import
from __future__ import print_function
import logging,numpy, sys,traceback
log = logging.getLogger( __name__ )
from . import bsp,brushviewer
from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGLContext.scenegraph import imagetexture
from OpenGLContext import texture

class Map( object ):
    """Map object which loads and renders Q3 map"""
    loaded = False
    def __init__( self, filename ):
        self.filename = filename 
    def load( self ):
        log.info("Starting BSP load of %s", self.filename)
        self.twitch = bsp.load( self.filename, brush_class=brushviewer.Brush )
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
            elif isinstance( image, brushviewer.Brush ):
                self.textures[id] = image
                image.compile_textures()
            else:
                texture = imagetexture.ImageTexture()
                texture.setImage( image ) # we don't want to trigger redraws, so skip that...
                self.textures[id] = texture 
        self.lightmaps = {}
        for id,data in self.twitch.iter_lightmaps():
            self.lightmaps[id] = brushviewer.Lightmap( id, data )
        self.skies = self.twitch.find_sky()
        if self.skies:
            for sky in self.skies:
                print('Sky:', sky)
                try:
                    sky.load(self.twitch)
                    sky.compile_textures()
                except Exception as err:
                    log.warn( 'Unable to load textures for sky %s: %s', sky.id, traceback.format_exc() )
                else:
                    self.sky = sky
                    break
        self.loaded = True
    sky = None
    def set_cull( self, newmode,current ):
        if newmode == 'disable':
            newmode = 'none'
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
        #glEnable(GL_LIGHTING)
        glDisable(GL_LIGHTING)
        glEnable( GL_COLOR_MATERIAL )
        
        if self.sky:
            self.sky.render_sky( mode )
        glActiveTexture( GL_TEXTURE0 )
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_BLEND)
        
        glActiveTexture( GL_TEXTURE1 )
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

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
            glClientActiveTexture( GL_TEXTURE0 )
            glTexCoordPointer(
                2,
                GL_FLOAT,
                self.simple_vertices.itemsize,
                self.simple_indices + 12,
            )
            glClientActiveTexture( GL_TEXTURE1 )
            glTexCoordPointer(
                2,
                GL_FLOAT,
                self.simple_vertices.itemsize,
                self.simple_indices + 20,
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
            
            current_lightmap = None
            current_texture = None
            try:
                for lightmap,id,stop in self.twitch.texture_set:
                    texture = self.textures.get( id )
                    lightmap = self.lightmaps.get( id )
                    if not getattr(texture,'nodraw',None):
                        if lightmap and lightmap != current_lightmap:
                            lightmap.render(
                                visible=mode.visible,
                                lit = False,
                                mode = mode,
                            )
                        if texture and texture != current_texture:
                            if isinstance( texture, brushviewer.Brush ):
                                # scripted brush can have lots and lots of details...
                                glActiveTexture( GL_TEXTURE0 )
                                cull = self.set_cull( texture.surface_params['cull'], cull )
                                texture.render(
                                    visible = mode.visible,
                                    lit = False,
                                    mode = mode,
                                )
                            elif texture:
                                cull = self.set_cull( 'front', cull )
                                glActiveTexture( GL_TEXTURE0 )
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
                        if isinstance( texture, brushviewer.Brush ):
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
