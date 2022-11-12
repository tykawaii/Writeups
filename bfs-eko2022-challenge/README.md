# Introduction
On Oct 25 2022, I saw a post from Blue Frost Security team about some exploitation challenges. I am a fan of windows exploitation, so I decided to take a try on this challenge.

The goal of this challenge is to run "calc.exe" on Windows 10/11 and keeping process continue running. 

Link to the challenge is here: https://labs.bluefrostsecurity.de/blog.html/2022/10/25/bfs-ekoparty-2022-exploitation-challenges/.

[Sorry for my english if I have any mistakes 😅]

# Table of contents
[Static analysis](https://github.com/tykawaii98/Writeups/tree/master/bfs-eko2022-challenge#static-analysis)

[The bug](https://github.com/tykawaii98/Writeups/tree/master/bfs-eko2022-challenge#bug)

[Exploit](https://github.com/tykawaii98/Writeups/tree/master/bfs-eko2022-challenge#exploit)

- [Fixed shellcode](https://github.com/tykawaii98/Writeups/tree/master/bfs-eko2022-challenge#the-fixed-shellcode)
- [Abusing IRET](https://github.com/tykawaii98/Writeups/tree/master/bfs-eko2022-challenge#abusing-iret-instruction)
- [Finding right value for CS/SS](https://github.com/tykawaii98/Writeups/tree/master/bfs-eko2022-challenge#finding-the-right-value-for-cs-and-ss)
- [Mistake from me](https://github.com/tykawaii98/Writeups/tree/master/bfs-eko2022-challenge#big-mistake)
- [Execute 32-bit shellcode](https://github.com/tykawaii98/Writeups/tree/master/bfs-eko2022-challenge#execute-the-32-bit-shellcode)
- [Switch back to 64-bit mode](https://github.com/tykawaii98/Writeups/tree/master/bfs-eko2022-challenge#switch-back-to-64-bit-mode)
- [Proof-of-concepts](https://github.com/tykawaii98/Writeups/tree/master/bfs-eko2022-challenge#poc)

# Static analysis
Decompile exe with Hex-rays decompile, look at the **main** function:

- Allocate a heap space at address **0x10000000** with **RWX** permission and save this address to a global variable named "**buf**". 
This buffer will be used for receiving data from client later.

  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/allocate.JPG)

- Start a tcp server listen on port *31415*. 
- Recv maximum 4096 bytes from client and compare with "*Hello\x00*" string. If checking is passed, send string "*Hi\x00*" back to client and call to **handle_client** funcition (at *0x140001240*).

  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/pre_checking.JPG)

In the **handle_client** function:
- Init each 16-bytes of global "**buf**" variable with values: **0x50 0x50 0x50 0x50 0x50 0x50 0x50 0x50 0x58 0x58 0x58 0x58 0x58 0x58 0x58 0xCF**.

  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/fill_in_buf.JPG)

- recv a 11 bytes from client into a local bufffer.
- Using first 8-bytes received as **cookie** and compare with string "*Eko2022\x00*".
- The next byte is used as packet **type**, and should be valued *0x54*. Then, this value will be saved into a local buffer **saved_type** for later checking.
- The last 2-bytes is used as **packet_size**, and should be less than *0xf00*.
- If every checking is pass, the server recv data from client into global "**buf**" with maximum size is **packet_size**.
- Then, the received data is copied to a local buffer named **CmdLine** and replace the data with values *0x33/0x2b* with the value *0x00*.

  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/check_format.JPG)

- After that, the value in **saved_type** will be compare with *0x54*. If it is, the copied data will be send back to the client. 
- Otherwise, if **save_type**'s value is *0x58* (in general, this will never happen because there is a checking must be bypass before), server will jump and execute shellcode from the last received size in **buf** variable.

  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/check_type.JPG)

# Bug
- There is a **type-confusion** bug inside the **handle_client** function when checking the **packet_size** value. Two-bytes received is used as a **signed-int** number when compare with value *0xf00*, but in **recv** function later, this value is used as an **unsigned-int** number.

  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/used_as_signed.JPG)
  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/used_as_unsigned.JPG)
  
- If we send the **packet_size** value is **0x8000 or over**, we can bypass this checking and send more bytes than server expected. 
- Using this bug, we can overflow the **save_type** with the value *0x58* and bypass checking for shellcode execution, with help of copy function below.

# Exploit
## The fixed shellcode
- In the fixed shellcode, we have 8 "**push rax**" instructions folowing by 7 "**pop rax**" instructions and a "**iret**" instruction in the last of shellcode.
- Fortunately, with 7 "**pop rax**" instruction, we can reach the "**iret**" with stack pointer poiting to our controlled data.
- To archive code execution, we have to setup a right stack frame for **iret** execute properly.

## Abusing **IRET** instruction
- Follow this [artical](http://jamesmolloy.co.uk/tutorial_html/10.-User%20Mode.html), I try to setup stack look like: [Instruction Pointer] > [Code Segment] > [FLAGS] > [Stack Pointer] > [Stack Segment]. 
- Because the global **buf** variable alway allocated at address *0x10000000* with **RWX** permission, so I have no difficult to find values for IP and SP.
- For FLAGS value, I use the value *0x200* (which is 1 << 9), meaning **Interupt enable flag** is set. Read more [here](https://mudongliang.github.io/x86/html/file_module_x86_id_145.html) and [here](https://en.wikipedia.org/wiki/FLAGS_register).
- The big question here is what are the "right" value for CS and SS.

## Finding the "right" value for CS and SS
- Because the copy function replaced 0x33 and 0x2b with the value 0x00, so we need to find another values.
- To find the value for code segment, I choose value 0x23 (which is value for CS in 32-bit mode).
- At this time, I don't know what is the "right" value for SS, so I choose some random value and it not work. I was stuck here for a long time...
- Thanks to the help of [dhn](https://twitter.com/dhn_), he said that I can use **dg** command in WinDBG to find which segment selector have type is "**Data RW**" and use it for SS segment. 

  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/dhn_help.JPG)
  
- I found some candidate values are *0x28, 0x29, 0x2a, 0x2b, 0x50, 0x51, 0x52, 0x53*.
- Finally, I found the correct value is *0x53* (which is also the value for FS).
## Big mistake
- I try to set SS value with every candidate value and execute with IRET, but I still got exception "Access violation".
- After reading carefully some documents, I realise that when I use value *0x23* for CS, my CPU got switched into 32-bit mode, so I have to use 32-bit address instead of 64-bit address. 
- What a BIG MISTAKE from me :(.

  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/failed_stack.jpg)
  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/exception.jpg)
  
## Execute the 32-bit shellcode
- After IRET execute successfully, CPU switched to 32-bit mode and I try to execute 32-bit shellcode generated from msfvenom, but still got crash.

  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/sc32_fail.JPG)

## Switch back to 64-bit mode
- I decided to switch back to 64-bit CPU to avoid some unexpected errors.
- To to this, I use **IRET** instruction again with a correct stack frame.
- Currently, SS is set to 0x53, so to make stack usage, I add some code to restore value *0x2b* for SS. And lucky me again, at this time, ECX register still holding address of the old stack. So I can get the right value for RSP after switch back.
- With restored SS, I can push value to stack and execute IRET instruction properly.
- After switch back to 64-bit mode, I can archive code execution with shellcode get from [here](https://www.exploit-db.com/shellcodes/49819) and adding some instruction to make server keep execution.

## POC
- Full exploit can be found [here](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/sol.py).

  ![](https://github.com/tykawaii98/Writeups/blob/master/bfs-eko2022-challenge/images/poc.JPG)
