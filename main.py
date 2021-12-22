from tkinter import *
import serial
import sys
import glob
import time

from serial.serialutil import SerialException

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
        # rescale all the objects tagged with the "all" tag
        #self.scale("all",0,0,wscale,hscale)
        self.scale("all",0,0,wscale,hscale)
        self.moveto("image", (self.width/2)-86, self.height-50)

        #self.scale("border_horizontal", 0, 0, wscale, 1)
        #self.scale("border_vertical", 0, 0, 1, hscale)        

def serial_ports():
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
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
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

    lst = serial_ports()

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

    root.title('Etch a Sketch')
    root.protocol("WM_DELETE_WINDOW", on_quit)
    root.configure(background='red')

    serialPort = serialPopup("Select a serial port to connect to :", "300x150").get()

    while True:
        try:
            ser = serial.Serial(serialPort, 9800, timeout=1)

            # wait for a sec while arduino is resetting
            #time.sleep(1)
            # read launch message
            data = ser.readline()[:-2].decode('utf-8')
            print(data)
            if(data != 'Etch a Sketch USB'):
                raise CustomSerialException("Choosen serial device not responding as expected.")
            break
        except SerialException:
            serialPort = serialPopup("Cannot connect to choosen serial port !\n Please choose another one : ", "300x150").get()
        except CustomSerialException:
            serialPort = serialPopup("Choosen device is not responding as expected.\n Please choose another one or try to reconnect the device : ", "400x150").get()

    infoPopup("Welcome to Etch a Sketch USB !\n\nYou're now ready to draw using the two knobs.\nTo erase, shake the device !\nPress q or Echap to quit.", "320x150")

    del_count = 0

    #root = Tk()
    bottomFrame = Frame(root, background="red")
    bottomFrame.pack(fill=Y, expand=False, side="bottom")
    #bottomCanvas = Canvas(bottomFrame, width=850, height=100, bg="green")
    #bottomCanvas.pack(fill=Y, expand=YES)

    myframe = Frame(root)
    myframe.pack(fill=BOTH, expand=YES, padx=20, pady=20)
    root.bind("<Key>", keyup)
    #root.resizable(False, False)

    # background = ResizingCanvas(root, width=850, height=400, bg='red')
    # #mycanvas.create_rectangle(0, 0, 850, 400, fill='red', outline='red')
    # img = PhotoImage(file='logo_app_small.png')
    # background.create_image((850/2)-86, 10, image=img)
    # background.pack(fill=BOTH, expand=YES)
    # background.addtag_all("all")

    #mycanvas = ResizingCanvas(myframe, width=850, height=400, bg="gray", highlightthickness=20, highlightbackground='red')
    mycanvas = ResizingCanvas(myframe, width=850, height=500, bg="gray")

    #mycanvas.create_rectangle(0, 0, 850, 20, fill='red', outline='red')
    #mycanvas.create_rectangle(0, 0, 20, 500, fill='red', outline='red')
    #mycanvas.create_rectangle(830, 0, 850, 500, fill='red', outline='red')
    #mycanvas.create_rectangle(0, 450, 850, 500, fill='red', outline='red')
    img = PhotoImage(file='logo_app_small.png')

    img_lbl = Label(bottomFrame, image=img, background="red")
    img_lbl.pack(pady=(0,20))
    #mycanvas.create_image(850/2, 420, anchor="center", image=img, tags=('image'))

    mycanvas.pack(fill=BOTH, expand=YES)

    # tag all of the drawn widgets
    mycanvas.addtag_all("all")

    
    

    while not exitFlag:
        # grab serial data
        try:
            data = ser.readline()[:-2].decode('utf-8')

            if(data != ''):
                x = ((int(data.split(':')[0])*(mycanvas.winfo_width()-40))/1024)+20
                y = ((int(data.split(':')[1])*(mycanvas.winfo_height()-70))/1024)+20
                sw = data.split(':')[2]
                if(sw == '0'):
                    del_count += 1
                if(del_count > 10):
                    mycanvas.delete("draw")
                    del_count = 0
                #mycanvas.create_line(x, y, x+5, y+5)
                size = (mycanvas.winfo_height()-40)/100
                id = mycanvas.create_rectangle(x-(size/2), y-(size/2), x+(size/2), y+(size/2), fill='black', tags=('draw'))

            # draw pixel
            #if(data != ""):
            #    print(data)

            # update
            root.update_idletasks()
            root.update()
        except(SerialException):
            serialPort = serialPopup("Connection lost !\n Please reconnect or exit app : ", "300x150").get()
        

if __name__ == "__main__":
    main()
