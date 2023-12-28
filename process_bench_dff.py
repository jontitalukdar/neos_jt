"""
This code is written to inject the XOR scrambler into a .bench design
Date: 13 Oct 20
Author: Jonti Talukdar
"""

import re
import sys
import os
import pdb

#File reading function
def file_reader(file_path, line_arr):
    with open(file_path, "r") as f:
        data = f.readlines()
        for line in data:
            line_arr.append(line)
    print("Read OK: %s"%(file_path))
    return

#File writing function
def file_writer(file_path, line_arr):
    with open(file_path, "w") as f:
        for lines in line_arr:
            f.write(lines)
    print("Success Write: %s"%(file_path))
    return

#Identify [/] in string and replace with _
def replace_bracket(net):
    replacement = ""
    for char in net:
        if(char in ["[", "]"]):
            replacement = replacement  + "_"
        else:
            replacement = replacement  + char
    return replacement

#Create a dictionary of inputs/outputs 
def process_ios(line_arr):
    input_dict = {}
    output_dict = {}
    for i,line in enumerate(line_arr):
        ip_regex = r"INPUT\((.*)\)"
        m = re.search(ip_regex, line.strip())
        if(m):
            input_dict[i] = m.group(1).strip()
    for i,line in enumerate(line_arr):
        op_regex = r"OUTPUT\((.*)\)"
        m = re.search(op_regex, line.strip())
        if(m):
            output_dict[i] = m.group(1).strip()
    return input_dict, output_dict

#Replace input with input_scr_out
def replace_inputs(line_arr):
    input_dict, output_dict = process_ios(line_arr)
    replace_line_arr = []
    for i,line in enumerate(line_arr):
        #First check to identify all input nets 
        if(line.startswith("INPUT") or line.startswith("OUTPUT")):
            replace_line_arr.append(line)
            insert_id = i
            continue
        #Second check after extracting all inputs to replace input with scrambler output
        else:
            #Deconstruct line, replace items, reconstruct line
            m = re.search(r"(.*)=(.*)\((.*)\)", line)
            if(m):
                output = m.group(1).strip()
                gate = m.group(2).strip()
                nets = m.group(3).strip().split(",")
                replace_string = "%s = %s("%(output, gate)
                for j,net in enumerate(nets):
                    net = net.strip()
                    if(net in input_dict.values()):
                        #*Check to replace [/] in string
                        replace_net = replace_bracket(net)
                        nets[j] = "%s_scr_out"%(replace_net)
                    if(j == 0):
                        replace_string = replace_string + nets[j].strip() 
                    else:
                        replace_string = replace_string + ", " + nets[j].strip()
                replace_string = replace_string + ")\n"
                replace_line_arr.append(replace_string)
    # file_writer("replaced.bench", replace_line_arr)
    return replace_line_arr, insert_id          

#Add xor gates to replaced arr
def add_gates(replace_lin_arr, insert_id):
    input_dict, output_dict = process_ios(replace_lin_arr)
    #Add inputs first
    for j,value in enumerate(input_dict.values()):
        #*Check to replace [/] in string
        replace_net = replace_bracket(value)
        xor2_line = "%s_scr_out = xor(%s, %s_scr_in)\n"%(replace_net, replace_net, replace_net)
        replace_lin_arr.insert(insert_id, xor2_line)
        xor1_line = "%s_scr_in = xor(keyinput%d, keyinput%d)\n"%(replace_net, 2*j, 2*j+1)
        replace_lin_arr.insert(insert_id, xor1_line)
        input1_line = "INPUT(keyinput%d)\n"%(2*j)
        replace_lin_arr.insert(insert_id, input1_line)
        input2_line = "INPUT(keyinput%d)\n"%(2*j+1)
        replace_lin_arr.insert(insert_id, input2_line)
    return

#Functio to replace vdd with input
def replace_vdd(line_arr, input_dict, output_dict):
    new_line_arr = []
    insert_list = [] #Stores vdd nets to be added as inputs
    output_list = []
    #First for loop to search for vdda
    for i, line in enumerate(line_arr):
        m = re.search(r"(.*)= vdd", line.strip())
        if(m):
            #If vdd found, and it is output, ignore it.
            # pdb.set_trace()
            if(m.group(1).strip() not in output_dict.values()):
                insert_list.append(m.group(1).strip())
                print("Inserting net: %s from line %s"%(m.group(1).strip(), line))
            else:
                output_list.append("OUTPUT(%s)\n"%(m.group(1).strip()))
            line_arr[i] = "-----\n"
    #Second for loop to insert inputs 
    for net in insert_list:
        input_line = "INPUT(%s)\n"%(net)
        insert_index = sorted(input_dict.keys())[-1] + 1
        print("Insert index: %d, %s"%(insert_index, net))
        input_dict[insert_index] = net
        line_arr.insert(insert_index, input_line)
    #Third for loop to create new list
    for line in line_arr:
        if(line == "-----\n"):
            continue
        elif(line in output_list):
            continue
        else:
            new_line_arr.append(line)
    return new_line_arr

#Function to replace square brackets"
def replace_square(line_arr):
    replace_line_arr = []
    #First replace INPUTs and outputs
    for i,line in enumerate(line_arr):
        #First check to identify all input nets 
        if(line.startswith("INPUT") or line.startswith("OUTPUT")):
            #Within input and output nets, replace any square brackets wherever applicable
            q = re.search(r"(.*)\((.*)\)", line.strip())
            if(q):
                replace_pi_po = replace_bracket(q.group(2).strip())
                line = "%s(%s)\n"%(q.group(1), replace_pi_po)
            replace_line_arr.append(line)
            insert_id = i
            continue
        #Second check after extracting all inputs to replace input with scrambler output
        else:
            #Deconstruct line, replace items, reconstruct line
            m = re.search(r"(.*)=(.*)\((.*)\)", line)
            if(m):
                output = m.group(1).strip()
                gate = m.group(2).strip()
                nets = m.group(3).strip().split(",")
                replace_string = "%s = %s("%(replace_bracket(output), gate) #Added replace bracket to output to replace [/] 
                for j,net in enumerate(nets):
                    net = net.strip()
                    if(j == 0):
                        replace_string = replace_string + replace_bracket(nets[j].strip()) #Added replace bracket to other strings
                    else:
                        replace_string = replace_string + ", " + replace_bracket(nets[j].strip()) #Added replace bracket to other strings
                replace_string = replace_string + ")\n"
                replace_line_arr.append(replace_string)
    return replace_line_arr

#Create a dictionary of inputs/outputs 
def remove_qin_dout(line_arr):
    input_dict, output_dict = process_ios(line_arr)
    new_line_arr = []
    skip_ids = []
    for key in sorted(input_dict.keys()):
        m = re.search(r"q_in_([0-9]*)", input_dict[key])
        n = re.search(r"qn_in_([0-9]*)", input_dict[key])
        o = re.search(r"d_out_([0-9]*)", input_dict[key])
        if(m or n or o):
            skip_ids.append(key)
    for key in sorted(output_dict.keys()):
        p = re.search(r"q_in_([0-9]*)", output_dict[key])
        q = re.search(r"qn_in_([0-9]*)", output_dict[key])
        r = re.search(r"d_out_([0-9]*)", output_dict[key])
        if(p or q or r):
            skip_ids.append(key)
    
    #! Generate and Insert DFF Logic
    dff_arr = []
    for key in sorted(input_dict.keys()):
        if(input_dict[key].startswith("q")):
            s = re.search(r"q_in_([0-9]*)", input_dict[key])
            t = re.search(r"qn_in_([0-9]*)", input_dict[key])
            if(s):
                id = s.group(1)
            elif(t):
                id = t.group(1)
            # print(key, id)
            dff_string = "%s = dff(d_out_%s)\n"%(input_dict[key], str(id))
            dff_arr.insert(0, dff_string)
    
    #! Insert the dff string after last output
    for line in dff_arr:
        line_arr.insert(sorted(output_dict.keys())[-1] + 1, line)
        # print("Inserted flop in line %d"%(skip_ids[-1] + 1))

    #! Generate final line array
    for i, line in enumerate(line_arr):
        if(i in skip_ids):
            continue
        else:
            new_line_arr.append(line)
    # print(skip_ids)
    # print(len(skip_ids))
    # print(skip_ids[-1])
    # for lin in new_line_arr:
    #     print(lin)
    return new_line_arr

"""
Main
"""
lin_arr = []
cwd = os.getcwd()
bench_path = os.path.join(cwd, sys.argv[1])
file_reader(bench_path, lin_arr)

#* STEP 1: Process inputs
input_dict, output_dict = process_ios(lin_arr)
print(input_dict, output_dict)

#* STEP 1.5: If vdd found in the design, assign the net as INPUT if it is not part of output
new_lin_arr = replace_vdd(lin_arr, input_dict, output_dict)
#* STEP 1.75 Replace square brackets
replace_lin_arr = replace_square(new_lin_arr)

file_writer(os.path.join(cwd, sys.argv[1][:-6] + "_orig.bench"), replace_lin_arr)

# TODO: Remove an input / output from the list of line array with a while loop 
dff_lin_arr = remove_qin_dout(replace_lin_arr)
file_writer(os.path.join(cwd, sys.argv[1][:-6] + "_dff_orig.bench"), dff_lin_arr)

#* STEP 2: Replace input nets
final_lin_arr, insert_id = replace_inputs(dff_lin_arr)

#* STEP 3: Add two gates
add_gates(final_lin_arr, insert_id)

# #* STEP 4: Final Write
# file_writer(os.path.join(cwd, sys.argv[1][:-6] + "_dff_enc.bench"), final_lin_arr)