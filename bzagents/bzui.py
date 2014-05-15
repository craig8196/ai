import os
import _tkinter
from Tkinter import *
from threading import Thread

class BZUI(Thread):
    """Create a graphical user interface."""
    def __init__(self, tanks):
        super(BZUI, self).__init__()
        self.tanks = tanks
    
    def run(self):
        """Run the gui."""
        root = Tk()
        gui = BZGUI(self.tanks, root)
        gui.mainloop()
        root.destroy()


# Used to kill the entire process
def callback(root):
        if root:
            root.destroy()
        os._exit(0)


class BZGUI(Frame):
    def __init__(self, tanks, master=None):
        Frame.__init__(self, master)
        self.tanks = tanks
        self.selected_tank = -1
        self.root = master
        if self.root:
            self.root.protocol('WM_DELETE_WINDOW', lambda r=self.root: callback(r))
        self.pack()
        self.createWidgets()
    
    def createWidgets(self):
        self.LIST = None
        self.LIST = Listbox(self, selectmode=SINGLE)
        self.LIST.bind("<ButtonRelease-1>", lambda x: self.select_tank(int(self.LIST.curselection()[0])))
        for tank in self.tanks:
            self.LIST.insert(END, "Tank " + str(tank.index))
        self.LIST.pack(side='left')
        
        self.LABEL = Label(self)
        self.LABEL['text'] = "NO TANK SELECTED"
        self.LABEL.pack(side='left')
        self.ENABLE_PLOT = Checkbutton(self, text="Enable Plot", command=self.enable_plot)
        self.ENABLE_PLOT.pack(side='left')
        
        self.TEXT = Text(self)
        self.TEXT.insert(END, "Welcome to the BZFlag GUI!\n")
        self.TEXT.pack(side='bottom')
    
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
        self.LABEL['text'] = "Tank " + str(index) + " Selected"
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
