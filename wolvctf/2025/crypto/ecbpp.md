# ECB++

This challenge provides us this script:

```py
#!/usr/local/bin/python3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import random

f = open('./flag.txt','r')
flag = f.read()

def encrypt(message):
    global flag
    message = message.encode()
    message += flag.encode()
    key = random.getrandbits(256)
    key = key.to_bytes(32,'little')
    cipher = AES.new(key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(message, AES.block_size))
    return(ciphertext.hex())

print("Welcome to my secure encryption machine!")
print("I'll encrypt all your messages (and add a little surprise at the end)")

while(True):
    print("Do you have a message to encrypt? [Y|N]")
    response = input()
    if(response == 'Y'):
        print("Gimme your message:")
        message = input()
        print("Your message is: ",encrypt(message))
    else:
        exit(0)
```

It is a basic AES-ECB encryption scheme where the server encrypts our input concatenated with the flag using AES-ECB with a random key each time. ECB mode encrypts identical 16-byte blocks to the same ciphertext. 

Knowing that the flag starts with `wctf{`. We can leak the flag byte-by-byte by crafting messages and comparing ciphertext blocks.

## solve.py

```py
from pwn import *
import string

alphabet = string.ascii_letters + string.punctuation + string.digits  # 94 characters
block_size = 16
flag = b"wctf{"

r = remote("ecbpp.kctf-453514-codelab.kctf.cloud", 1337)

while b"}" not in flag:
    k = len(flag)
    within_block = k % block_size
    pad_len = 15 - within_block
    known_prefix = flag[max(0, k - 15):k]

    guesses = []
    for c in alphabet:
        guess = b"a" * (15 - len(known_prefix)) + known_prefix + c.encode()
        guesses.append(guess[:16])

    message = b"".join(guesses) + b"a" * pad_len

    r.recvuntil(b'[Y|N]')
    r.sendline(b'Y')
    r.recvuntil(b'message:')
    r.sendline(message)
    r.recvuntil(b'Your message is: ')
    res = r.recvline().decode().strip()
    ct = bytes.fromhex(res)

    target_block_index = (len(message) + k) // block_size
    target_block = ct[target_block_index * block_size:(target_block_index + 1) * block_size]

    for i in range(len(alphabet)):
        guess_block = ct[i * block_size:(i + 1) * block_size]
        if guess_block == target_block:
            flag += alphabet[i].encode()
            print(f"Flag so far: {flag.decode()}")
            break
    else:
        print("No match found, stopping")
        print(f"Debug: k={k}, len(message)={len(message)}, target_block_index={target_block_index}")
        break
```
