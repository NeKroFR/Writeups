# FlagsFlagsFlags (the lazy way)

This challenge provides an ELF binary:
```sh
❯ file flagsflagsflags
flagsflagsflags: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, no section header
```

Opening it in IDA, it seems to be packed. Looking at the strings shows it was packed using UPX:

```sh
❯ strings flagsflagsflags | grep upx
$Info: This file is packed with the UPX executable packer http://upx.sf.net $
```

Let's unpack it:

```sh
❯ upx -d flagsflagsflags -o flagsflagsflags.upxed
                       Ultimate Packer for eXecutables
                          Copyright (C) 1996 - 2024
UPX 4.2.2       Markus Oberhumer, Laszlo Molnar & John Reiser    Jan 3rd 2024

        File size         Ratio      Format      Name
   --------------------   ------   -----------   -----------
   6918175 <-   3387920   48.97%   linux/amd64   flagsflagsflags.upxed

Unpacked 1 file.
```

On IDA we can see that the flag generations involve playing with the index from an offset:

![alt text](https://i.imgur.com/jZsJiRd_d.webp?maxwidth=760&fidelity=grand)

Let's look at what is stored in this offset:

```S
.rodata:000000000088D028 off_88D028      dq offset aFlag55dd8a6035
.rodata:000000000088D028                                         ; DATA XREF: main_generateFlag+2C↑o
.rodata:000000000088D028                                         ; "flag{55dd8a603527dde588b261ee2dda1c9c}"
.rodata:000000000088D030                 db '&',0
.rodata:000000000088D032                 align 8
.rodata:000000000088D038                 dq offset aFlag602200d19e ; "flag{602200d19ec0a3a60a7011a71dfcee60}"
.rodata:000000000088D040                 db '&',0
.rodata:000000000088D042                 align 8
.rodata:000000000088D048                 dq offset aFlag102bce7892 ; "flag{102bce789210611558b8b7e22938f193}"
.rodata:000000000088D050                 db '&',0
.rodata:000000000088D052                 align 8
.rodata:000000000088D058                 dq offset aFlag2abae0fd41 ; "flag{2abae0fd4157a3c703de893c198edbe9}"
.rodata:000000000088D060                 db '&',0
.rodata:000000000088D062                 align 8
.rodata:000000000088D068                 dq offset aFlag40ad960517 ; "flag{40ad960517440be0e9d9485425a196a6}"
.rodata:000000000088D070                 db '&',0
.rodata:000000000088D072                 align 8
...
.rodata:00000000009E57A0                 db '&',0
.rodata:00000000009E57A2                 align 8
.rodata:00000000009E57A8                 dq offset aFlagA1a740f594 ; "flag{a1a740f594e37402b1101ced2d5d67c2}"
.rodata:00000000009E57B0                 db '&',0
.rodata:00000000009E57B2                 align 8
```

We can see that there is a lot of different flag possible (1410954), but I was to lazy to reverse. So I just bruteforced the flag 🤡

First let's dump the possible flags:

```
❯ strings flagsflagsflags.upxed | grep flag{ > strings.txt
```

And now we can just try each flag.

## solve.py

```py
import re
from pwn import *
from multiprocessing import Pool

def test_flag(flag):
    p = process('./flagsflagsflags.upxed')
    p.sendline(flag)
    output = p.recvall().decode()
    p.close()

    if "Incorrect" not in output:
        with open('flag.txt', 'w') as f:
            f.write(flag)
        return flag
    return None

if __name__ == "__main__":
    with open('strings.txt', 'r') as file:
        content = file.read()
        flags = re.findall(r'flag\{.*?\}', content)
    
    with Pool() as pool:
        results = pool.map(test_flag, flags)
    
    for result in results:
        if result:
            print(f"Correct 
Écrivez ou collez votre texte ici￼
First let's dump the possible flags:
￼
flag: {result}")
            break
    else:
        print("No correct flag found among the extracted flags.")
```

After a few minutes, the flag was written in the flag.txt file.
