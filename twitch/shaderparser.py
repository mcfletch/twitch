#! /usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
from simpleparse.parser import Parser
from simpleparse.common import chartypes, comments, numbers, strings
from simpleparse.dispatchprocessor import *

grammar = r'''
file            := ts,production+
production      := name, ts, suite, ts
suite           := '{', ts, (command/suite,ts)*, '}', ts 
command         := name, ts_simple, ((ref/number/vector/name),ts_simple)*
ref             := '$', name 
name            := [-a-zA-Z],[-_./a-zA-Z0-9]*
vector          := '(', ts, (number,ts)*, ')', ts
<ts_simple>     := [ \t]*
<ts>            :=  ( [ \011-\015]+ / slashslash_comment)*
'''

class ScriptParser( Parser ):
    """Produce a parser for the script files"""

def buildParser( declaration = grammar ):
    """Build a new VRMLParser object"""
    return ScriptParser( declaration, "file" )

def test_parser( ):
    parser = buildParser()
    for should_match,production in [
        ('//this\n//that', 'ts' ),
        ('''//**********************************************************************//
''', 'ts'),
        ('my/name/there', 'name'),
        ('{ this and that 23.0 }', 'suite' ),
        ('textures/focal/alpha_100', 'name' ),
        ('rgbGen','name'),
        ('{}', 'suite' ),
        ('1.0', 'number'),
        ('''	// Secondary texture ONLY
''', 'ts' ),
        ('''textures/focal/alpha_100 {} ''', 'production' ),
        ('''textures/focal/alpha_100
{}''', 'production' ),
        ('''textures/focal/alpha_100	// Secondary texture ONLY
{}''', 'production' ),
        ('''textures/focal/alpha_100	// Secondary texture ONLY
{
	qer_editorimage textures/focal/alpha_100.tga
	q3map_alphaMod volume
	q3map_alphaMod set 1.0
	surfaceparm nodraw
	surfaceparm nonsolid
	surfaceparm trans
	qer_trans 0.7
}''', 'production'),
        ('''textures/focal/skyportal
{
	qer_editorimage textures/focal/sky_edit.jpg

	q3map_noFog
	q3map_globalTexture
	surfaceparm sky
	surfaceparm noimpact
	surfaceparm nolightmap
	skyparms textures/focal/env/sky 1500 -
	nopicmip

	{
		map textures/focal/cloud_edge.tga
		blendFunc GL_ONE_MINUS_SRC_ALPHA GL_SRC_ALPHA
		tcMod scale 2 2
		tcMod transform 0.125 0 0 0.125 0.1075 0.1075
		rgbGen identityLighting
	}
	{
		map textures/focal/env/sky_mask.tga
		blendFunc GL_ONE_MINUS_SRC_ALPHA GL_SRC_ALPHA
		tcMod transform 0.25 0 0 0.25 0.1075 0.1075
		rgbGen identityLighting
	}
}
''', 'production'),
        
    ]:
        result = parser.parse( should_match, production )
        assert result[-1] == len(should_match), (should_match, production, result)

class ParseProcessor( DispatchProcessor ):
    def __init__( self, *args, **named ):
        DispatchProcessor.__init__( self, *args, **named )
        self.productions = {}
    def file( self, match, buffer ):
        (tag,start,stop,children) = match
        dispatchList( self, children, buffer )
    def production( self, match, buffer ):
        (tag,start,stop,children) = match
        name,suite = children
        name = dispatch( self, name, buffer )
        self.productions[name] = dispatch( self, suite, buffer )
    def suite( self, match, buffer):
        (tag,start,stop,children) = match
        return dispatchList( self, children, buffer )
    def command( self, match, buffer ):
        (tag,start,stop,children) = match
        name = dispatch( self, children[0], buffer )
        params = dispatchList( self, children[1:], buffer )
        return (name,params)
    def name( self, match, buffer ):
        (tag,start,stop,children) = match
        return buffer[start:stop]
    ref = name
    def number( self, match, buffer ):
        (tag,start,stop,children) = match
        try:
            return int( buffer[start:stop] )
        except ValueError as err:
            return float( buffer[start:stop] )
    def vector( self, match, buffer):
        (tag,start,stop,children) = match
        return dispatchList( self, children, buffer )

def load( filename ):
    content = open( filename ).read()
    parser = buildParser()
    processor = ParseProcessor()
    
    parsed = parser.parse( content, production='file')
    processor( parsed, content )
    return processor.productions
        
def main( ):
    import sys 
    productions = load( sys.argv[1] )
    def print_suite( suite, indent=1 ):
        print(' '*max((indent-1,0)),'{')
        for component in suite:
            if isinstance( component, tuple ):
                print(' '*indent, component[0], '->', " ".join( [str(x) for x in component[1]] ))
            else:
                print_suite( component, indent+1 )
        print(' '*max((indent-1,0)),'}')
    for key,suite in sorted( productions.items()):
        print(key) 
        print_suite( suite )

if __name__ == "__main__":
    #test_parser()
    main()
