from tkinter import *
from serial import *
import sys
import glob

# globals, can't find how to do better
exitFlag = False
root = Tk()

class CustomSerialException(Exception):
    pass

# a subclass of Canvas for dealing with resizing of windows
class ResizingCanvas(Canvas):
    def __init__(self,parent,**kwargs):
        Canvas.__init__(self,parent,**kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self,event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas 
        self.config(width=self.width, height=self.height)
        self.scale("all",0,0,wscale,hscale)     

def listSerialPorts():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = Serial(port)
            s.close()
            result.append(port)
        except (OSError, SerialException):
            pass
    return result

def serialPopup(message, size):
    global root
    popup = Toplevel()
    popup.geometry(size)
    popup.resizable(False, False)
    popup.title('Etch a Sketch : Serial connection')

    var = StringVar()
    label = Label(popup, textvariable=var).pack(pady=10)
    var.set(message)

    lst = listSerialPorts()

    var = StringVar(popup)
    var.set(lst[0]) # default value

    w = OptionMenu(popup, var, *lst).pack()

    buttons = Frame(popup).pack(side=TOP, pady=10)
    Button(popup, text='Exit', command=root.destroy).pack(in_=buttons, side=RIGHT, padx=10)
    Button(popup, text='Connect', command=popup.destroy).pack(in_=buttons, side=RIGHT, padx=(10,0))
    
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)
    return var

def infoPopup(message, size):
    global root
    popup = Toplevel()
    popup.geometry(size)
    popup.resizable(False, False)
    popup.title('Etch a Sketch : Info')

    var = StringVar()
    label = Label(popup, textvariable=var).pack(pady=10)
    var.set(message)

    Button(popup, text='Got it !', command=popup.destroy).pack()
    
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)

def keyup(e):
    if(e.keycode == 24 or e.keycode == 9):
        on_quit()

def on_quit():
    global exitFlag, root
    exitFlag = True
    root.destroy()

def main():
    global exitFlag, root
    shakeCount = 0

    # Main window title, minsize & quit event handler
    root.title('Etch a Sketc h')
    root.minsize(width=400, height=300) # 400x300 minimum window size, 'cause otherwise the logo won't be displayed correctly
    root.protocol("WM_DELETE_WINDOW", on_quit) 
    root.bind("<Key>", keyup)

    # Serial port popup & connection
    serialPort = serialPopup("Select a serial port to connect to :", "300x150").get()
    while True:
        try:
            ser = Serial(serialPort, 9800, timeout=1)
            # TODO : maybe improve this part ?
            # wait for a sec while arduino is resetting
            #time.sleep(1)
            # read launch message
            data = ser.readline()[:-2].decode('utf-8')
            if(data != 'Etch a Sketch USB'):
                raise CustomSerialException("Choosen serial device not responding as expected.")
            break
        except SerialException:
            serialPort = serialPopup("Cannot connect to choosen serial port !\n Please choose another one : ", "300x150").get()
        except CustomSerialException:
            serialPort = serialPopup("Choosen device is not responding as expected.\n Please choose another one or try to reconnect the device : ", "400x150").get()


    # Connected to USB device at this point, let's show a quick information popup and start drawing !
    infoPopup("Welcome to Etch a Sketch USB !\n\nYou're now ready to draw using the two knobs.\nTo erase, shake the device !\nPress q or Echap to quit.", "320x150")
    
    # TODO : add some sort of config popup ? (to choose color, "pencil" size ?)

    # window background has to be set to red, Etch a Sketch fashion
    root.configure(background='red')

    # bottom frame : logo placeholder
    logoFrame = Frame(root, background="red")
    logoFrame.pack(fill=Y, expand=False, side="bottom")
    # display the logo on this frame
    logo = PhotoImage(file='logo_app_small.png')
    logoLabel = Label(logoFrame, image=logo, background="red")
    logoLabel.pack(pady=(0,20))

    # canvas frame : where the drawing actually happens
    canvasFrame = Frame(root)
    canvasFrame.pack(fill=BOTH, expand=YES, padx=20, pady=20)
    # custom canvas object, with resizing capabilities (thanks StackOverflow)
    canvas = ResizingCanvas(canvasFrame, width=850, height=500, bg="gray")
    canvas.pack(fill=BOTH, expand=YES)
    # tag all of the drawn widgets (for resizing purpose)
    canvas.addtag_all("all")

    # exitFlag is set to true when the window exit button is hit or when q/Esc is pressed
    # this condition was necessary to avoid an exception being raised
    while not exitFlag:   
        try:
            # grab serial data
            data = ser.readline()[:-2].decode('utf-8')
            if(data != ''):
                size = canvas.winfo_height()/100
                # convert potentiometers values to canvas x,y position
                x = ((int(data.split(':')[0])*(canvas.winfo_width()-size))/1024)+(size/2)
                y = ((int(data.split(':')[1])*(canvas.winfo_height()-size))/1024)+(size/2)
                sw = data.split(':')[2]
                
                if(sw == '0'):
                    shakeCount += 1
                # if device shaked multiple times (approx 10, no debounce on arduino side)
                if(shakeCount > 10):
                    canvas.delete("draw")
                    shakeCount = 0
                
                # draw
                canvas.create_rectangle(x-(size/2), y-(size/2), x+(size/2), y+(size/2), fill='black', tags=('draw'))

            # update canvas thingy
            root.update_idletasks()
            root.update()
        except(SerialException):
            # raised when device is disconnected
            serialPort = serialPopup("Connection lost !\n Please reconnect or exit app : ", "300x150").get()

if __name__ == "__main__":
    main()
