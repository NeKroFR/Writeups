# Confusion

When connecting to the service using `nc confusion.challs.srdnlen.it 1338`, we're presented with a flag in hex format and prompted to encrypt our own input:

```
❯ nc confusion.challs.srdnlen.it 1338
Let's try to make it confusing
|
|    flag = bd87976b9a27fa2fde16aeee931169f910eeae5acef93814c21526e3bb2c6d0ccad4660a736095c9f827a8dbd99be5f940b48021012d0d55d4910c15309ad190c8ac63784e9c318e2ba808d3091cc8dd
|
|  ~ Want to encrypt something?
|
|    > (hex)
```

The service allowed us to submit plaintext data and returned the corresponding encrypted output.
We can then bruteforce every char because of: `C1 ⊕ C2 = (P1 ⊕ K) ⊕ (P2 ⊕ K) = P1 ⊕ P2` so if `P1 = P2` then `C1 ⊕ C2 = 0`

# solve.py

```py
import string
from pwn import *
from textwrap import wrap

flag = 'srdnlen{'
alphabet = string.ascii_letters + string.punctuation + string.digits

r = remote('confusion.challs.srdnlen.it', 1338)

while True:
    pad_len = 95 - len(flag)

    r.recvuntil(b"> (hex) ")
    r.sendline(("a" * pad_len).encode().hex().encode())
    r.recvuntil(b" Here is your encryption:\n|\n|   ")
    ref_block = [bytes.fromhex(block) for block in wrap(r.recvline().decode().strip(), 32)][6]

    for c in alphabet:
        test_input = ("a" * pad_len + flag + c).encode()
        
        r.recvuntil(b"> (hex) ")
        r.sendline(test_input.hex().encode())
        r.recvuntil(b" Here is your encryption:\n|\n|   ")
        test_block = [bytes.fromhex(block) for block in wrap(r.recvline().decode().strip(), 32)][6]

        if bytes(a ^ b for a, b in zip(ref_block, test_block)) == b"\x00" * len(ref_block):
            flag += c
            print(f"{flag = }")

            if c == "}":
                r.close()
                exit()
            break
```
