# Info
VERSION = "2.3.0"
DEVELOPER = "Rohan Dharwadker"
PRODUCT = "CircuitCreator"

# Look and Feel
ROOT_BACKGROUND_COLOR = "#999"
WORKSPACE_BACKGROUND_COLOR = "#777"
MENU_BACKGROUND_COLOR = "#555"
MENU_BACKGROUND_COLOR_ALT = "#333"
BUTTON_COLOR = "#0c5af5"
MESSAGE_BG = "white"
MESSAGE_FG = "black"
MESSAGE_OUTLINE_COLOR = "blue"
MESSAGE_OUTLINE_THICKNESS = "3"
MESSAGE_DURATION = 3
MESSAGE_POSITION = "top" # 'top' or 'bottom'
WIRE_THICKNESS = 5
WIRE_HOVER_THICKNESS = 10
CURSOR_IDLE = "arrow"
CURSOR_WIRE = "cross"
CURSOR_MOVING = "fleur"

# Speed
PERFORMANCE_MODE = "STANDARD"
if (PERFORMANCE_MODE == "STANDARD"):
    UPDATE_SPEED = 1
    DEBUG_SPEED = 100
    PREVIEW_UPDATE_SPEED = 100
    WIRE_UPDATE_SPEED = 50
elif (PERFORMANCE_MODE == "HIGH"):
    UPDATE_SPEED = 1
    DEBUG_SPEED = 1
    PREVIEW_UPDATE_SPEED = 1
    WIRE_UPDATE_SPEED = 1
elif (PERFORMANCE_MODE == "LOW"):
    UPDATE_SPEED = 100
    DEBUG_SPEED = 500
    PREVIEW_UPDATE_SPEED = 2000
    WIRE_UPDATE_SPEED = 1000

# Wires
WIRE_COLORS = ["Red","Black","White","Yellow","Purple"] # Exactly 5 colors allowed
MAX_PIN_CHARACTERS = 5

# Components
MOUSE_OFF_COMPONENT_WARNING_RADIUS = 20
MAX_COMPONENT_CHARACTERS = 20
MAX_COMPONENT_SIZE = 300
MIN_COMPONENT_SIZE = 75
COMPONENT_COLORS = ["Red","Orange","Yellow","Green","Blue","Purple","Gray","Black"]
COMPONENT_SHAPES = ["Rect","Circle","Hex"]

# Save
SAVE_DATA_PATH = "save/preferences/data.pickle"
SETTINGS_SAVE_PATH = "save/preferences/settings.pickle"