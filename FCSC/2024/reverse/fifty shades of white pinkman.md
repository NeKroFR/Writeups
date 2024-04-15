Fifty Shades of White (Pinkman) - 219

Looking at the chall we can see that it is the same binary as [Fifty Shades of White (Junior)](/FCSC/2024/intro/fifty%20shades%20of%20white%20junior.md). We just need to make a keygen. To do so, we will take our previous script to generate admin licenses.

```py
import hashlib
import uuid
import base64
from pwn import *
from concurrent.futures import ThreadPoolExecutor

def validate(name, serial):
    hashed_serial = hashlib.sha256(serial.encode()).digest()
    for i in range(3):
        sum_of_chars = sum(ord(name[j]) for j in range(i, len(name), 3))
        hashed_byte_value = (sum_of_chars * 0x13 + 0x37) % 0x7f
        checksum = (hashed_serial[i] * 0x37 + 0x13) % 0x7f
        if hashed_byte_value != checksum:
            return False
    return True

def get_serial(name, stop_event):
    while not stop_event.is_set():
        serial = str(uuid.uuid4())
        if validate(name, serial):
            stop_event.set()
            return serial
    return None



def make_license(name, serial):
    license = "----BEGIN WHITE LICENSE----"
    content = f"Name: {name}\nSerial: {serial}\nType: 1337\n"
    license += base64.b64encode(content.encode('utf-8')).decode('utf-8')
    l = len("----BEGIN WHITE LICENSE----")
    i = l
    while i < len(license)-l:
        license = license[:i] + '\n' + license[i:]
        i += l
    license += "\n-----END WHITE LICENSE-----\n"
    return license


sock = remote("challengesock.france-cybersecurity-challenge.fr",2250)

sock.recvline()
sock.recvline()
sock.sendline(make_license("Walter White Junior", "96d2e476-54fe-46f1-b4f8-7ff6e6541f1d").encode())
sock.recvline()
sock.recvline()
sock.recvline()


for i in range(2, 51):
    name = sock.recvline()[len(b'[*] Give me a valid license for username: '):-1].decode()
    print(i, "making license for", name)
    stop_event = threading.Event()
    with ThreadPoolExecutor(max_workers=12) as executor:
        serial = executor.submit(get_serial, name, stop_event).result()
    license = make_license(name, serial)
    sock.sendline(license.encode())
    for i in range(3):
        sock.recvline()
for i in range(2):
    print(sock.recvline())
```