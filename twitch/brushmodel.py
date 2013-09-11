class Brush( object ):
    """Model view of a brush (no rendering logic)"""
    nodraw = False
    sky = False
    cull = 'front'
    def __init__( self, definition ):
        self.definition = definition 
        self.commands = []
        self.suites = []
        self.surface_params = {}
        self.images = {}
        for definition in definition:
            if isinstance( definition, tuple ):
                if tuple[0] == 'surfaceparam':
                    self.surface_params[definition[1][0]] = definition[1][1:]
                else:
                    self.commands.append( definition )
            else:
                self.suites.append( definition )
                
        for prop in self.NO_DRAW_PROPERTIES:
            if prop in self.surface_params:
                self.nodraw = True
        if 'cull' in self.surface_params:
            self.cull = self.surface_params['cull']
    NO_DRAW_PROPERTIES = ['nodraw','areaportal','clusterportal','donotenter']
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
