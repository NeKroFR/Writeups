# RPS

This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/293) asks us to defeat a computer 5 times in a row on a paper rock paper sisors.


Let's look how the code determine if we win:
```c
if (strstr(player_turn, loses[computer_turn])) {
  puts("You win! Play again?");
  return true;
} else {
  puts("Seems like you didn't win this time. Play again?");
  return false;
}
```

We can see that it looks if our input contain the element of the loses array that defeat the computer choice we win. We can then just send a string containing all the possible answer so we are sure to win:

# Solve.py

```py
from pwn import *

r = remote('saturn.picoctf.net', 61023)

r.recvuntil(b"Type '2' to exit the program")

for i in range(5):
    r.sendline(b'1')
    r.recvuntil(b'Please make your selection (rock/paper/scissors):')
    r.sendline(b'rockpaperscissors')
    r.recvuntil(b'You win! Play again?')
r.interactive()
```