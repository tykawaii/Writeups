# Warmup - Pwn - 29 solves

## Reversing

File PE khá đơn giản, tại hàm main sẽ gọi tới 1 hàm func, sau đó sẽ đọc input vào biến Buffer bằng hàm ReadFile.

```
int __cdecl main(int argc, const char **argv, const char **envp)
{
  char Buffer; // [esp+0h] [ebp-44h]

  j_init();
  j_printf(aWelcomeBanner, Buffer);
  j_func();
  j_printf(aDidYouMakeSome, Buffer);
  ReadFile(hStdin, &Buffer, 0x60u, 0, 0);
  return 0;
}
```

Bên trong hàm func thực hiện đọc input từ người dùng, sau đó in ra input đã nhập:

```
  v0 = GetProcessHeap();
  hHeap = (char)v0;
  lpBuffer = HeapAlloc(v0, 8u, 0x150u);
  j_printf(&v6, hHeap);
  ReadFile(hStdin, lpBuffer, 0x150u, 0, 0);
  j_printf(lpBuffer, v3);
  j_printf(&unk_463018, v4);
  return 0;
```

## Bugs

Ở đây, có 2 bug khá rõ ràng:

Một là bug formatstring bên trong hàm func:

```
  ReadFile(hStdin, lpBuffer, 0x150u, 0, 0);
  j_printf(lpBuffer, v3);
```

Bug còn lại là buffer overflow bên trong hàm main. Sau khi gọi hàm func, chương trình sử dụng ReadFile để đọc tối đa 0x150 ký tự vào biến Buffer (chứa tối đa 0x44 ký tự)(thông tin hàm ReadFile có thể xem tại [đây](https://docs.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile)):

```
  char Buffer; // [esp+0h] [ebp-44h]
  ...
  ReadFile(hStdin, &Buffer, 0x60u, 0, 0);
```

## Exploitation

Chương trình cung cấp sẵn một hàm có nhiệm vụ đọc flag nằm ở offset 0x406c80 (hoặc có thể sử dụng lệnh jump tới hàm này ở offset 0x4023bf)

Chương trình sử dụng stack canary để bảo vệ stack overflow, tuy nhiên có thể sử dụng formatstring để leak giá trị canary. Đồng thời leak địa chỉ hàm main để tính địa chỉ của hàm catFlag

***Debug***

Để xác định được địa chỉ cần tìm nằm đâu trong stack, đặt breakpoint tại câu lệnh
```
.text:00406D0D                 mov     [ebp+var_4], eax
```
Thực thi chương trình, dừng tại bp, thấy giá trị ebp lúc này là 0x00AFFA6C -> ebp + var_4 = 0x00AFFA6C - 4 = 0x00AFFA68. Bấm F8 thực thi câu lệnh để kiểm chứng:

![](https://github.com/tykawaii/CTF/blob/master/Writeups/InCTF%202019/images/Capture.PNG)

Như vậy, stack canary của hàm main sẽ lưu tại địa chỉ 0xAFFA68

Tiếp tục trace đến lệnh gây ra lỗi formatstring bên trong hàm func
```
.text:00DA6BE4 call    j__printf
```

Kiểm tra trong stack, lúc này ta có thể xác định được vị trí các địa chỉ cần thiết:

![](https://github.com/tykawaii/CTF/blob/master/Writeups/InCTF%202019/images/stack0.PNG)

Ta thấy tại địa chỉ 0x00AFFA24 chứa địa chỉ của main+27 -> Có thể leak hàm này để tính địa chỉ của catFlag

Tính thứ tự in ra trong stack như sau: (0xAFFA24 - 0xAFF9F0) / 4 = 13 => địa chỉ main+27 nằm ở index 12 trong mảng in ra (sử dụng nhiều format %p để in ra 1 mảng các giá trị bên trong stack)

Tương tự, tính index của stack canary của main như sau: (0xAFFA68 - 0xAFF9F0) / 4 = 30 => stack canany nằm tại index 29

Như vậy, đã đầy đủ các giá trị cần thiết, thực hiện xây dựng payload để tận dụng buffer overflow và gọi hàm catFlag (mã nguồn khai thác ở [đây](https://github.com/tykawaii/CTF/blob/master/Writeups/InCTF%202019/pwn1.py))

***Go go get flag :v***

![](https://github.com/tykawaii/CTF/blob/master/Writeups/InCTF%202019/images/Capture1.PNG)




