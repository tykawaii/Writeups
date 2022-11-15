# Introduction

Goal of this challenge is pop cacl.exe on Windows 10/11 and process keep continue running.

Link challenge: https://labs.bluefrostsecurity.de/blog.html/2022/03/01/bfs-hiring-challenge/

# Static analysis

- Server starting listening on port 12321.
- For every connection, receive 8-bytes from client for checking.
- Check if first 4-bytes is "BFS." and last 4-bytes in double-word is less than 0x100.
- When checking is passed, server will receive data from client, copy into a global buffer and send back to client.
- The server also setup a array for saving return-address each time a fuction is called. This used for prevent overwriting return address on the stack with buffer-overflow. The array is at address **bfsc+0xE5B8**, and a 1-byte at **bfsc+0xE5b4** is used for "index" of current return-address in the array. 

# Bug

Inside the sending and receiving function (**sub_140001380**), server get last 4-bytes from previous 8-bytes received data and add with the last 4-bytes in local buffer (which is on the stack). Then, the result will be used as the size for "recv" and "send" later.

Because the stack frame is re-used for every connection, the last 4-bytes is controlled by client. If we send data long enough (greater than 252 bytes),
we can control the size for "recv" and "send" funtions.

# Exploit strategy

1. Send data with size over 252 bytes (should be < 0x100) to set data in stack.
2. With last 4-bytes in step 1, I can control size for "send" function. So that I can leak data from return-address array, and also the address of WinExec funtion below.
3. Because data is copy from local buffer to global "Buffer" with "sprintf" function, I cannot use data contains "\x00". So I cut the writing process into 3 pieces:
  - First, overwrite return address pointer at index 1 with address I want to execute (which is the first gadget of my ropchains).
  - Second, put the string "calc.exe\x00" in index 0 of return-address array.
  - Lastly, overwrite "index" value to 1 to trigger the first gadget. Because, there is also have a buffer overflow inside function, so I can control everything in the stack for setup my ropchains.
4. After poping "calc.exe" with ropchain, to keep process continue running, I jump back to address **bfsc+0x1597** (which is inside the loop). 
Lucky me, the stack after jump back is the same with stack frame with the stack before. There are some several variables was overwritten, but the important one is the server socket keeping unchanged.

# Proof of concepts

![](https://github.com/tykawaii98/Writeups/blob/master/BFS-hiring-challenge-2022/poc.JPG)

Full exploit can be found [here](https://github.com/tykawaii98/Writeups/blob/master/BFS-hiring-challenge-2022/sol.py)

# Thanks for reading :D
