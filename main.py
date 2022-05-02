import pickle
import os
import tkinter
import tkButton
import sys
import time
from config import *
from tkinter import messagebox
from tkinter import filedialog
from PIL import ImageGrab

# Global Variables
state = "idle" # the state of the program
hover_text = "" # the text next to the mouse
mouse_x = 0
mouse_y = 0
debug_labels = [] # labels shown in debug mode
message = None # the current displayed message
add_component_menu_open = False # if the add component menu is open
current_preview_drawing = None # the current drawing in the add component menu
wire_buttons = [] # the wire selection buttons
wires = [] # wires currently existing in the workspace
current_wire = [None,None] # the current wire pairing
selected_wire_color = "" # the currently selected wire color
wire_preview = None # the wire preview drawing
new_component_id = 0 # the next component id
current_save_path = ""
debug_mode = False
previous_message_position = MESSAGE_POSITION
root_updated = 0

root = tkinter.Tk()

# Global Methods
def point_between(x,p1,p2): # check if x is between p1 and p2
    if (x >= p1 and x <= p2):
        return True
    return False

def coord_between(px,py,x1,y1,x2,y2): # check if (px,py) is within (x1,y1) and (x2,y2)
    if (point_between(px,x1,x2) and point_between(py,y1,y2)):
        return True
    return False

def motion(event): # update the (x,y) position of the mouse and draw the hover label
    global mouse_x
    global mouse_y
    x, y = event.x, event.y
    mouse_x,mouse_y = x,y
    hover_label.configure(text=hover_text)
    if (hover_text == ""):
        hover_label.place_forget()
    else:
        hover_label.place(anchor="nw",x=x+10,y=y+10)
        hover_label.lift()

def component_meets_conditions(name,w,h,color,shape,show_errors=True): # Return a bool based on if a component meets the conditions to add
    conditions_met = True
    if (color == "Select"): # color is selected
        conditions_met = False
        if (show_errors):
            show_message("Select component color",accent="red")
    elif (shape == "Select"): # shape is selected
        conditions_met = False
        if (show_errors):
            show_message("Select component shape",accent="red")
    elif (name == ""): # has a name
        conditions_met = False
        if (show_errors):
            show_message("Set component name",accent="red")
    elif (len(name) > MAX_COMPONENT_CHARACTERS): # name isn't too long
        conditions_met = False
        if (show_errors):
            show_message("Component name must be %s characters or less"%MAX_COMPONENT_CHARACTERS,accent="red")
    elif (w > MAX_COMPONENT_SIZE or h > MAX_COMPONENT_SIZE): # isn't too big
        conditions_met = False
        if (show_errors):
            show_message("Component must be smaller than 400x400",accent="red")
    elif (w < MIN_COMPONENT_SIZE or h < MIN_COMPONENT_SIZE): # isn't too small
        conditions_met = False
        if (show_errors):
            show_message("Component must be larger than 75x75",accent="red")
    return conditions_met

def add_component(workspace,name,w,h,color,shape,show_errors=True): # create and add a component to a workspace
    # Check h and w to make sure they are valid integers
    try:
        h = int(h)
    except ValueError:
        if show_errors:
            show_message("Invalid height",accent="red")
        return -1
    try:
        if show_errors:
            w = int(w)
    except ValueError:
        if show_errors:
            show_message("Invalid width",accent="red")
        return -1
    # Meets conditions
    conditions_met = component_meets_conditions(name,w,h,color,shape,show_errors=show_errors)
    # Set Colors
    color = canvas_color(color)
    # Add object
    if (conditions_met):
        obj = Component(workspace,name,300,300,w,h,color=color.lower(),shape=shape.lower())
        workspace.add_component(obj)
        close_component_menu()
        obj.handle_click(event="")
        root.focus()


def show_message(text,accent=MESSAGE_OUTLINE_COLOR): # shows a message at the top or bottom of the screen
    global message
    # delete the current message if it exists
    try:
        message.place_forget()
    except AttributeError:
        pass
    # create the message frame
    message_width = len(text)*11
    message_frame = tkinter.Frame(root,width=message_width,height=30,bg=MESSAGE_BG,highlightbackground=accent,highlightthickness=MESSAGE_OUTLINE_THICKNESS)
    if (MESSAGE_POSITION == "top"):
        message_frame.place(anchor="n",relx=0.5,rely=0.01)
    else:
        message_frame.place(anchor="s",relx=0.5,rely=0.99)
    tkinter.Label(message_frame,text=text,bg=MESSAGE_BG,fg=MESSAGE_FG,font="Menlo 15 bold").place(anchor="center",relx=0.5,rely=0.5)
    message = message_frame
    root.after(MESSAGE_DURATION*1000,lambda: message_frame.place_forget())

def draw_debug(): # handles drawing of all debug labels 
    global debug_labels
    for label in debug_labels:
        canvas.delete(label)
    debug_labels = []
    if (debug_mode):
        for label in debug_labels:
            canvas.delete(label)
        for component in workspace.components:
            # show x and y of all components
            debug_labels.append(canvas.create_text(component.x,component.y,text="(%s,%s)"%(component.x,component.y),anchor="se"))
        # show app info
        debug_labels.append(canvas.create_text(1190,10,text="%s (v%s)\nBy %s\nDEBUG ENABLED"%(PRODUCT,VERSION,DEVELOPER),anchor="ne",fill="white",justify="right"))
        # show performance mode
        debug_labels.append(canvas.create_text(1190,690,text="%s PERFORMANCE MODE"%PERFORMANCE_MODE,anchor="se",fill="white"))
        # show state and current wire combo
        debug_labels.append(canvas.create_text(310,10,text="STATE: %s\nCurrent wire: %s"%(state.upper(),current_wire),anchor="nw",fill="white"))
    root.after(DEBUG_SPEED,draw_debug)

def open_component_menu(): # open the new component menu
    global add_component_menu_open
    global state
    preview_canvas.delete("all")
    if (not add_component_menu_open and state == "idle"):
        add_component_menu_open = True
        state = "menu"
        add_component_frame.place(anchor="center",relx=0.5,rely=0.4)
        add_component_frame.lift()

def close_component_menu(): # close the new component menu and reset the parameters
    global add_component_menu_open
    global state
    if (add_component_menu_open):
        add_component_menu_open = False
        width_stringvar.set("100")
        height_stringvar.set("100")
        component_color.set("Select")
        component_shape.set("Select")
        component_name.delete(0,tkinter.END)
        state = "idle"
        add_component_frame.place_forget()

def update_component_preview(): # update the preview in the new component menu
    global current_preview_drawing
    try:
        w = int(width_stringvar.get())
        h = int(height_stringvar.get())
        color = canvas_color(component_color.get())
        shape = component_shape.get().lower()
        x = 228-w/2
        y = 180-h/2
        if (component_meets_conditions("component",w,h,color,shape,show_errors=False)):
            preview_canvas.delete("all")
            if (shape == "rect"):
                current_preview_drawing = preview_canvas.create_rectangle(x,y,x+w,y+h,outline="black",fill=color)
            elif (shape == "circle"):
                current_preview_drawing = preview_canvas.create_oval(x,y,x+w,y+h,outline="black",fill=color)
            elif (shape == "hex"):
                current_preview_drawing = preview_canvas.create_polygon(
                    x+w/4,y,
                    x+(w/4)*3,y,
                    x+w,y+h/4,
                    x+w,y+(h/4)*3,
                    x+(w/4)*3,y+h,
                    x+w/4,y+h,
                    x,y+(h/4)*3,
                    x,y+h/4,
                    outline="black",fill=color)
    except:
        pass
    finally:
        preview_canvas.create_text(228,355,anchor="s",text="PREVIEW",fill=WORKSPACE_BACKGROUND_COLOR,font="Menlo 16")
        root.after(PREVIEW_UPDATE_SPEED,update_component_preview)

def panel_label(text): # style of labels on left panel
    return tkinter.Label(panel,text=text,bg=ROOT_BACKGROUND_COLOR,fg=WORKSPACE_BACKGROUND_COLOR,font="Menlo 14 bold")

def canvas_color(color): # get actual colors for components
    if (color == "Red"):
        return "#990000"
    elif (color == "Black"):
        return "#333"
    elif (color == "Blue"):
        return "#3f3fd1"
    else:
        return color

def wire_color(color):  # get actual colors for wires
        if (color.lower() == "purple"):
            return "#a434eb"
        elif (color.lower() == "green"):
            return "#14c900"
        else:
            return color
    
def select_wire(color): # handle clicks on wire selectors
    global selected_wire_color
    global state
    if (state == "idle"):
        state = "wire"
    selected_wire_color = color.lower()

def update_wires(): # move wires with components
    global mouse_x
    global mouse_y

    for obj,wire,color,component1,ox1,oy1,component2,ox2,oy2 in wires:
        canvas.coords(wire,component1.x+ox1,component1.y+oy1,component2.x+ox2,component2.y+oy2)
        canvas.tag_raise(wire)

    root.after(WIRE_UPDATE_SPEED,update_wires)

def handle_global_click(event): # handle global click events and pass to objects
    clicked_object = None
    # Wires
    for wire in wires:
        if (wire[0].mouse_hover):
            clicked_object = wire[0]
    # Components
    for component in workspace.components:
        if (coord_between(mouse_x,mouse_y,component.x,component.y,component.x+component.w,component.y+component.h)):
            clicked_object = component
    # Trigger the click event
    try:
        clicked_object.handle_click(event)
    except AttributeError as e:
        pass

def open_wire_add_menu(current_wire): # Open the pin labels wire menu
    global state
    state = "menu"
    wire = current_wire[0][0]
    component1 = current_wire[0][1]
    component2 = current_wire[1][1]
    add_wire_frame.place(anchor="center",relx=0.5,rely=0.4)
    add_wire_from_label.configure(text="%s Pin Name"%(component1.name))
    add_wire_to_label.configure(text="%s Pin Name"%(component2.name))
    add_wire_button.command = lambda:close_wire_add_menu(wire)

def close_wire_add_menu(wire): # Close the pin labels wire menu and set the pin names
    name1 = add_wire_pin1_entry.get()
    name2 = add_wire_pin2_entry.get()
    if (len(name1) > MAX_PIN_CHARACTERS or len(name2) > MAX_PIN_CHARACTERS):
        show_message("Pin names must be 5 characters or less",accent="red")
    else:
        global state
        state = "idle"
        wire.set_pin_names(name1,name2)
        add_wire_frame.place_forget()
    add_wire_pin1_entry.delete(0,tkinter.END)
    add_wire_pin2_entry.delete(0,tkinter.END)

def get_wires_to_component(component): # get all wires connected to a given component
    connected_wires = []
    for wire in wires:
        if (wire[3] == component or wire[6] == component):
            connected_wires.append(wire[0])
    return connected_wires

def save(item,file): # Save an item using pickle
    with open(file,"wb") as f:
        pickle.dump(item,f)
    f.close()

def load(file,empty_return_value=None): # load a .pickle file
    if (os.path.exists(file)):
        with open(file,"rb") as f:
            return pickle.load(f)
    else:
        return empty_return_value

def save_session(workspace,event=""): # Save the current workspace to a .pickle file
    global current_save_path
    if (current_save_path == ""): # Get the save path
        current_save_path = filedialog.asksaveasfilename(filetypes=[("Workspace Files",".pickle")],title="Save Workspace")
    if (current_save_path != ""):
        _wires = []
        for wire in wires:
            w = []
            for item in wire:
                w.append(item)
            _wires.append(w)
        for wire in _wires:
            wire[0].drawing = None
            wire[0].wire_from_label = None
            wire[0].wire_to_label = None
            wire.append(wire[0].get_pin_names())
            wire.append(wire[0].initial_component.id)
            wire.append(wire[0].final_component.id)
        _components = workspace.components
        save_content = {"components":_components,"wires":_wires}
        if (os.path.exists(current_save_path)):
            os.remove(current_save_path)
        save(save_content,current_save_path)
        show_message("Workspace Saved to %s"%current_save_path)
    else:
        return "no file"

def save_session_as(workspace): # Save session as a new file
    global current_save_path
    prev_save_path = current_save_path
    current_save_path = "" 
    if (save_session(workspace) == "no file"):
        current_save_path = prev_save_path

def load_session(file): # Load a .pickle workspace
    global current_save_path
    global selected_wire_color
    global current_wire
    session = load(file,empty_return_value=None)
    if (session != None):
        workspace.clear()
        for component in session["components"]:
            new_component = Component(workspace,component.name,component.x-workspace.x,component.y-workspace.y,component.w,component.h,component.color,component.shape)
            new_component.id = component.id
            workspace.add_component(new_component)
        for wire in session["wires"]:
            new_wire = None
            for component in workspace.components:
                if (component.id == wire[-2]):
                    new_wire = Wire(wire[0].color,component,wire[0].initial_offset_x,wire[0].initial_offset_y)
                    for c in workspace.components:
                        if (c.id == wire[-1] and new_wire != None):
                            new_wire.set_final_component(c,wire[0].final_offset_x,wire[0].final_offset_y)
            new_wire.wire_from_label = tkinter.Label(root,text="from",bg="white",fg="black")
            new_wire.wire_to_label = tkinter.Label(root,text="to",bg="white",fg="black")
            selected_wire_color = wire[2]
            new_wire.set_pin_names(wire[-3][0],wire[-3][1])
            new_wire.draw()
            current_wire = [None,None]
        current_save_path = file
        show_message("Successfully Loaded Workspace.")

def select_load_session(): # Load session through file explorer
    load_session(filedialog.askopenfilename(filetypes=[("Workspace Files",".pickle")],title="Load Workspace"))

def question_exit(): # Ask to save or cancel before exiting
    save = messagebox.askyesnocancel("","You are about to exit %s.\n\nSave workspace?"%PRODUCT)
    if (save):
        save_session(workspace)
        exit()
    elif (save == None):
        pass
    else:
        exit()

def save_and_exit(): # Save and exit root
    save_session(workspace)
    exit()

def exit(): # Exit the root
    if (os.path.exists(SAVE_DATA_PATH)):
        os.remove(SAVE_DATA_PATH)
    if (current_save_path != ""):
        save({"current_save_path":current_save_path},SAVE_DATA_PATH)
    save_settings()
    root.destroy()

def update_title(): # Update the root title
    current_save_file = current_save_path.split("/")[-1].replace(".pickle","")
    new_title = "CircuitCreator v%s"%VERSION
    if (debug_mode):
        new_title += " (DEBUG MODE)"
    if (current_save_file == ""):
        current_save_file = "Untitled"
    new_title = current_save_file + " - " + new_title
    root.title(new_title)
    root.after(UPDATE_SPEED,update_title)

def new_session(): # Create a new workspace
    global current_save_path
    action = messagebox.askyesnocancel("","Save?\n\nDo you want to save changes to your current workspace before starting a new workspace?")
    if (action == True):
        save_session(workspace)
    if (action != None):
        workspace.clear()
        current_save_path = ""
        show_message("Started new workspace.")

def update_root(): # update elements of the root
    global debug_mode
    global PERFORMANCE_MODE
    global MESSAGE_POSITION
    global previous_message_position
    global root_updated
    # Debug Mode
    if (debug_stringvar.get() == "True"):
        debug_mode = True
    else:
        debug_mode = False
    # Update title
    current_save_file = current_save_path.split("/")[-1].replace(".pickle","")
    new_title = "CircuitCreator v%s"%VERSION
    if (debug_mode):
        new_title += " (DEBUG MODE)"
    if (current_save_file == ""):
        current_save_file = "Untitled"
    new_title = current_save_file + " - " + new_title
    root.title(new_title)
    # Update Performance Mode
    PERFORMANCE_MODE = performance_stringvar.get()
    # Update Message Position
    MESSAGE_POSITION = message_position_stringvar.get()
    if (MESSAGE_POSITION != previous_message_position and not root_updated == 0):
        show_message("Messages will appear here.")
    previous_message_position = MESSAGE_POSITION
    root_updated += 1
    root.after(UPDATE_SPEED,update_root)

def save_settings(): # save settings adjusted by the user
    settings = {
        "performance":PERFORMANCE_MODE,
        "message-position":MESSAGE_POSITION,
        "debug-mode":debug_mode
    }
    if (os.path.exists(SETTINGS_SAVE_PATH)):
        os.remove(SETTINGS_SAVE_PATH)
    save(settings,SETTINGS_SAVE_PATH)

def load_settings(): # load settings from previous session
    global MESSAGE_POSITION
    global PERFORMANCE_MODE
    global debug_mode
    settings = load(SETTINGS_SAVE_PATH,empty_return_value=None)
    if (settings != None):
        PERFORMANCE_MODE = settings["performance"]
        performance_stringvar.set(PERFORMANCE_MODE)
        MESSAGE_POSITION = settings["message-position"]
        message_position_stringvar.set(MESSAGE_POSITION)
        debug_mode = settings["debug-mode"]
        debug_stringvar.set(str(debug_mode))

def export_workspace(event=""):
    global message
    default_name = current_save_path.split("/")[-1].replace(".pickle","")+"_Diagram"
    export_file = filedialog.asksaveasfilename(filetypes=[("PNG Image",".png")],initialfile=default_name,title="Export Workspace")
    if (export_file != ""):
        watermark.place(anchor="se",relx=1,rely=0.99)
        show_message("Exporting...")
        root.after(200,lambda:post_export(export_file))
    else:
        show_message("An error occured during export.",accent="red")

def post_export(export_file):
    message.place_forget()
    x = root.winfo_rootx()+workspace.x
    y = root.winfo_rooty()+workspace.y
    x1 = x + root.winfo_width()-workspace.x
    y1 = y + root.winfo_height()-workspace.y
    x = x*2
    y = y*2
    x1 = x1*2
    y1 = y1*2
    root.after(100,lambda: ImageGrab.grab().crop((x,y,x1,y1)).save(export_file))
    root.after(200,watermark.place_forget)
    root.after(200,lambda:show_message("Exported Workspace to '%s'"%export_file))

class Workspace(): # where all the components, wires], etc. exist
    x = 0
    y = 0
    w = 0
    h = 0
    color = WORKSPACE_BACKGROUND_COLOR
    components = []
    show_trash = False
    trash_label = None

    def __init__(self,x,y,w,h,color=WORKSPACE_BACKGROUND_COLOR):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color

    def set_position(self,x,y): # Change the position of the work space
        self.x = x
        self.y = y
    
    def set_size(self,w,h): # Change the size of the workspace
        self.w = w
        self.h = h

    def add_component(self,obj): # Add a component to the workspace
        self.components.append(obj)
        show_message("Added component to workspace: %s"%obj.name)
        obj.draw()
        return True

    def draw(self): # draw the workspace on the tkinter canvas
        canvas.create_rectangle(self.x,self.y,self.x+self.w,self.y+self.h,fill=self.color,outline="")
        self.trash_label = canvas.create_text(self.x+self.w/2,self.y+self.h,text="REMOVE COMPONENT",fill=WORKSPACE_BACKGROUND_COLOR,font="Menlo 24 bold",anchor="s")

    def clear(self): # delete all components and wires in the workspace
        global wires
        for obj in self.components:
            canvas.delete(obj.get_drawing())
        self.components = []
        wires_to_delete = []
        for wire in wires:
            wires_to_delete.append(wire[0])
        for wire in wires_to_delete:
            wire.delete()
        wires = []

    def remove_object(self,obj): # remove an object from the workspace
        self.components.remove(obj)

    def update(self): # update the workspace by moving components, showing trash, etc
        global state
        global current_wire
        global mouse_x
        global mouse_y
        # component movement
        for component in self.components:
            if (component.moving):
                component.x = mouse_x-component.w/2
                component.y = mouse_y-component.h/2
        # show/hide trash
        if (state == "moving"):
            if (not self.show_trash):
                self.show_trash = True
                canvas.itemconfig(self.trash_label,fill=ROOT_BACKGROUND_COLOR)
        else:
            if (self.show_trash):
                self.show_trash = False
                canvas.itemconfig(self.trash_label,fill=WORKSPACE_BACKGROUND_COLOR)
        # Wire preview
        if (current_wire[0] != None and current_wire[1] == None):
            global wire_preview
            canvas.delete(wire_preview)
            wire_preview = canvas.create_line(current_wire[0][1].x+current_wire[0][2],current_wire[0][1].y+current_wire[0][3],mouse_x,mouse_y,fill=wire_color(selected_wire_color),width=WIRE_THICKNESS,capstyle=tkinter.ROUND)
        elif (wire_preview != None):
            canvas.delete(wire_preview)
            wire_preview = None
        # Cursor
        if (state == "idle"):
            root.configure(cursor=CURSOR_IDLE)
        elif (state == "wire"):
            root.configure(cursor=CURSOR_WIRE)
        elif (state == "moving"):
            root.configure(cursor=CURSOR_MOVING)
        # Run infinitely
        root.after(UPDATE_SPEED,self.update)

class Wire(): # wire connecting two components
    color = "Black"
    initial_component = None
    initial_offset_x = 0
    initial_offset_y = 0
    final_component = None
    final_offset_x = 0
    final_offset_y = 0
    drawing = None
    mouse_hover = False
    component_1_pin = ""
    component_2_pin = ""
    show_labels = False
    wire_from_label = None
    wire_to_label = None

    def __init__(self,color,initial_component,initial_offset_x,initial_offset_y):
        global current_wire
        self.color = color
        self.initial_component = initial_component
        self.initial_offset_x = initial_offset_x
        self.initial_offset_y = initial_offset_y
        current_wire = [(self,initial_component,self.initial_offset_x,self.initial_offset_y),None]
        self.wire_from_label = tkinter.Label(root,text="from",bg="white",fg="black")
        self.wire_to_label = tkinter.Label(root,text="to",bg="white",fg="black")
        self.labels()

    def delete(self): # delete the wire wrom the workspace
        global wires
        try:
            for wire in wires:
                try:
                    if (wire[0] == self):
                        wires.remove(wire)
                        canvas.delete(wire[1])
                        self.hover_off()
                        show_message("Deleted wire from %s (%s) to %s (%s)"%(self.initial_component.name,self.component_1_pin,self.final_component.name,self.component_2_pin))
                        del self
                except UnboundLocalError:
                    pass
        except IndexError:
            pass

    def set_pin_names(self,component_1_pin,component_2_pin): # set the pin names on either end of the wire
        self.component_1_pin = component_1_pin
        self.component_2_pin = component_2_pin

    def get_pin_names(self): # return (component_1_pin,component_2_pin)
        return (self.component_1_pin,self.component_2_pin)

    def set_final_component(self,component,offset_x,offset_y): # set the second component
        self.final_component = component
        self.final_offset_x = offset_x
        self.final_offset_y = offset_y
        current_wire[1] = (self,self.final_component,self.final_offset_x,self.final_offset_y)
    
    def handle_click(self,event): # delete the wire on click
        if (state == "idle"):
            self.delete()

    def hover_on(self,event): # mouse enters
        if (state == "idle" or state == "wire"):
            global hover_text
            hover_text = "%s -> %s"%(self.component_1_pin,self.component_2_pin)
            self.mouse_hover = True
            canvas.itemconfigure(self.drawing,width=WIRE_HOVER_THICKNESS)
            self.show_labels = True

    def hover_off(self,event=""): # mouse leaves
        global hover_text
        if (hover_text == "%s -> %s"%(self.component_1_pin,self.component_2_pin)):
            hover_text = ""
        self.mouse_hover = False
        canvas.itemconfigure(self.drawing,width=WIRE_THICKNESS)
        self.show_labels = False

    def labels(self): # Draw/Erase the labels for the pins on either end of the wire
        if (self.show_labels):
            self.wire_from_label.configure(text=self.component_1_pin)
            self.wire_to_label.configure(text=self.component_2_pin)
            x1,y1,x2,y2 = canvas.coords(self.drawing)
            self.wire_from_label.place(anchor="center",x=x1,y=y1)
            self.wire_to_label.place(anchor="center",x=x2,y=y2)
            if (hover_text == ""):
                self.wire_from_label.lift()
                self.wire_to_label.lift()
        else:
            try:
                self.wire_from_label.place_forget()
                self.wire_to_label.place_forget()
            except AttributeError:
                pass
        root.after(WIRE_UPDATE_SPEED,self.labels)

    def draw(self): # draw self and append to 'wires'
        if (self.initial_component != None and self.final_component != None):
            global wires
            color = wire_color(selected_wire_color)
            self.drawing = canvas.create_line(self.initial_component.x+self.initial_offset_x,self.initial_component.y+self.initial_offset_y,self.final_component.x+self.final_offset_x,self.final_component.y+self.final_offset_y,fill=color,width=WIRE_THICKNESS,capstyle=tkinter.ROUND)
            wires.append( (self,self.drawing,color,self.initial_component,self.initial_offset_x,self.initial_offset_y,self.final_component,self.final_offset_x,self.final_offset_y) )
            canvas.tag_bind(self.drawing,"<Enter>",self.hover_on)
            canvas.tag_bind(self.drawing,"<Leave>",self.hover_off)

class Component(): # an element in the workspace
    name = ""
    x = 0
    y = 0
    w = 0
    h = 0
    prev_x = 0
    prev_y = 0
    color = "green"
    border_color = "black"
    moving = False
    drawing = None
    shape = "rect"
    over_delete = False
    id = 0

    def __init__(self,workspace,name,x,y,w,h,color="green",shape="rect"):
        global new_component_id
        self.name = name
        self.x = workspace.x+x
        self.y = workspace.y+y
        self.w = w
        self.h = h
        self.color = color
        self.shape = shape 
        self.id = new_component_id
        new_component_id += 1
        self.movement()

    def delete(self): # remove component and all connected wires
        wires_to_delete = get_wires_to_component(self)
        for wire in wires_to_delete:
            wire.delete()
        canvas.delete(self.drawing)
        show_message("Deleted component: %s"%self.name)
        self.hover_off()
        workspace.remove_object(self)
        del self

    def set_position(self,x,y): # set the position of the object
        self.x = x
        self.y = y
    
    def set_size(self,w,h): # change the size of the object
        self.w = w
        self.h = h

    def hover_on(self,event1="",event2=""): # handle mouse hover on
        global state
        global hover_text
        if (state == "idle" or state == "wire"):
            hover_text = self.name
            canvas.itemconfig(self.drawing,outline="yellow")
            connected_wires = get_wires_to_component(self)
            for wire in connected_wires:
                wire.show_labels = True

    def hover_off(self,event1="",event2=""): # handle mouse hover off
        global state
        global hover_text
        if (state == "idle" or state == "wire"):
            hover_text = ""
            canvas.itemconfig(self.drawing,outline="black")
            connected_wires = get_wires_to_component(self)
            for wire in connected_wires:
                wire.show_labels = False

    def handle_click(self,event): # handle click
        global state
        global current_wire
        global wire_preview
        if (state != "menu"):
            if (state == "wire"): # wires
                if (current_wire == [None,None]):
                    Wire(selected_wire_color,self,event.x-self.x,event.y-self.y)
                elif (current_wire[1] == None):
                    current_wire[0][0].set_final_component(self,event.x-self.x,event.y-self.y)
                    current_wire[0][0].draw()
                    state = "idle"
                    for wire in current_wire:
                        wire[1].hover_off() 
                    open_wire_add_menu(current_wire)
                    current_wire = [None,None]
            elif (self.moving): # movement
                self.moving = False
                state = "idle"
                if (not self.over_delete):
                    canvas.itemconfig(self.drawing,outline="black")
                else:
                    self.delete()
            elif (not self.moving and state == "idle"):
                canvas.tag_raise(self.drawing)
                workspace.components.remove(self)
                workspace.components.append(self)
                state = "moving"
                self.moving = True
                canvas.itemconfig(self.drawing,outline="white")

    def get_drawing(self): # return the tkinter drawing
        return self.drawing

    def movement(self): # move object to x and y position on the canvas
        # movement
        if (self.x != self.prev_x or self.y != self.prev_y):
            if (self.drawing != None):
                canvas.moveto(self.drawing,self.x,self.y)
                if (self.moving and coord_between(self.x+self.w/2,self.y+self.h,workspace.x+workspace.w/2-200,workspace.y+workspace.h-50,workspace.x+workspace.w/2+200,workspace.y+workspace.h+1000)):
                    self.over_delete = True
                    canvas.itemconfig(self.drawing,outline="red")
                elif (self.moving):
                    self.over_delete = False
        if (self.moving and not self.over_delete):
            if (coord_between(mouse_x,mouse_y,self.x+self.w/2-MOUSE_OFF_COMPONENT_WARNING_RADIUS,self.y+self.h/2-MOUSE_OFF_COMPONENT_WARNING_RADIUS,self.x+self.w/2+MOUSE_OFF_COMPONENT_WARNING_RADIUS,self.y+self.h/2+MOUSE_OFF_COMPONENT_WARNING_RADIUS)):
                canvas.itemconfig(self.drawing,outline="white")
            else:
                canvas.itemconfig(self.drawing,outline="red")
        # hover events
        if (state == "wire"):
            if (coord_between(mouse_x,mouse_y,self.x,self.y,self.x+self.w,self.y+self.h) and hover_text == ""):
                self.hover_on()
            if (not coord_between(mouse_x,mouse_y,self.x,self.y,self.x+self.w,self.y+self.h) and hover_text == self.name):
                self.hover_off()
        self.prev_x = self.x
        self.prev_y = self.y
        root.after(UPDATE_SPEED,self.movement)

    def draw(self): # draw the component on the canvas
        if (self.shape == "rect"):
            self.drawing = canvas.create_rectangle(self.x,self.y,self.x+self.w,self.y+self.h,outline=self.border_color,fill=self.color)
        elif (self.shape == "circle"):
            self.drawing = canvas.create_oval(self.x,self.y,self.x+self.w,self.y+self.h,outline=self.border_color,fill=self.color)
        elif (self.shape == "hex"):
            self.drawing = canvas.create_polygon(
                self.x+self.w/4,self.y,
                self.x+(self.w/4)*3,self.y,
                self.x+self.w,self.y+self.h/4,
                self.x+self.w,self.y+(self.h/4)*3,
                self.x+(self.w/4)*3,self.y+self.h,
                self.x+self.w/4,self.y+self.h,
                self.x,self.y+(self.h/4)*3,
                self.x,self.y+self.h/4,
                outline=self.border_color,fill=self.color)
        canvas.tag_bind(self.drawing,"<Enter>",self.hover_on)
        canvas.tag_bind(self.drawing,"<Leave>",self.hover_off)

# Graphics
# Root Setup
root.geometry("1200x700")
root.configure(bg="lime")
root.iconphoto(False, tkinter.PhotoImage(file="logo.png"))
root.title("CircuitCreator v%s"%(VERSION))
root.bind("<Button-1>",handle_global_click)
root.protocol("WM_DELETE_WINDOW", question_exit)

# Key bindings
root.bind("<Command-s>",lambda x: save_session(workspace))
root.bind("<Command-Option-S>",lambda x: save_session(workspace))
root.bind("<Command-o>",lambda x: select_load_session())
root.bind("<Command-n>",lambda x: new_session())
root.bind("<Command-w>",lambda x: save_and_exit())
root.bind("<Command-Option-w>",lambda x: question_exit())
root.bind("<Command-c>",lambda x: open_component_menu())
root.bind("<Command-e>",lambda x: export_workspace())

# Menu Bar Setup
menu = tkinter.Menu(root)
# Workspace Menu
workspace_menu = tkinter.Menu(menu,tearoff=0)
workspace_menu.add_command(label="New Component",accelerator="Command-C",command=open_component_menu)
workspace_menu.add_separator()
workspace_menu.add_command(label="New Workspace",accelerator="Command-N",command=new_session)
workspace_menu.add_command(label="Load Workspace...", accelerator="Command-O", command=select_load_session)
workspace_menu.add_separator()
workspace_menu.add_command(label="Save Workspace", accelerator="Command-S", command=lambda: save_session(workspace))
workspace_menu.add_command(label="Save Workspace As...", accelerator="Command-Option-S", command=lambda: save_session_as(workspace))
workspace_menu.add_separator()
workspace_menu.add_command(label="Export Workspace...",accelerator="Command-E",command=export_workspace)
workspace_menu.add_separator()
workspace_menu.add_command(label="Exit", accelerator="Command-Option-W",command=question_exit)
workspace_menu.add_command(label="Save and Exit",accelerator="Command-W",command=save_and_exit)
# Configure Menu
configure_menu = tkinter.Menu(menu,tearoff=0)
performance_stringvar = tkinter.StringVar()
performance_stringvar.set(PERFORMANCE_MODE)
performance_menu = tkinter.Menu(configure_menu)
performance_menu.add_radiobutton(label="High",variable=performance_stringvar,value="HIGH")
performance_menu.add_radiobutton(label="Standard",variable=performance_stringvar,value="STANDARD")
performance_menu.add_radiobutton(label="Low",variable=performance_stringvar,value="LOW")
configure_menu.add_cascade(menu=performance_menu,label="Performance")
message_position_stringvar = tkinter.StringVar()
message_position_stringvar.set(MESSAGE_POSITION)
message_position_menu = tkinter.Menu(configure_menu)
message_position_menu.add_radiobutton(label="Display at Top",variable=message_position_stringvar,value="top")
message_position_menu.add_radiobutton(label="Display at Bottom",variable=message_position_stringvar,value="bottom")
configure_menu.add_cascade(menu=message_position_menu,label="Alerts")
configure_menu.add_separator()
debug_stringvar = tkinter.StringVar()
configure_menu.add_checkbutton(label="Developer View",variable=debug_stringvar,onvalue="True",offvalue="False")
# Add Menus to menubar
menu.add_cascade(label="Workspace",menu=workspace_menu)
menu.add_cascade(label="Configure",menu=configure_menu)
root.configure(menu=menu)

# Canvas Setup
canvas = tkinter.Canvas(root,width=1200,height=700,bg=ROOT_BACKGROUND_COLOR,highlightthickness=0)
canvas.place(anchor="center",relx=0.5,rely=0.5)

# Component Menu Setup
add_component_frame = tkinter.Frame(root,width=700,height=360,bg=MENU_BACKGROUND_COLOR,highlightthickness=3,highlightbackground="black")
add_component_frame.place(anchor="center",relx=0.5,rely=0.4)
# Menu Frame
component_menu_frame = tkinter.Frame(add_component_frame,bg=MENU_BACKGROUND_COLOR_ALT)
component_menu_frame.place(anchor="w",relx=0,rely=0.5,relwidth=0.35,relheight=1)
# Color
component_color = tkinter.StringVar()
component_color.set("Select")
add_component_color = tkinter.OptionMenu(component_menu_frame,component_color,*COMPONENT_COLORS)
add_component_color.configure(bg=MENU_BACKGROUND_COLOR_ALT,width=4,font="Menlo 12")
add_component_color.place(anchor="e",relx=0.95,rely=0.1)
tkinter.Label(component_menu_frame,text="Component Color",bg=MENU_BACKGROUND_COLOR_ALT,fg="white",font="Menlo 14").place(anchor="w",relx=0.05,rely=0.1)
# Shape
component_shape = tkinter.StringVar()
component_shape.set("Select")
add_component_shape = tkinter.OptionMenu(component_menu_frame,component_shape,*COMPONENT_SHAPES)
add_component_shape.configure(bg=MENU_BACKGROUND_COLOR_ALT,width=4,font="Menlo 12")
add_component_shape.place(anchor="e",relx=0.95,rely=0.22)
tkinter.Label(component_menu_frame,text="Component Shape",bg=MENU_BACKGROUND_COLOR_ALT,fg="white",font="Menlo 14").place(anchor="w",relx=0.05,rely=0.22)
# Width
width_stringvar = tkinter.StringVar()
width_stringvar.set(100)
add_component_width = tkinter.Spinbox(component_menu_frame, from_=100, to=400,textvariable=width_stringvar,width=6,fg="black",background="white",font="Menlo 14",highlightbackground=MENU_BACKGROUND_COLOR_ALT)
add_component_width.place(anchor="e",relx=0.95,rely=0.38)
tkinter.Label(component_menu_frame,text="Component Width",bg=MENU_BACKGROUND_COLOR_ALT,fg="white",font="Menlo 14").place(anchor="w",relx=0.05,rely=0.38)
# Height
height_stringvar = tkinter.StringVar()
height_stringvar.set(100)
add_component_height = tkinter.Spinbox(component_menu_frame, from_=100, to=400,textvariable=height_stringvar,width=6,fg="black",background="white",font="Menlo 14",highlightbackground=MENU_BACKGROUND_COLOR_ALT)
add_component_height.place(anchor="e",relx=0.95,rely=0.5)
tkinter.Label(component_menu_frame,text="Component Height",bg=MENU_BACKGROUND_COLOR_ALT,fg="white",font="Menlo 14").place(anchor="w",relx=0.05,rely=0.5)
# Name
tkinter.Label(component_menu_frame,text="Component Name",bg=MENU_BACKGROUND_COLOR_ALT,fg="white",font="Menlo 14").place(anchor="center",relx=0.5,rely=0.62)
component_name = tkinter.Entry(component_menu_frame,width=20,bg="white",fg="black",highlightthickness=0,relief="flat",insertbackground="black",justify="center")
component_name.place(anchor="n",relx=0.5,rely=0.66)
# Buttons
add_component_button = tkButton.Button(component_menu_frame,text="+ ADD COMPONENT",bg=BUTTON_COLOR,fg="white",width=220,height=40,font="Menlo 17 bold",command=lambda: add_component(workspace,component_name.get(),add_component_width.get(),add_component_height.get(),component_color.get(),component_shape.get()))
add_component_button.place(anchor="s",relx=0.5,rely=0.92)
add_component_button.button_frame.configure(highlightthickness=5,highlightbackground="#0942b3")
add_component_close_button = tkButton.Button(component_menu_frame,text="CANCEL",bg=MENU_BACKGROUND_COLOR_ALT,fg="red",font="Menlo 12",command=close_component_menu)
add_component_close_button.place(anchor="s",relx=0.5,rely=0.99)
# Preview Frame
component_preview_frame = tkinter.Frame(add_component_frame,bg=MENU_BACKGROUND_COLOR)
component_preview_frame.place(anchor="e",relx=1,rely=0.5,relwidth=0.65,relheight=1)
preview_canvas = tkinter.Canvas(component_preview_frame,width=455,height=360,bg=MENU_BACKGROUND_COLOR)
preview_canvas.place(anchor="center",relx=0.5,rely=0.5)
update_component_preview()
# Don't place this frame yet
add_component_frame.place_forget()

# Add wire menu setup
add_wire_frame = tkinter.Frame(root,width=400,height=200,bg=MENU_BACKGROUND_COLOR,highlightthickness=3,highlightbackground="black")
add_wire_frame.place(anchor="center",relx=0.5,rely=0.4)
# Original Component
add_wire_from_label = tkinter.Label(add_wire_frame,text="Connection 1",bg=MENU_BACKGROUND_COLOR,fg="white",font="Menlo 14")
add_wire_from_label.place(anchor="w",relx=0.03,rely=0.2)
add_wire_to_label = tkinter.Label(add_wire_frame,text="Connection 2",bg=MENU_BACKGROUND_COLOR,fg="white",font="Menlo 14")
add_wire_to_label.place(anchor="w",relx=0.03,rely=0.4)
# Pin name entries
add_wire_pin1_entry = tkinter.Entry(add_wire_frame,width=10,bg="white",fg="black",highlightthickness=0,relief="flat",insertbackground="black",justify="right")
add_wire_pin1_entry.place(anchor="e",relx=0.97,rely=0.2)
add_wire_pin2_entry = tkinter.Entry(add_wire_frame,width=10,bg="white",fg="black",highlightthickness=0,relief="flat",insertbackground="black",justify="right")
add_wire_pin2_entry.place(anchor="e",relx=0.97,rely=0.4)
# Add button
add_wire_button = tkButton.Button(add_wire_frame,text="+ ADD WIRE",bg=BUTTON_COLOR,fg="white",width=220,height=40,font="Menlo 17 bold")
add_wire_button.place(anchor="s",relx=0.5,rely=0.92)
add_wire_button.button_frame.configure(highlightthickness=5,highlightbackground="#0942b3")
# Don't place this frame yet
add_wire_frame.place_forget()

# Panel Setup
panel = tkinter.Frame(root,width=300,height=700,bg=ROOT_BACKGROUND_COLOR)
panel.place(anchor="nw",relx=0,rely=0)

# New Component button
panel_label("ADD COMPONENTS").place(anchor="s",relx=0.5,rely=0.04)
new_component_button = tkButton.Button(panel,text="+ NEW COMPONENT",bg=BUTTON_COLOR,fg="white",width=250,height=40,font="Menlo 17 bold",command=open_component_menu)
new_component_button.place(anchor="n",relx=0.5,rely=0.05)
new_component_button.button_frame.configure(highlightthickness=5,highlightbackground="#0942b3")

# Add Wires Setup
panel_label("ADD WIRE").place(anchor="s",relx=0.5,rely=0.82)
wire_buttons_frame = tkinter.Frame(panel,bg=MENU_BACKGROUND_COLOR,width=250,height=50)
wire_buttons_frame.place(anchor="s",relx=0.5,rely=0.9)
for color in WIRE_COLORS:
    wire_buttons.append(tkButton.Button(wire_buttons_frame,width=30,height=30,text=" ",bg=wire_color(color),command=lambda x=color:select_wire(x)))
for i in range(len(wire_buttons)):
    wire_buttons[i].place(anchor="center",relx=0.1+i/5,rely=0.5)
update_wires()

# Export Button Setup
export_button = tkButton.Button(panel,text="EXPORT WORKSPACE",bg=BUTTON_COLOR,fg="white",width=250,height=40,font="Menlo 17 bold",command=export_workspace)
export_button.place(anchor="s",relx=0.5,rely=0.99)
export_button.button_frame.configure(highlightthickness=5,highlightbackground="#0942b3")

# Watermark Setup
watermark = tkinter.Label(root,text=" Created with CircuitCreator ",bg="white",fg="black",font="Menlo 12")

# Mouse Setup
root.bind("<Motion>",motion)
hover_label = tkinter.Label(root,text="mouse",bg="white",fg="black")

# Workspace Setup
workspace = Workspace(300,0,900,700)
workspace.draw()
workspace.update()

# Sys Arguments
if ("--highperformance" in sys.argv):
    PERFORMANCE_MODE = "HIGH"
elif ("--lowperformance" in  sys.argv):
    PERFORMANCE_MODE = "LOW"
elif ("--standardperformance" in  sys.argv):
    PERFORMANCE_MODE = "STANDARD"
if ("--debug" in sys.argv):
    debug_mode = True
    if (not "--highperformance" in sys.argv and not "--standardperformance" in sys.argv):
        PERFORMANCE_MODE = "LOW"

# Load previous workspace
load_settings()
existing_data = load(SAVE_DATA_PATH,empty_return_value=None)
if (existing_data != None and os.path.exists(existing_data["current_save_path"] and existing_data["current_save_path"] != "")):
    load_session(existing_data["current_save_path"])

# Start infinite methods
draw_debug()
update_root()

# Run application
root.mainloop()