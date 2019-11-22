# Python/PyOpenGL/OpenGLContext PK3 Renderer

Twitch is a demonstration of how to load a Quake III style
.pk3 file into a PyOpenGL context and render it such that
you can walk around and see the geometry. It does *not*
implement a game, it is *just* a renderer.

## Installation

```
pip install twitch
```

## Usage

```
twitch-viewer https://gamebanana.com/dl/391867
twitch-viewer unpack-directory/maps/test.bsp
twitch-viewer unpack-directory/test.pk3
```

### Controls

| Key | Action | Alt Action | Ctrl Action |
| --- | ------ | ---------- | ----------- |
| Up  | Forward| Pan Up     | Turn Up |
| Down | Backward | Pan Down | Turn Down |
| Left | Turn Left | Pan Left | |
| Right | Turn Right | Pan Right |  |

