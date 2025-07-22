# Shaker

The challenge implements a custom `Shaker` class that performs XOR and permutation operations on a 64-byte flag. We can interact with it through a menu system that allows us to shake the data and see the result.

Looking at the `shaker.py` code we have:

```py
import random
import hashlib 

class Shaker:

    def __init__(self, state):
        self.state = state
        self.x = random.randbytes(64)
        self.p = [i for i in range(64)]
        random.shuffle(self.p)
        
    def permute(self):
        self.state = [self.state[_] for _ in self.p]

    def xor(self):
        self.state = [a^b for a,b in zip(self.state, self.x)]

    def shake(self):
        self.xor()
        self.permute()

    def reset(self):
        random.shuffle(self.p)
        self.shake()
        
    def open(self):
        self.xor()
        return self.state
        
with open("flag.txt", "r") as f:
    flag = f.read().encode()

assert(len(flag) == 64)
assert(hashlib.md5(flag).hexdigest() == "4839d730994228d53f64f0dca6488f8d")
s = Shaker(flag)

ct = 0
MAX_SHAKES = 200
MENU = """Choose an option:
1. Shake the shaker
2. See inside
3. Exit
> """

while True:
    choice = input(MENU)
    if choice == '1':
        if (ct >= MAX_SHAKES):
            print("The shaker broke...")
            exit(0)
        s.shake()
        ct += 1
        print(f"You have shaken {ct} times.") 
        
    if choice == '2':
        ret = s.open()
        s.reset()
        print(f"Result: {bytes(ret).hex()}")
        
    if choice == '3':
        exit(0)
```

The key insight is that the `open()` function only applies XOR without permutation, while `shake()` applies both XOR and permutation.
When we call option 2, it willl call `open()` followed by `reset()`.

The vulnerability is based on timing the operations correctly. After testing different combinations, I realized that shaking exactly 119 times followed by opening can create a recoverable state. 

## solve.py

```py
from pwn import *
import hashlib 

# context.log_level = 'debug'

while True:
    r = remote("challs.nusgreyhats.org", 33302)
    r.sendline(b"2")
    r.readuntil(b"Result: ")
    T = 120
    for i in range(T-1):  # Shake 119 times
        r.sendline(b"1")

    r.sendline(b"2")  # See inside
    r.readuntil(b"Result: ")
    R = r.readline().decode()
    R = bytes.fromhex(R)
    if hashlib.md5(R).hexdigest() == "4839d730994228d53f64f0dca6488f8d":
        print(R)
        exit()
```
