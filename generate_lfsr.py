import os
import sys
import random
import math

#!This function prints up till 1 to N-1 LFSRs
def print_lfsrs(start_index, lfsr_size, lin_arr):

    lin_arr.append("\n")
    lin_arr.append("d%d = xor(keyinput%d, muxout%d)\n"%(start_index, start_index,  start_index + 1))
    for i in range(start_index + 1, start_index + 1 + lfsr_size):
        lin_arr.append("d%d = dff(d%d)\n"%(i, i-1))
    lin_arr.append("doubt%d = dff(d%d)\n"%(lfsr_size + start_index + 1, lfsr_size + start_index))

    for i in range(start_index + 1 , start_index + lfsr_size):
        lin_arr.append("\n")
        lin_arr.append("xorout%d = xor(d%d, muxout%d)\n"%(i, i, i+1))
        lin_arr.append("inter%d = and(keyinput%d, xorout%d)\n"%(i, i, i))
        lin_arr.append("inver%d = not(keyinput%d)\n"%(i, i))
        lin_arr.append("outer%d = and(inver%d, muxout%d)\n"%(i, i, i+1))
        lin_arr.append("muxout%d = or(inter%d, outer%d)\n"%(i, i, i))
    
    return

def print_last_lfsr(lfsr_size, lin_arr):
    lin_arr.append("\n")
    lin_arr.append("xorout%d = xor(d%d, doubt%d)\n"%(lfsr_size, lfsr_size, lfsr_size+1))
    lin_arr.append("inter%d = and(keyinput%d, xorout%d)\n"%(lfsr_size, lfsr_size, lfsr_size))
    lin_arr.append("inver%d = not(keyinput%d)\n"%(lfsr_size, lfsr_size))
    lin_arr.append("outer%d = and(inver%d, doubt%d)\n"%(lfsr_size, lfsr_size, lfsr_size + 1))
    lin_arr.append("muxout%d = or(inter%d, outer%d)\n"%(lfsr_size, lfsr_size, lfsr_size))
    
    return

def print_compout(degree, lin_arr):
    lin_arr.append("\n")
    for i in range(1, degree):
        lin_arr.append("compout%d = xor(d%d, d%d)\n"%(i-1, i, i+degree))
    lin_arr.append("compout%d = xor(doubt%d, doubt%d)\n"%(degree-1, degree, degree + degree))

#File writing function
def file_writer(file_path, line_arr):
    with open(file_path, "w") as f:
        for lines in line_arr:
            f.write(lines)
    print("Success Write: %s"%(file_path))
    return

#Reduction of xor output to match scrambler inputs
def upsample(start, end, degree, lin_arr):
    lfsr_output = degree
    if(end > start):
        print("upsampling")
        lin_arr.append("\n")
        for i in range(start, end, 1):
            lin_arr.append("compout%d = xor(d%d, d%d)\n"%(i, random.randint(0, end), random.randint(0, end)))
    return

# Print LFSRs
degree = 16 
lfsr_size = degree - 1

lin_arr = []

for i in range(0, degree*2):
    lin_arr.append("INPUT(keyinput%d)\n"%(i))

print_lfsrs(0, lfsr_size, lin_arr)
print_last_lfsr(lfsr_size, lin_arr)

print_lfsrs(degree, lfsr_size, lin_arr)
print_last_lfsr(lfsr_size + degree, lin_arr)

print_compout(degree, lin_arr)

upsample(16, 10, degree, lin_arr)

file_writer("output.txt", lin_arr)
os.system("cat output.txt")
# Print 

