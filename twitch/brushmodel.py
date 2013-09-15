

class Brush( object ):
    """Model view of a brush (no rendering logic)"""
    DEFAULT_SURFACE_PARAMS = dict(
        cull = 'front',
        flesh = False,
        fog = False,
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
    def __init__( self, definition ):
        self.definition = definition 
        for key,value in self.DEFAULT_SURFACE_PARAMS.items():
            setattr( self, key, value )
        self.commands = []
        self.suites = []
        self.images = {}
        for definition in definition:
            if isinstance( definition, tuple ):
                if tuple[0] == 'surfaceparam':
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
                return cmd
        return None
    def get_commands( self, command ):
        for cmd in self.commands:
            if cmd[0] == command:
                yield cmd
    def load( self, twitch ):
        """Use the twitch object to load our external resources"""
        if self.nodraw:
            return
        for suite in self.suites:
            for command in suite:
                if command[0] in ['map','clampMap']:
                    filename = command[1]
                    if filename not in self.maps:
                        self.images[filename] = twitch._load_image_file( command[1] )
                        if not self.images[filename]:
                            log.warn( 'Unable to load %s', command )
    
