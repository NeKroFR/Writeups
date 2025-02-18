# Extremely Convenient Breaker

In this challenge, we are presented with an AES encryption system running in ECB mode. The service generates a random AES key and encrypts a 64-byte flag. It then prints the encrypted flag (in hex) and provides a decryption oracle that will decrypt any 64-byte ciphertext we send, but our input must be different to the ciphertext:

```py
#!/usr/local/bin/python3

from Crypto.Cipher import AES
import os

key = os.urandom(16)
with open("flag.txt", "r") as f:
    flag = f.readline().strip()
cipher = AES.new(key, AES.MODE_ECB)

flag_enc = cipher.encrypt(flag.encode())
print("Here's the encrypted flag in hex: ")
print(flag_enc.hex())
print("Alright, lemme spin up my Extremely Convenient Breaker (trademark copyright all rights reserved). ")

while True:
    ecb = input("What ciphertext do you want me to break in an extremely convenient manner? Enter as hex: ")
    try:
        ecb = bytes.fromhex(ecb)
        if not len(ecb) == 64:
            print("Sorry, it's not *that* convenient. Make your ciphertext 64 bytes please. ")
        elif ecb == flag_enc:
            print("No, I'm not decrypting the flag. ")
        else:
            print(cipher.decrypt(ecb))
    except Exception:
        print("Uh something went wrong, please try again. ")
```

In ECB mode, each 16-byte block is processed independently, the flag is 64 bytes long, so we will deal with 4 blocks.
Because of we have the flag ciphertext we can simply send each ciphertext block as the first block in our query so that its corresponding decrypted output gives us the plaintext for that block.

## solve.py

```py
from pwn import *
from ast import literal_eval

r = remote("chall.lac.tf", 31180)

r.recvuntil(b"Here's the encrypted flag in hex:")
ct = r.recvline().strip()

while not ct:
    ct = r.recvline().strip()

ct = ct.decode()
ciphertext = bytes.fromhex(ct)
    
flag = b""

for i in range(4):
    r.recvuntil(b"Enter as hex: ")
    block = ciphertext[i*16:(i+1)*16]
    query = block + b'0'*16*3
    r.sendline(query.hex().encode())

    res = r.recvline().strip()
    decrypted = literal_eval(res.decode())
    decrypted_block = decrypted[:16]
    flag += decrypted_block

print(flag)
```
