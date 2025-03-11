# Very Serious Cryptography

The challenge allows us connect to a remote server running this code:

```py
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import os

with open("flag.txt", "rb") as f:
    flag = f.read()

key = os.urandom(16)

# Efficient service for pre-generating personal, romantic, deeply heartfelt white day gifts for all the people who sent you valentines gifts
for _ in range(1024):

    # Which special someone should we prepare a truly meaningful gift for? 
    recipient = input("Recipient name: ")

    # whats more romantic than the abstract notion of a securely encrypted flag?
    romantic_message = f'Dear {recipient}, as a token of the depth of my feelings, I gift to you that which is most precious to me. A {flag}'
    
    aes = AES.new(key, AES.MODE_CBC, iv=b'preprocessedlove')

    print(f'heres a thoughtful and unique gift for {recipient}: {aes.decrypt(pad(romantic_message.encode(), AES.block_size)).hex()}')
```

The most striking thing is that the server does not encrypt the `romantic_message` but it uses `aes.decrypt()`.
The issue is that the same input will always produce the same "decrypted" output. Thanks to this, we can control part of the input and perform a [Byte at a Time Attack](https://github.com/ashutosh1206/Crypton/blob/master/Block-Cipher/Attack-CBC-Byte-at-a-Time/README.md) to retrieve the flag.

The message is like this: `Dear {recipient}, as a token of the depth of my feelings, I gift to you that which is most precious to me. A {flag}`. Our input is stored in the recipent and we don't have input lenght restriction. We can then just bruteforce the flag and look for matching outputs.

## solve.py

```py
from pwn import *

context.log_level = "error"

alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'{}_"

pref = "Dear "
mid = ", as a token of the depth of my feelings, I gift to you that which is most precious to me. A "
flag = ""

r = remote("very-serious.chal-kalmarc.tf", 2257)
while not '}' in flag:
    try:
        payload = "_" * ((15 - len(pref + mid + flag)) % 16)
        r.send((payload + "\n").encode())

        res = bytes.fromhex(r.recvline().decode().split()[-1])
        r.send(b"".join([(payload + mid + flag + c + "\n").encode() for c in alphabet]))
        n = len(pref + payload + mid + flag) + 1
        flag += {b[:n]: c for b, c in zip([bytes.fromhex(r.recvline().decode().split()[-1]) for _ in alphabet], alphabet)}[res[:n]]
        print(flag)
    except:
        r = remote("very-serious.chal-kalmarc.tf", 2257)
```
