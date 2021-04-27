import os
import tkinter
import datetime
from dronekit import connect, Command, LocationGlobal
#from pymavlink import mavutil5
from pymavlink import mavutil
import time
import sys
import argparse
import math


print("Connecting")
#connection_string = '/dev/cu.usbmodem01'
connection_string = '0.0.0.0:14550'
vehicle = connect(connection_string, wait_ready=False, baud=921600)


print("Connected")
print(" Type: %s" % vehicle._vehicle_type)
print(" Armed: %s" % vehicle.armed)
print(" System status: %s" % vehicle.system_status.state)
print(" GPS: %s" % vehicle.gps_0)
print(" Alt: %s" % vehicle.location.global_relative_frame.alt)
print(" Mode: %s" % vehicle.mode.name)

coeff = 10

last_update = 0
min_delta_time = 1

def msg(vehicle, b):
    '''write some bytes'''
    while len(b) > 0:
        n = len(b)
        if n > 70:
            n = 70
        buf = [ord(x) for x in b[:n]]
        buf.extend([0]*(70-len(buf)))
        vehicle.get_handler().master.mav.serial_control_send(10,
                                            mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE |
                                            mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND,
                                            0,
                                            0,
                                            n,
                                            buf)
        b = b[n:]

root = tkinter.Tk()
canvas = tkinter.Canvas(root)
canvas.config(width=77*coeff, height=51*coeff)
canvas.pack()

msg_text = tkinter.StringVar()
msg_text.set("nxpcup ")
msg_history = list()
msg_history_ind = -1
def motion(event):
    global msg_history_ind, msg_history
    #print(event.keysym)
    if event.keysym == 'Escape':
        msg_history_ind = 0
        msg_text.set("nxpcup ")
    elif event.keysym == 'BackSpace':
        msg_text.set(msg_text.get()[:-1])
    elif event.keysym == 'Return':
        msg(vehicle, msg_text.get() + "\n")
        msg_history.append(msg_text.get())
        msg_history_ind = 0
        msg_text.set("nxpcup ")
    elif event.keysym == 'Up':
        if msg_history_ind < len(msg_history):
            msg_history_ind += 1
        msg_text.set(msg_history[-msg_history_ind])
    elif event.keysym == 'Down':
        if msg_history_ind > 1:
            msg_history_ind -= 1
        msg_text.set(msg_history[-msg_history_ind])
    else:
        msg_text.set(msg_text.get() + event.char)


msg_box = tkinter.Message(root, textvariable = msg_text, width=77*coeff)
msg_box.config(bg='lightgreen', font=('times', 24, 'italic'))
msg_box.bind('<KeyPress>',motion)
msg_box.focus_set()
msg_box.pack(expand=1, fill=tkinter.X)


@vehicle.on_message('DEBUG_FLOAT_ARRAY')
def listener(self, name, payload):
    global last_update, min_delta_time, canvas
#    print(name, payload)
    curr_time = datetime.datetime.now().microsecond
    if last_update + min_delta_time < last_update:
        return
    canvas.delete("all")
    data = payload.data
    vectors_count = int(data[0])
    for i in range(vectors_count + 3):
        # if (i < vectors_count):
        #     continue§
        line_width = 5
        color = None
        if i == vectors_count:
            color = 'blue'
        elif i == vectors_count + 1:
            color = 'red'
        elif i == vectors_count + 2:
            color = 'green'
            line_width = 3
        else:
            color = 'black'

        canvas.create_line(data[1 + i * 4] * coeff, data[2 + i * 4] * coeff,
                           data[3 + i * 4] * coeff, data[4 + i * 4] * coeff, arrow=tkinter.LAST, fill=color, width=line_width)

    canvas.create_text(77*coeff / 2, 51*coeff / 2, fill="green", font="Times 20 italic bold",
                       text=data[5 + i * 4])
    canvas.create_text(77*coeff / 2, 51*coeff / 2 + 25, fill="yellow", font="Times 20 italic bold",
                       text=data[6 + i * 4])
    last_update = curr_time


#os.system('xset r off')
root.mainloop()

