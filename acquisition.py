import serial 
import time
import struct
import sys
import random

ser = serial.Serial('/dev/ttyACM0',921600)  # open serial port 921600,8,N,1

print(ser.name)         # check which port was really used

# ser.write(b'echo off\r')     # write a string
# time.sleep(0.5)

f = open("data.txt","a")
# # print("Initialisation")
# ser.write(b'start 1\r')

# time.sleep(5)

# data = ser.readline()

# ser.write(b'torque_cmd 1 0.3\r')     # write a string
# print(ser.readline())

test = input()

ser.write(b'exp\r')     # write a string
print(ser.read(2)) # eliminate first '\r\n'

for i in range (0,20001):
    # if i % 1000 == 0:
    #     currentvalue = round(random.uniform(-0.1,0.1),1)
    #     torque_head = "torque_cmd 1 "
    #     torque_cmd = torque_head + str(currentvalue)
    #     torque_cmd_ascii = torque_cmd.encode('ascii') 
    #     ser.write(torque_cmd_ascii)
    header = ser.read(1)
    if header == b'\xff':
        header2 = ser.read(1)
        if header2 == b'\xaa':
            data = ser.read(10)
            delta_t, current, pos = struct.unpack('<Ihi',data)
            # print(delta_t, current, pos)
            f.write(str(delta_t))
            f.write(",")
            f.write(str(current))
            f.write(",")
            f.write(str(pos))
            f.write("\n")
        
    # print(data)

ser.close()             # close port