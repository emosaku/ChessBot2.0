BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8
SIDEBAR_WIDTH = 360
WIDTH = BOARD_SIZE + SIDEBAR_WIDTH
HEIGHT = BOARD_SIZE

# Board colors
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE  = (181, 136, 99)
HIGHLIGHT    = (186, 202, 68)

# Sidebar / general UI
BG_COLOR   = (30, 26, 22)
TEXT_COLOR = (235, 225, 210)
DIM_COLOR  = (160, 150, 135)
GOLD_COLOR = (212, 175, 55)
DIVIDER_COLOR = (70, 60, 50)

# Advantage colors
ADV_WHITE = (230, 230, 230)
ADV_BLACK = (80, 80, 80)

# Menu button palette
BTN_FILL        = (90, 60, 30)
BTN_FILL_HOVER  = (120, 85, 45)
BTN_BORDER      = (212, 175, 55)
BTN_KEY_BG      = (55, 38, 18)
BTN_TEXT        = (245, 235, 215)

# Captured piece icons
SMALL_ICON_SIZE = 22
SMALL_ICON_GAP  = 4

# Menu button layout
_BTN_W, _BTN_H = 330, 58
_BTN_X = WIDTH // 2 - _BTN_W // 2
_BTN_Y_START = 240
_BTN_GAP = 18

MENU_BUTTON_RECTS = [
    (_BTN_X, _BTN_Y_START + i * (_BTN_H + _BTN_GAP), _BTN_W, _BTN_H)
    for i in range(2)
]
MENU_BUTTON_LABELS = [
    ("1", "Play as White"),
    ("2", "Play as Black"),
]
