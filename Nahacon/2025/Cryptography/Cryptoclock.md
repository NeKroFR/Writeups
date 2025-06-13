# Cryptoclock

This challenge provide us the source code of a remote server which xor the flag with a key and gives us the encrypted flag, and then we can send it some input wich will be xored with the same key.

```py
#!/usr/bin/env python3
import socket
import threading
import time
import random
import os
from typing import Optional

def encrypt(data: bytes, key: bytes) -> bytes:
    """Encrypt data using XOR with the given key."""
    return bytes(a ^ b for a, b in zip(data, key))

def generate_key(length: int, seed: Optional[float] = None) -> bytes:
    """Generate a random key of given length using the provided seed."""
    if seed is not None:
        random.seed(int(seed))
    return bytes(random.randint(0, 255) for _ in range(length))

def handle_client(client_socket: socket.socket):
    """Handle individual client connections."""
    try:
        with open('flag.txt', 'rb') as f:
            flag = f.read().strip()
        
        current_time = int(time.time())
        key = generate_key(len(flag), current_time)
        
        encrypted_flag = encrypt(flag, key)
        
        welcome_msg = b"Welcome to Cryptoclock!\n"
        welcome_msg += b"The encrypted flag is: " + encrypted_flag.hex().encode() + b"\n"
        welcome_msg += b"Enter text to encrypt (or 'quit' to exit):\n"
        client_socket.send(welcome_msg)
        
        while True:
            data = client_socket.recv(1024).strip()
            if not data:
                break
                
            if data.lower() == b'quit':
                break
                
            key = generate_key(len(data), current_time)
            encrypted_data = encrypt(data, key)
            
            response = b"Encrypted: " + encrypted_data.hex().encode() + b"\n"
            client_socket.send(response)
            
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind(('0.0.0.0', 1337))
    server.listen(5)
    
    print("Server started on port 1337...")
    
    try:
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    main() 
```

Xor is reversible, because our input is xored with the same key as the flag we have:

```
ct = flag ^ key
know_ct = known ^ key
ct ^ know_ct = (flag ^ key) ^ (known ^ key)
             = flag ^ knwon
flag = (flag ^ known) ^ known
```

## solve.py

```py
from pwn import *

r = remote("challenge.nahamcon.com", 32581)

for l in r.recvuntil(b"Enter text to encrypt (or 'quit' to exit):\n").split(b"\n"):
    if b"The encrypted flag is:" in l:
        ct = bytes.fromhex(l.split(b": ")[1].strip().decode())
        break

known = b"A" * len(ct)
r.sendline(known)

known_ct = bytes.fromhex(r.recvuntil(b"\n").split(b": ")[1].strip().decode())
xor_res = bytes(a ^ b for a, b in zip(ct, known_ct))
flag = bytes(a ^ b for a, b in zip(xor_res, known))
print(flag.decode())
```
