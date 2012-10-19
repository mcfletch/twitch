"""Quake3 BSP file loading module (lowest abstraction layer)

Written directly from the following:

    http://www.mralligator.com/q3/

Basically just uses numpy record declarations to parse the bsp files
into structured data-arrays.  Uses the bezier module to tessellate 
patches into simple triangles (note: not triangle strips).
"""
import numpy, sys, logging, os, zipfile
from . import bezier
from . import pk3

log = logging.getLogger( __name__ )
i4 = '<i4'
f4 = '<f4'
TEXTURE_RECORD = numpy.dtype( [
    ('filename','c',64),
    ('flags',i4),
    ('contents',i4),
])
PLANE_RECORD = numpy.dtype( [
    ('normal',f4,3),
    ('distance',f4,1),
] )
NODE_RECORD = numpy.dtype( [
    ('plane',i4,),
    ('children',i4,2),
    ('mins',i4,3),
    ('maxs',i4,3),
] )
LEAF_RECORD = numpy.dtype( [
    ('cluster',i4),
    ('area',i4),
    ('mins',i4,3),
    ('maxs',i4,3),
    ('leafface',i4),
    ('n_leaffaces',i4),
    ('leafbrush',i4),
    ('n_leafbrushes',i4),
] )
MODEL_RECORD = [
    ('mins',f4,3),
    ('maxs',f4,3),
    ('face',i4),
    ('n_faces',i4),
    ('brush',i4),
    ('n_brushes',i4),
]
BRUSH_RECORD = [
    ('brushside',i4),
    ('n_brushsides',i4),
    ('texture',i4),
]
BRUSHSIDE_RECORD = [
    ('plane',i4),
    ('texture',i4),
]
VERTEX_RECORD = [
    ('position',f4,3),
    ('texcoord_surface',f4,2),
    ('texcoord_lightmap',f4,2),
    ('normal',f4,3),
    ('color','B',4),
]
EFFECT_RECORD = [
    ('name','c',64),
    ('brush',i4),
    ('unknown',i4),
]
FACE_RECORD = [
    ('texture',i4),
    ('effect',i4),
    ('type',i4),
    ('vertex',i4),
    ('n_vertices',i4),
    ('meshvert',i4),
    ('n_meshverts',i4),
    ('lm_index',i4),
    ('lm_start',i4,2),
    ('lm_size',i4,2),
    ('lm_origin',f4,3),
    ('lm_vecs_s',f4,3),
    ('lm_vecs_t',f4,3),
    ('normal',f4,3),
    ('size',i4,2),
]
LIGHTMAP_RECORD = [
    ('texture','i1',(128,128,3)),
]
LIGHTVOL_RECORD = [
    ('ambient','i1',3),
    ('directional','i1',3),
    ('dir','i1',2),
]
VISDATA_RECORD_HEADER = [
    ('n_vecs',i4),
    ('sz_vecs',i4),
]

LUMP_ORDER = [
    ('entities','c'),
    ('textures',TEXTURE_RECORD),
    ('planes',PLANE_RECORD),
    ('nodes',NODE_RECORD),
    ('leafs',LEAF_RECORD),
    ('leaffaces',i4),
    ('leafbrushes',i4),
    ('models',MODEL_RECORD),
    ('brushes',BRUSH_RECORD),
    ('brushsides',BRUSHSIDE_RECORD),
    ('vertices',VERTEX_RECORD),
    ('meshverts',i4),
    ('effects',EFFECT_RECORD),
    ('faces',FACE_RECORD),
    ('lightmaps',LIGHTMAP_RECORD),
    ('lightvols',LIGHTVOL_RECORD),
    ('visdata','iio'),
]

def load_visdata( visdata ):
    header = numpy.dtype( VISDATA_RECORD_HEADER )
    result = []
    while len(visdata):
        this_header = visdata[:header.itemsize].view( header )[0]
        n_vecs,sz_vecs = this_header
        size = (n_vecs * sz_vecs)
        end = header.itemsize+size
        vecs = visdata[header.itemsize:end]
        assert len(vecs) == size
        result.append( (n_vecs,sz_vecs,vecs))
        visdata = visdata[end:]
    assert len(result) == 1
    return result[0]

def parse_bsp( array ):
    """Parse a BSP structure for the array 
    
    array -- numpy array with the data to parse...
    
    returns {
        <lump>: <lump_array>,
        for lump,dtype in LUMP_ORDER
    }
    """
    array = array.view( 'c' )
    iarray = array.view( i4 )
    magic = array[:4].tostring()
    assert magic == 'IBSP', magic 
    version = iarray[1]
    assert version == 0x2e, version
    direntries = iarray[2:2+17*2]
    direntries = numpy.reshape( direntries, (17,2))
    model = {}
    for (lump,dtype),(offset,length) in zip( LUMP_ORDER, direntries ):
        data = array[offset:offset+length]
        loader = globals().get( 'load_%s'%(lump,))
        if loader:
            model[lump] = data = loader( data )
        else:
            dtype = numpy.dtype( dtype )
            extra = len(data) % dtype.itemsize
            if extra:
                log.warn( 'Extra data in lump %s: %s bytes', lump, extra )
                data = data[:-extra]
            model[lump] = data = data.view( dtype )
            log.debug( 'Loaded %s %s', data.shape[0], lump )
    return model

class Twitch( object ):
    def __init__( self, model, base_directory=None ):
        self.__dict__.update( model )
        self.base_directory = base_directory
    
    simple_indices = None
    texture_set = None
    @property
    def simple_faces( self ):
        """Create an index array for the indices to render faces of type 1 and 3"""
        if self.simple_indices is None:
            faces = self.faces
            # for type 1 and 3 we can simply create indices...
            simple_types = numpy.logical_or( self.faces['type'] == 1, self.faces['type'] == 3)
            simple_faces = numpy.compress( simple_types, self.faces )
            # texture counts...
            sortorder = numpy.lexsort( (simple_faces['texture'],) )
            simple_faces = numpy.take( simple_faces, sortorder )
            
            self.texture_set = texture_set = []
            
            simple_index_count = numpy.sum( simple_faces['n_meshverts'] )
            indices = numpy.zeros( (simple_index_count,), 'I4' )
            # ick, should be a fast way to do this...
            starts = simple_faces['meshvert']
            textures = simple_faces['texture']
            stops = simple_faces['meshvert'] + simple_faces['n_meshverts']
            start_indices = simple_faces['vertex']
            current = 0
            texture = None
            for tex,start,stop,index in zip(textures,starts,stops,start_indices):
                if texture != tex:
                    if texture:
                        texture_set.append( (texture,stop))
                    texture = tex
                end = current + (stop-start)
                indices[current:end] = self.meshverts[start:stop] + index
                current = end
            self.simple_indices = indices
            # for type 2, we need to convert a control surface to a set of indices...
            log.debug( '%s textures used by simple geometry', len(self.texture_set, ))
        return self.simple_indices
    patch_vertices = None
    patch_indices = None
    @property
    def patch_faces( self ):
        """Create another pair of arrays for our patch faces
        """
        if self.patch_indices is None:
            patch_faces = numpy.compress( self.faces['type'] == 2, self.faces )
            if not len(patch_faces):
                self.patch_indices = None
                return None,None
            
            starts = patch_faces['vertex']
            sizes = patch_faces['size']
            
            expanded_patches = []
            expanded_indices = []
            current_offset = 0
            index_count = 0
            for start,(x,y) in zip( starts, sizes ):
                control_points = self.vertices[start: start+(x*y)]['position']
                control_points = control_points.reshape( (x,y,3) )
                
                expanded = bezier.expand( control_points, final_size=8 )
                expanded[:,:,3:6] = bezier.expand_blend( 
                    self.vertices[start: start+(x*y)]['normal'].reshape(x,y,3) 
                )
                expanded[:,:,6:8] = bezier.expand_blend( 
                    self.vertices[start: start+(x*y)]['texcoord_surface'].reshape(x,y,2) 
                )
                
                indices = bezier.grid_indices( expanded, current_offset )
                
                indices = indices.ravel()
                expanded_indices.append( indices )
                index_count += len(indices)
                
                expanded = expanded.reshape( (-1,expanded.shape[-1]) )
                expanded_patches.append( expanded )
                current_offset += expanded.shape[0] 
            
            final_indices = numpy.zeros( (index_count,), 'I' )
            index_count = 0
            for index in expanded_indices:
                final_indices[index_count:(index_count+len(index))] = index 
                index_count += len(index)
            vertex_count = 0
            final_vertices = numpy.zeros( (current_offset,8), 'f' )
            for patch in expanded_patches:
                final_vertices[vertex_count:(vertex_count+len(patch))] = patch 
                vertex_count += len(patch)
            self.patch_vertices = final_vertices
            self.patch_indices = final_indices
        return self.patch_vertices,self.patch_indices
    
    def load_texture_by_id( self, id, texture=None ):
        """Load a single texture by ID (index)
        
        returns PIL Image instance or None if image is not found
        """
        if texture is None:
            texture = self.textures[id]
        relative = ''.join( texture['filename'] )
        if pk3.escape_path( relative ):
            raise IOError( """Texture: %s references an external file"""%( relative ))
        path = os.path.join( self.base_directory, relative + '.tga' )
        directory,basename = os.path.split( path )
        alt_path = os.path.join( directory, 'x_'+basename )
        img = None
        for possible in [path,alt_path]:
            if os.path.exists( possible ):
                from PIL import Image
                img = Image.open( possible )
                x,y = img.size 
                if not self.is_pow2( x ) or not self.is_pow2( y ):
                    log.warn( 'Non power-of-two Image #%s %s: %sx%s', id, relative, x, y )
                log.debug( "Image #%s %s: %sx%s,", id, relative, img.size[0], img.size[1] )
        if not img:
            log.warn( "Unable to find Image #%s: %s", id, relative )
        return img 
    
    loaded_textures = None
    def load_textures( self ):
        """Load all of our textures"""
        if self.loaded_textures is None:
            self.loaded_textures = []
            for id,texture in enumerate(self.textures):
                self.loaded_textures.append( self.load_texture_by_id( id, texture ) )
        return self.loaded_textures
    
    @staticmethod
    def is_pow2( size ):
        """Is this an even power of two size?"""
        if size < 0:
            raise ValueError( "Negative image size???" )
        while (not (size & 1)) and (size > 1):
            size = size >> 1
        if size == 1:
            return True 
        return False
    

def load( filename, base_directory=None ):
    if base_directory is None:
        # TODO: this could, in theory, produce a directory traversal attack
        # if you unpacked your file next to something important and called 
        # parse without a root directory...
        base_directory = os.path.dirname( os.path.dirname( filename ) )
    array = numpy.memmap( filename, dtype='c', mode='c' )
    return Twitch( parse_bsp( array ), base_directory )
    
def main():
    logging.basicConfig( level=logging.DEBUG )
    target = sys.argv[1]
    base_directory = None
    if target.endswith( '.pk3' ):
        from . import pk3 
        key = pk3.key( target )
        base_directory = pk3.unpack_directory( key )
        target = pk3.unpack( target, base_directory )
    twitch = load( target, base_directory )
    twitch.load_textures()
    return twitch
