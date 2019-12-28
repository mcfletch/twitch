# Python/PyOpenGL/OpenGLContext PK3 Renderer

Twitch-OGLC is a sketch of how to load a Quake III style
.pk3 file into a [PyOpenGL](https://github.com/mcfletch/openglcontext) context and render it such that
you can walk around and see the geometry. It does *not*
implement a game, it is *just* a renderer and
an incomplete one at that.

## Installation

You'll need [OpenGLContext](https://github.com/mcfletch/openglcontext) installed with one of
the GUI libraries it supports (GLUT, PyGame, wxPython).

```
pip3.6 install twitchoglc OpenGLContext pygame
# Get high-res versions of core textures
twitch-downloader --resources http://ioquake3.org/files/xcsv_hires.zip
```

## Usage

To download, unpack and run:
```
twitch-viewer https://gamebanana.com/dl/391867
```
> Note
>
> Many map-download sites would prefer that
> you **not** download maps directly, as their
> revenue is advertising based. So expect that
> many download links that are usable in the
> browser will fail an automated download
> due to server-side validation.

To unpack and run a downloaded .zip/pk3:
```
twitch-viewer unpack-directory/test.pk3
```
To run an already-unpacked pk3 (a bsp):
```
twitch-viewer unpack-directory/maps/test.bsp
```


### Controls

These are just the default controls from
OpenGLContext, but for reference:

| Key | Action | Alt Action | Ctrl Action |
| --- | ------ | ---------- | ----------- |
| Up  | Forward| Pan Up     | Turn Up |
| Down | Backward | Pan Down | Turn Down |
| Left | Turn Left | Pan (Step) Left | |
| Right | Turn Right | Pan (Step) Right |  |

## Limits and Problems

This is very much a proof of concept, *not*
a fully functional Quake III rendering engine.

* There are lots of core textures missing
* The lighting is wrong (*far* too dark)
* We don't use spawn points to launch in 
  reasonable locations
* We don't do any collision checking or other
  game-needed operations

## Contributing

If you'd like to work on the library, feel free
to fork and make a pull request,
but please note that I very seldom get 
time to work on my Open Source projects, so 
expect that my response times can be measured
in weeks or months, so don't block your own
work waiting for me.