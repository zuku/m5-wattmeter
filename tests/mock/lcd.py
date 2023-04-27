"""Color"""
BLACK       = 0x000000
BLUE        = 0x0000ff
CYAN        = 0x00ffff
DARKCYAN    = 0x008080
DARKGREEN   = 0x008000
DARKGREY    = 0x808080
GREEN       = 0x00ff00
GREENYELLOW = 0xacfc2c
LIGHTGREY   = 0xc0c0c0
MAGENTA     = 0xfc00ff
MAROON      = 0x800000
NAVY        = 0x000080
OLIVE       = 0x808000
ORANGE      = 0xfca400
PINK        = 0xfcc0ca
PURPLE      = 0x800080
RED         = 0xfc0000
WHITE       = 0xfcfcfc
YELLOW      = 0xfcfc00

"""Color depth"""
COLOR_BITS16 = 16
COLOR_BITS24 = 24
SPRITE_1BIT  =  1
SPRITE_8BIT  =  8
SPRITE_16BIT = 16

"""Position"""
CENTER = -0x232b
BOTTOM = -0x232c
RIGHT  = -0x232c
LASTX  =  0x1b58
LASTY  =  0x1f40

"""Font"""
FONT_Default      = 0
FONT_DejaVu18     = 1
FONT_DejaVu24     = 2
FONT_Ubuntu       = 3
FONT_Comic        = 4
FONT_Minya        = 5
FONT_Tooney       = 6
FONT_Small        = 7
FONT_DefaultSmall = 8
FONT_7seg         = 9
FONT_DejaVu40     = 11
FONT_DejaVu56     = 12
FONT_DejaVu72     = 13
FONT_Arial12      = 14
FONT_Arial16      = 15
FONT_UNICODE      = 16

def screensize():
    return (136, 241)

def sprite_create(w, h, color):
    pass

def sprite_select():
    pass

def sprite_deselect():
    pass

def sprite_show(x, y):
    pass

def setColor(color, bg_color):
    pass

def clear(color = -1):
    pass

def font(font, rotate=0, transparent=True, fixedwidth=True, dist=0, width=0, outline=0, color=0):
    pass

def fontSize():
    return (16, 16)

def textWidth(text):
    return 100

def pixel(x, y, color=-1):
    pass

def rect(x, y, width, height, color=-1, fillcolor=-1):
    pass

def roundrect(x, y, width, height, r, color=-1, fillcolor=-1):
    pass

def triangle(x, y, x1, y1, x2, y2, color=-1, fillcolor=-1):
    pass

def circle(x, y, r, color=-1, fillcolor=-1):
    pass

def arc(x, y, r, thick, start, end, color=-1, fillcolor=-1):
    pass

def text(x, y, txt, color=-1):
    pass
