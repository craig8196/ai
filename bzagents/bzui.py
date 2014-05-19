import os
import io
import _tkinter
import time
from Tkinter import *
from threading import Thread, Event
from PIL import Image

class BZUI(Thread):
    """Create a thread that creates a graphical user interface."""
    def __init__(self, tanks, env_constants):
        super(BZUI, self).__init__()
        self.tanks = tanks
        self.env_constants = env_constants
    
    def run(self):
        """Run the gui."""
        root = Tk()
        gui = BZGUI(root, self.tanks, self.env_constants)
        gui.mainloop()
        root.destroy()

# Used to kill the entire process
def callback(root):
    if root:
        root.destroy()
    os._exit(0)


class BZGUI(Frame):
    def __init__(self, master, tanks, env_constants):
        Frame.__init__(self, master)
        
        self.tanks = tanks
        self.env_constants = env_constants
        self.selected_tank = -1
        
        self.root = master
        if self.root: # set closing window as closing program
            self.root.protocol('WM_DELETE_WINDOW', lambda r=self.root: callback(r))
        self['height'] = self.env_constants.worldsize + 100
        self['width'] = self.env_constants.worldsize + 400
        self.pack()
        self.root.title("BZFlag GUI")
        self.createWidgets()
        
        #~ self.grid_event = Event()
        #~ self.grid_event.clear()
        #~ self.env_constants.grid.add_update_event(self.grid_event)
        
    def createWidgets(self):
        WORLD_HEIGHT = self.env_constants.worldsize
        WORLD_WIDTH = self.env_constants.worldsize
        self.WORLD_HEIGHT = WORLD_HEIGHT
        self.WORLD_WIDTH = WORLD_WIDTH
        
        self.TOP_FRAME = Frame(self, height=WORLD_HEIGHT)
        self.TOP_FRAME.grid(column=0, padx=2, pady=2)
        
        # CONTROLS
        self.CONTROL_FRAME = Frame(self.TOP_FRAME, height=WORLD_HEIGHT)
        self.CONTROL_FRAME.pack(side=LEFT, padx=2, pady=2)
        
        self.LIST = None
        self.LIST = Listbox(self.CONTROL_FRAME, selectmode=SINGLE)
        self.LIST.bind("<ButtonRelease-1>", lambda x: self.select_tank(int(self.LIST.curselection()[0])))
        for tank in self.tanks:
            self.LIST.insert(END, "Tank " + str(tank.index))
        self.LIST.pack(side=TOP)
        
        self.ENABLE_PLOT = Checkbutton(self.CONTROL_FRAME, text="Enable Plot", command=self.enable_plot)
        self.ENABLE_PLOT.pack(side=TOP)
        
        #CANVAS
        #~ self.CANVAS = Canvas(self.TOP_FRAME,  width=WORLD_WIDTH, height=WORLD_HEIGHT, bg="#000000")
        #~ self.CANVAS.pack()
        #~ self.IMG = PhotoImage(width=WORLD_WIDTH, height=WORLD_HEIGHT)
        #~ self.IMG_ID = self.CANVAS.create_image((WORLD_WIDTH/2, WORLD_HEIGHT/2), image=self.IMG, state=NORMAL)
        
        # BOTTOM FRAME, for the text area
        self.BOTTOM_FRAME = Frame(self)
        self.BOTTOM_FRAME.grid(column=0, padx=2, pady=2, sticky=E+W+S+N)
        
        # TEXT
        self.TEXT = Text(self.BOTTOM_FRAME)
        self.TEXT.insert(END, "Welcome to the BZFlag GUI!\n")
        self.TEXT.grid(row=0, column=0, sticky=E+W+S+N)
    
    #~ def run_events(self):
        #~ self.run_grid_updater()
        #~ self.root.after(1000, self.run_events)
    #~ 
    #~ def run_grid_updater(self):
        #~ if self.grid_event.is_set():
            #~ self.display_grid()
            #~ self.grid_event.clear()
    #~ 
    #~ def display_grid(self):
        #~ """Chart the grid."""
        #~ grid = self.env_constants.grid
        #~ (x_len, y_len) = grid.get_shape()
        #~ new_image = Image.new('RGB', (x_len, y_len), 'black')
        #~ pixels = new_image.load()
        #~ print x_len, y_len
        #~ for x in xrange(0, x_len):
            #~ for y in xrange(0, y_len):
                #~ value = grid.get_value(x, y)
                #~ if value > grid.obstacle_threshold:
                    #~ pixels[x, y_len - y - 1] = (255, 255, 255)
                    #~ pixels[x, y] = (int(value*255), 0, 0)
                #~ else:
                    #~ pixels[x, y] = (0, int((1-value)*255), 0)
        #~ ppm = io.BytesIO()
        #~ new_image.save(ppm, 'ppm')
        #~ ppm_image = PhotoImage(data=ppm.getvalue())
        #~ temp_id = self.CANVAS.create_image((x_len/2, y_len/2), image=ppm_image)
        #~ self.CANVAS.delete(self.IMG_ID)
        #~ self.IMG_ID = ppm_image
    
    def enable_plot(self):
        if self.selected_tank == -1:
            return
        if self.tanks[self.selected_tank].is_plotting():
            self.tanks[self.selected_tank].stop_plotting()
            self.message("Stop plotting Tank " + str(self.selected_tank))
        else:
            self.tanks[self.selected_tank].start_plotting()
            self.message("Start plotting Tank " + str(self.selected_tank))
    
    def message(self, message):
        self.TEXT.insert(END, message + "\n")
    
    def select_tank(self, index):
        self.selected_tank = index
        self.root.title("Tank " + str(index) + " Selected")
        if self.tanks[index].is_plotting():
            self.ENABLE_PLOT.select()
        else:
            self.ENABLE_PLOT.deselect()
        self.message("Tank " + str(index) + " is selected.")

    

if __name__ == "__main__":
    ui = BZUI()
    ui.start()
    ui.join()
    exit(0)
