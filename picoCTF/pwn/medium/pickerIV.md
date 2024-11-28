# Picker IV


In this challenge from [picoCTF](https://play.picoctf.org/practice/challenge/403), we need to retrieve the adress of the win function.

Once we connect to the remote, we are asked to enter an adress to jump to:
```
❯ nc saturn.picoctf.net 61744
Enter the address in hex to jump to, excluding '0x': 0123
You input 0x0123
Segfault triggered! Exiting.
```

We can easilly retrieve the `win` function adress using objdump:

```
❯ objdump -D picker-IV | grep win
000000000040129e <win>:
  4012d2:       75 16                   jne    4012ea <win+0x4c>
  4012f9:       eb 1a                   jmp    401315 <win+0x77>
  401319:       75 e0                   jne    4012fb <win+0x5d>
```
And now, we can just send this adress to get the flag:

```
❯ nc saturn.picoctf.net 61744
Enter the address in hex to jump to, excluding '0x': 000000000040129e
You input 0x40129e
You won!
picoCTF{n3v3r_jump_t0_u53r_5uppl13d_4ddr35535_01672a61}
```