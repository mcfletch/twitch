from __future__ import absolute_import
import logging 
log = logging.getLogger( __name__ )

class Brush( object ):
    """Model view of a brush (no rendering logic)"""
    DEFAULT_SURFACE_PARAMS = dict(
        areaportal=False,
        clusterportal=False,
        cull = 'front',
        donotenter=False,
        flesh = False,
        fog = False,
        sky = False,
        nodamage = False,
        nodlight = False,
        nodraw = False,
        nodrop = False,
        noimpact = False,
        nolightmap = False,
        nomarks = False,
        nosteps = False,
        nonsolid = False,
        origin = False,
        lava = False,
        metalsteps = False,
        playerclip = False,
        slick = False,
        slime = False,
        structural = False,
        trans = False,
        water = False,
    )
    def __init__( self, id, definition ):
        self.id = id
        self.definition = definition 
        for key,value in self.DEFAULT_SURFACE_PARAMS.items():
            setattr( self, key, value )
        self.commands = []
        self.suites = []
        self.images = {}
        for definition in definition:
            if isinstance( definition, tuple ):
                if definition[0] == 'surfaceparm':
                    name,param = definition[1][0],definition[1][1:]
                    if not param:
                        # flag type...
                        param = True 
                    elif len(param) == 1:
                        param = param[0]
                    if name in self.DEFAULT_SURFACE_PARAMS:
                        setattr( self, name, param )
                else:
                    self.commands.append( definition )
            else:
                self.suites.append( definition )
                
    def get_command( self, command ):
        for cmd in self.commands:
            if cmd[0] == command:
                return cmd[1]
        return None
    def get_commands( self, command ):
        for cmd in self.commands:
            if cmd[0] == command:
                yield cmd
    SKY_SUFFIXES = [
        ('rt',[-1,0,0]),
        ('lf',[1,0,0]),
        ('ft',[0,0,1]),
        ('bk',[0,0,-1]),
        ('up',[0,-1,0]),
        ('dn',[0,1,0]),
    ]
    loaded = False
    def load( self, twitch ):
        """Use the twitch object to load our external resources"""
        # TODO: atomic...
        if self.loaded:
            return False 
        self.loaded = True
        
        if self.nodraw:
            return
        for suite in self.suites:
            for command in suite:
                if command[0] in ['map','clampMap']:
                    filename = command[1][0]
                    if filename not in self.images:
                        self.images[filename] = twitch._load_image_file( filename )
                        if not self.images[filename]:
                            log.warn( 'Unable to load %s', command )
        if self.sky:
            command = self.get_command( 'skyparms' )
            try:
                farbox,cloudheight = command[0:2]
            except ValueError as err:
                raise ValueError( *command )
            if farbox == '-':
                raise ValueError( "Can't currently render non-skybox skies" )
            for suffix,normal in self.SKY_SUFFIXES:
                image = twitch._load_image_file( '%s_%s'%(farbox,suffix) )
                if not image:
                    raise RuntimeError( "unable to find skybox image: %s", '%s_%s'%(farbox,suffix))
                self.images[suffix] = image
            try:
                self.cloudheight = float( cloudheight )
            except ValueError as err:
                self.cloudheight = None
            except TypeError as err:
                err.args += (cloudheight,command)
                raise
