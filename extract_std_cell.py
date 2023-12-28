
import os
import sys
import re
import subprocess
import time
import copy

#File reading function
def file_reader(file_path, line_arr):
    with open(file_path, "r") as f:
        data = f.readlines()
        for line in data:
            line_arr.append(line)
    print("File Read Successfully: %s"%(file_path))
    return

#File writing function
def file_writer(file_path, line_arr):
    with open(file_path, "w") as f:
        for lines in line_arr:
            f.write(lines)
    print("File Written Successfully: %s"%(file_path))
    return

#Netlist preprocessor
def netlist_parser(line_arr):
    parsed_line_arr = []
    #!Start scanning lines. Begin when you see module
    begin = False
    add_line = ""
    comment_on = True
    for line in line_arr:
        str_line = line.strip()
        if(line.startswith("module")):
            begin = True
            comment_on = False
        if(begin):
            if(str_line.startswith("//")):
                continue
            if(str_line.startswith("/*")):
                comment_on = True
            if(str_line.endswith("*/")):
                comment_on = False
            if(comment_on == False):
                if(str_line.endswith("endmodule")):
                    begin = False
                    parsed_line_arr.append("endmodule\n")
                    break
                if(str_line.endswith(";")):
                    add_line = add_line + str_line + "\n"
                    parsed_line_arr.append(add_line)
                    add_line = ""
                else:
                    add_line = add_line + str_line 
    print("Netlist pre-processing successful...")
    return parsed_line_arr

#Extract module definition
def module_def(line_arr):
    module_name = None
    inout_list = None
    for line in line_arr:
        if(line.startswith("module")):
            words = line.strip().split()
            m = re.search(r"(.*?)\((.*?)\);", line)
            # print(line)
            if(m):
                module_name = m.group(1).split()[1]
                inoutlist = m.group(2).split(",")
                inout_list = [item.strip() for item in inoutlist]
                # print(module_name, inout_list)
            break
    print("Module definition extraction successful...")
    return module_name, inout_list

#Extract inout wires
def extract_inout_wire(line_arr):
    #Global dict with each element being a line/array
    wire_dict = {}
    input_dict = {}
    output_dict = {}
    for i, line in enumerate(line_arr):
        #Each line containing multiple wires/inouts
        wire_arr = []
        input_arr = []
        output_arr = []
        if(line.startswith("wire ")):
            words = line[4:].strip().split(",")
            for word in words:
                word = word.strip()
                if(word.endswith(";")):
                    word = word[:-1]
                wire_arr.append(word)
            wire_dict[i] = wire_arr
        elif(line.startswith("input ")):
            words = line[5:].strip().split(",")
            for word in words:
                word = word.strip()
                if(word.endswith(";")):
                    word = word[:-1]
                input_arr.append(word)
            input_dict[i] = input_arr
        elif(line.startswith("output ")):
            words = line[6:].strip().split(",")
            for word in words:
                word = word.strip()
                if(word.endswith(";")):
                    word = word[:-1]
                output_arr.append(word)
            output_dict[i] = output_arr
    # print(wire_dict)
    # print(input_dict)
    # print(output_dict)
    print("Input/Output/Wire information extraction successful...")
    return wire_dict, input_dict, output_dict

#Flip Flop Parser
def flop_parser(line_arr, module_name, inout_list, wire_dict, input_dict, output_dict):
    final_arr = []
    flop_dict = {"DFFX1":["Q", "CK", "D", "QN"], "DFFSRX1":["Q", "CK", "D", "QN", "SN", "RN"], "SDFFSRX1":["Q", "CK", "D", "QN", "SN", "RN"]}
    flop_cnt = 0
    for i,line in enumerate(line_arr):
        words = line.strip().split()
        #Continue case
        if(line.startswith("module") or line.startswith("wire") or line.startswith("input") or line.startswith("output")):
            continue
        #Check for flop
        if(words[0].strip() in flop_dict.keys()):
            flop_cnt += 1
            regex = r"(.*?)\((.*?)\);"
            m = re.search(regex, line.strip())
            if(m):
                #If flop found, check for nets / pins
                net_D = None
                net_Q = None
                net_Qn = None
                nets = m.group(2).split(",")
                net_list = [net.strip() for net in nets]
                for net in net_list:
                    if(net.startswith(".D")):
                        q = re.search(r"(.*?)\((.*?)\)", net)
                        if(q):
                            net_D = q.group(2).strip()
                    elif(net.startswith(".QN")):
                        q = re.search(r"(.*?)\((.*?)\)", net)
                        if(q):
                            net_Qn = q.group(2).strip()
                    elif(net.startswith(".Q")):
                        q = re.search(r"(.*?)\((.*?)\)", net)
                        if(q):
                            net_Q = q.group(2).strip()
                assert(len(net_D) > 0)
                assert(net_Qn != None)
                assert(net_Q != None)

                #*Replace pins with buffers/invereters where required
                # if(len(net_Q) > 0):
                #     append_line = "CLKBUFX1 gbuf%d(.A(%s), .Y(%s));\n"%(flop_cnt, net_D, net_Q)
                #     final_arr.append(append_line)
                # if(len(net_Qn) > 0):
                #     append_line = "INVX1 ginv%d(.A(%s), .Y(%s));\n"%(flop_cnt, net_D, net_Qn)
                #     final_arr.append(append_line)
                

                #*Flop outputs are considered POs, next gates considered PIs
                
                ### Logic 1
                #Check if D is a preexisting input, if not add it as a new output
                #Check if Q / Qn is a preexisting output, if not add it as a new input
                
                ### Logic 2
                #Dont check for input or output, simply add a buffer after D and a buffer before Q. 
                #Declare the output of buffer D as Po, input of buffer Q as PI
                #Insert buffer after D and declare output of buffer as PO
                if(len(net_D) > 0):
                    append_line = "CLKBUFX1 gbuf_d_%d(.A(%s), .Y(d_out_%d));\n"%(flop_cnt, net_D, flop_cnt)
                    output_dict[i] = ["d_out_%d"%(flop_cnt)]
                    inout_list.append("d_out_%d"%(flop_cnt))
                    final_arr.append(append_line)
                    #Insert buff before Q/Qn and declare input of buffer as PI
                    if(len(net_Q) > 0):
                        append_line = "CLKBUFX1 gbuf_q_%d(.A(q_in_%d), .Y(%s));\n"%(flop_cnt, flop_cnt, net_Q)
                        input_dict[i] = ["q_in_%d"%(flop_cnt)]
                        inout_list.append("q_in_%d"%(flop_cnt))
                        final_arr.append(append_line)
                    if(len(net_Qn) > 0):
                        append_line = "CLKBUFX1 gbuf_qn_%d(.A(qn_in_%d), .Y(%s));\n"%(flop_cnt, flop_cnt, net_Qn)
                        input_dict[i] = ["qn_in_%d"%(flop_cnt)]
                        inout_list.append("qn_in_%d"%(flop_cnt))
                        final_arr.append(append_line)
        
        else:
            final_arr.append(line)
    #Reinsert module name and wire and input output
    #Reinsert wires
    for key in wire_dict.keys():
        wire_line = "wire "
        for wire in wire_dict[key]:
            wire_line = wire_line + wire + ", "
        wire_line = wire_line[:-2] + ";\n"
        final_arr.insert(0, wire_line)
    #Reinsert outputs
    for key in output_dict.keys():
        output_line = "output "
        for output in output_dict[key]:
            output_line = output_line + output + ", "
        output_line = output_line[:-2] + ";\n"
        final_arr.insert(0, output_line)
    #Reinsert inputs
    for key in input_dict.keys():
        input_line = "input "
        for input_ in input_dict[key]:
            input_line = input_line + input_ + ", "
        input_line = input_line[:-2] + ";\n"
        final_arr.insert(0, input_line)
    #Reinsert module
    module_line = "module %s("%(module_name)
    for net in inout_list:
        module_line = module_line + net +  ", "
    module_line = module_line[:-2] + ");\n"
    final_arr.insert(0, module_line)
    print("Netlist flop reorganization successful...") 
    return final_arr

def std_extractor(lin_arr):
    std_dict = {}
    print("\nIN EXTRACTOR\n")
    print(lin_arr[9])
    for line in lin_arr:
        line = line.strip()
        if(line.startswith("input") or line.startswith("output") or line.startswith("wire") or line.startswith("module") or line.startswith("endmodule")):
            print("Continue")
            continue
        else:
            cell_name = line.split()[0].strip()
            std_dict[cell_name] = line
    # print(std_dict.keys())
    for cell_name in std_dict.keys():
        print(cell_name)
    return

"""
Main Function
"""
cwd = os.getcwd()
#Read original Netlist
line_arr = []
file_reader(os.path.join(cwd, sys.argv[1]), line_arr)

#Process Netlist
write_arr = netlist_parser(line_arr)
file_writer(os.path.join(cwd, sys.argv[1][:-2]+"_proc.v"), write_arr)

std_extractor(write_arr)

# #Extract module definition
# module_name, inout_list = module_def(write_arr)

# #Extract input and output and wire arrays
# wire_dict, input_dict, output_dict = extract_inout_wire(write_arr)

# #Bypass flip flop
# comb_arr = flop_parser(write_arr, module_name, inout_list, wire_dict, input_dict, output_dict)
# file_writer(os.path.join(cwd, sys.argv[1][:-2]+"_comb_v2.v"), comb_arr)

