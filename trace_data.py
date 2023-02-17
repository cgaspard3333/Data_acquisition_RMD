import time
import sys
import matplotlib.pyplot as plt
import numpy as np
import math
import statistics

import os
  
# Folder Path
path = "dataset"
# Change the directory
os.chdir(path)

step = 0
g = 9.81 #m/s²
A_multi  = np.array([[0,0,0]]) 
A_multi = A_multi[:-1]
delta_speed_multi = np.array([])

def slider(value, array, size_sliding_windows):
    index_l = np.searchsorted(array,value - size_sliding_windows)
    index_h = np.searchsorted(array,value + size_sliding_windows,'right')
    array_slide = array[index_l:index_h]
    return array_slide, index_l, index_h

# iterate through all file
for file in os.listdir():
    # Check whether file is in text format or not
    if file.endswith(".txt"):
        file_path = f"{file}"
  
        f = open(file_path,"r")

        count = 0
        ts=np.array([])
        torque=np.array([])
        pos=np.array([])
        torque_cmd=np.array([])

        A_part2 = np.array([[0, 0],
                            [0, 0]]) 
        B = np.array([]) 
        
        while True:
            count += 1
            line = f.readline()

            if not line:
                break
            str = line.replace('\n', ',')
            new_str = str.split(',')

            ts = np.append(ts,int(new_str[0])/1e6)
            torque = np.append(torque,int(new_str[1]) * 33/2048)
            pos = np.append(pos,(int(new_str[2])-52706) * 2*math.pi/65535/6)
            torque_cmd = np.append(torque_cmd,int(new_str[3]) * 32/2000)

        size_sliding_windows = 0.05 #s =10ms
        sample_rate = 0.003 #s =10ms

        resampled_ts=np.array([])
        speed=np.array([])
        torque_lstsq=np.array([])
        pos_lstsq=np.array([])
        torque_cmd_lstsq=np.array([])

        for i in np.arange(int(ts[0]),int(ts[-1]),sample_rate):
            ts_window, index_l, index_h = slider(i, ts, size_sliding_windows)
            pos_slide = pos[index_l:index_h]
            torque_slide = torque[index_l:index_h]
            torque_cmd_slide = torque_cmd[index_l:index_h]
            
            A = np.vstack([ts_window, np.ones(len(ts_window))]).T
            pos_a, pos_b = np.linalg.lstsq(A, pos_slide, rcond=None)[0]
            torque_a, torque_b = np.linalg.lstsq(A, torque_slide, rcond=None)[0]
            torque_cmd_a, torque_cmd_b = np.linalg.lstsq(A, torque_cmd_slide, rcond=None)[0]

            speed = np.append(speed, pos_a)
            resampled_ts = np.append(resampled_ts, i)
            torque_lstsq = np.append(torque_lstsq, torque_a*i+torque_b)
            pos_lstsq = np.append(pos_lstsq, pos_a*i+pos_b)
            torque_cmd_lstsq = np.append(torque_cmd_lstsq, torque_cmd_a*i+torque_cmd_b)

        resampled_ts = resampled_ts[:-1]
        torque_lstsq = torque_lstsq[:-1]
        pos_lstsq = pos_lstsq[:-1]
        torque_cmd_lstsq = torque_cmd_lstsq[:-1]

        speed_new = speed[1:]
        speed = speed[:-1]
        speed_sign = np.sign(speed * (abs(speed) > 0.01))
        A_bis = sample_rate * np.vstack([torque_cmd_lstsq, -np.sin(pos_lstsq)*g, speed_sign]).T
        delta_speed = speed_new - speed
    
        delta_speed_multi = np.append(delta_speed_multi, delta_speed)
        A_multi = np.concatenate((A_multi, A_bis), axis=0)

    step = step + 1
    print("Step",step,"/",len(os.listdir()))

coeffs = np.linalg.lstsq(A_multi, delta_speed_multi, rcond=None)[0]

delta_speed_sim = A_bis @ coeffs

states = [
    [pos_lstsq[0], speed[0]]
]
for step in range(len(speed)):
    state = states[-1]
    speed_sign = 0.
    if abs(state[1]) > 0.1:
        speed_sign = np.sign(state[1])
    _delta_speed = coeffs[0] * torque_cmd_lstsq[step] - coeffs[1] * np.sin(state[0]) * g + coeffs[2] * speed_sign
    new_speed = state[1] + sample_rate * _delta_speed
    new_pos = state[0] + sample_rate * new_speed
    states.append([new_pos, new_speed])

states = np.array(states)

print(coeffs)
print("Alpha :", coeffs[0], "| Beta :", coeffs[1], "| l:", 1/coeffs[1])

fig, axs = plt.subplots(5, sharex=True)

# axs[0].plot(ts, pos)
# axs[0].set_xlabel('Time (s)')
# axs[0].set_ylabel('Position (rad)')

axs[0].plot(resampled_ts, pos_lstsq, color="red") 
axs[0].set_xlabel('Time (s)')
axs[0].set_ylabel('Position resampled (rad)')

axs[1].plot(resampled_ts, speed, color="green") 
axs[1].set_xlabel('Time (s)')
axs[1].set_ylabel('Speed (rad/s)')

axs[2].plot(resampled_ts, torque_lstsq, color="orange") 
axs[2].set_xlabel('Time (s)')
axs[2].set_ylabel('Sim Current (A)')

axs[2].plot(resampled_ts, torque_cmd_lstsq, color="green") 
axs[2].set_xlabel('Time (s)')
axs[2].set_ylabel('Current (A)')

axs[3].plot(resampled_ts, delta_speed, color="blue") 
axs[3].set_xlabel('Time (s)')
axs[3].set_ylabel('Delta speed')

axs[3].plot(resampled_ts, delta_speed_sim, color="orange") 
axs[3].set_xlabel('Time (s)')
axs[3].set_ylabel('Sim delta speed')

axs[4].plot(resampled_ts, pos_lstsq, color="blue") 
axs[4].set_xlabel('Time (s)')
axs[4].set_ylabel('Real pos')

axs[4].plot(resampled_ts, states.T[0][1:], color="orange") 
axs[4].set_xlabel('Time (s)')
axs[4].set_ylabel('Sim pos')

fig.suptitle('Position, Speed and Current of RMD-X6 with random current commands (+/-0.73A)', fontsize=16)

plt.show()