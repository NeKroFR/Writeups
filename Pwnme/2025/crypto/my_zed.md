# My zed

This challenge presents a custom encryption scheme named `"OpenZED"` (wich is a hybrid AES implementation of CBC and CFB modes) that is used to encrypt a flag. The challenge provides the encrypted flag file (`flag.txt.ozed`) and the source code of the encryption library.

**challenge.py:**
```py
from openzedlib import openzed
import os
import zlib

from flag import FLAG


file = openzed.Openzed(b'zed', os.urandom(16), 'flag.txt', len(FLAG))

file.encrypt(FLAG)

file.generate_container()

with open(f"{file.filename}.ozed", "wb") as f:
	f.write(file.secure_container)
```


<details>
<summary>openzedlib source code:</summary>
<b>openzed.py:</b>

```py
from openzedlib.aes_cbc_zed import AES_CBC_ZED 
from hashlib import sha256

import json
import zlib


class Openzed:

	def __init__(self, user=b"user", password=b"OpenZEDdefaultpasswordtochangebeforedeployinproduction", filename="file", size=0):
		self.user = user
		self.password = password
		self.filename = filename
		self.size = size
		self.generate_metadata()

	"""Metadata 
	format : {"size": 0, "filename": "", "user": "", "password_hash": ""}+padding

	(size = 300 bytes and formatted in json)
	
	header ("OZED") -> 4
	size -> 4
	filename -> 112
	user -> 32
	password_hash -> 64
	json size -> 60
	"""

	def generate_metadata(self):
		
		metadata = {}
		metadata["user"] = self.user.decode()
		metadata["password_hash"] = sha256(self.password).hexdigest()
		metadata["filename"] = self.filename
		metadata["size"] = self.size

		self.metadata = json.dumps(metadata).encode()

		self.padding_len = 300-len(self.metadata)
		self.metadata += self.padding_len*b"\x00"
		
		return self.metadata
	
	def encrypt(self, data):
	
		cipher = AES_CBC_ZED(self.user, self.password)
		self.encrypted = cipher.encrypt(data)
		self.encrypted = zlib.compress(self.encrypted) # just for the lore
		
		return self.encrypted

	def decrypt(self, ciphertext):

		cipher = AES_CBC_ZED(self.user, self.password)
		ciphertext = zlib.decompress(ciphertext)
		self.decrypted = cipher.decrypt(ciphertext)
		
		return self.decrypted

	def generate_container(self):
		self.secure_container = b'OZED' + self.metadata + self.encrypted
		return self.secure_container

	def decrypt_container(self, container):

		self.read_metadata()
		filename = self.parsed_metadata["filename"]
		
		ciphertext = container[304:]

		plaintext = self.decrypt(ciphertext)
		return {"data":plaintext, "filename":filename}

	def read_metadata(self):
		self.parsed_metadata = json.loads(self.secure_container[4:300-self.padding_len+4])
		return self.parsed_metadata	
```

<b>aes_cbc_zed.py:</b>

```py

from Crypto.Cipher import AES
from hashlib import sha256

import os

def xor(a: bytes, b: bytes) -> bytes:
	return bytes(x^y for x,y in zip(a,b))

class AES_CBC_ZED:
	def __init__(self, user, password):
		self.user = user
		self.password = password
		self.derive_password()
		self.generate_iv()

	def encrypt(self, plaintext: bytes):
		iv = self.iv
		ciphertext = b""
		ecb_cipher = AES.new(key=self.key, mode=AES.MODE_ECB)
		
		
		for pos in range(0, len(plaintext), 16):
			chunk = plaintext[pos:pos+16]
			
			# AES CFB for the last block or if there is only one block
			if len(plaintext[pos+16:pos+32]) == 0 :
				#if plaintext length <= 16, iv = self.iv
				if len(plaintext) <= 16 :
					prev=iv
				# else, iv = previous ciphertext
				else:
					prev=ciphertext[pos-16:pos]
					
				prev = ecb_cipher.encrypt(prev)
				ciphertext += xor(chunk, prev)
			
			# AES CBC for the n-1 firsts block
			elif not ciphertext:
				xored = bytes(xor(plaintext, iv))
				ciphertext += ecb_cipher.encrypt(xored)
				
			else:
				xored = bytes(xor(chunk, ciphertext[pos-16:pos]))
				ciphertext += ecb_cipher.encrypt(xored)

		return iv + ciphertext


	def decrypt(self, ciphertext: bytes):
		# TODO prendre un iv déjà connu en paramètre ?
		plaintext = b""
		ecb_cipher = AES.new(key=self.key, mode=AES.MODE_ECB)
		iv = ciphertext[:16]
		ciphertext = ciphertext[16:]
		
		for pos in range(0, len(ciphertext), 16):
			chunk = ciphertext[pos:pos+16]
			
			# AES CFB for the last block or if there is only one block
			if len(ciphertext[pos+16:pos+32]) == 0 :
				
				#if plaintext length <= 16, iv = self.iv
				if len(ciphertext) <= 16 :
					prev=iv
				# else, iv = previous ciphertext
				else:
					prev=ciphertext[pos-16:pos]

				prev = ecb_cipher.encrypt(prev)
				plaintext += xor(prev, chunk)
				
			# AES CBC for the n-1 firsts block
			elif not plaintext:
				xored = ecb_cipher.decrypt(chunk)
				plaintext += bytes(xor(xored, iv))
				
			else:
				xored = ecb_cipher.decrypt(chunk)
				plaintext += bytes(xor(xored, ciphertext[pos-16:pos]))
				
		return plaintext
			
	
	def derive_password(self):
		for i in range(100):
			self.key = sha256(self.password).digest()[:16]

	def generate_iv(self):
		self.iv = (self.user+self.password)[:16]
```
</details>


Looking at the source code, we can see that the OpenZED container format consists of 3 parts:
1. A 4 bytes header: `"OZED"`
2. Metadata stored as a 300-byte JSON (with padding) containing:
   - User name
   - Password hash (SHA-256)
   - Filename
   - File size
3. The encrypted data (compressed with zlib)


Looking at the encryption process, we can see that blocks are encrypted using AES-CBC, except for the last (or single) block which uses AES-CFB mode.
The key is derived from the password using sha256 (100 iterations), and the IV is generated as `(user + password)[:16]`.

Fortunately, we know the username is **zed**. This, combined with the weak key derivation (only 100 SHA256 iterations) and the known username being part of the IV, makes brute-forcing the password a viable attack. We can try to brute-force the password, likely starting with short and simple passwords or variations related to "zed", "password", and "openzed".  To verify a correct password, we can attempt to decrypt `flag.txt.ozed` and check if it contains the first bytes of the flag: `PWNME{`.



## Exploitation

Here is the exploitation process:

### Step 1: Extract Metadata and IV

```python
with open("flag.txt.ozed", "rb") as f:
    container = f.read()

# Extract metadata (bytes 4-304)
metadata_bytes = container[4:304]
metadata_str = metadata_bytes.rstrip(b"\x00").decode()
metadata = json.loads(metadata_str)

print("User:", metadata["user"])
print("Password hash:", metadata["password_hash"])
```

### Step 2: Extract and Decompress the Encrypted Data

```python
encrypted_blob = container[304:]
decompressed = zlib.decompress(encrypted_blob)
iv = decompressed[:16]
```

### Step 3: Recover the Password

Since we know the user is **"zed"**, the first 3 bytes of the IV must be `zed`. The next 13 bytes are the beginning of the password and we only need to brute force the remaining 3 bytes of the 16-byte password:

```py
known_part = iv[3:16]
total = 256**3

for i in range(total):
    suffix = i.to_bytes(3, 'big')
    candidate = known_part + suffix
    if hashlib.sha256(candidate).hexdigest() == metadata["password_hash"]:
        found_password = candidate
        break
```

### Step 4: Decrypt the Flag

Once we have the password, we just need to derive the AES key as done in the original code (SHA-256 hash of the password, first 16 bytes) and decrypt the flag using the openzed decryption.

```py
key = hashlib.sha256(found_password).digest()[:16]
plaintext = aes_cbc_zed_decrypt(decompressed, key)
flag = plaintext.decode().strip()
```

## solve.py


```py
import hashlib, json, zlib
from Crypto.Cipher import AES

def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def aes_cbc_zed_decrypt(full_ct, key):
    ecb = AES.new(key, AES.MODE_ECB)
    iv = full_ct[:16]
    ct = full_ct[16:]
    blocks = [ct[i:i+16] for i in range(0, len(ct), 16)]
    pt = b""
    for i, block in enumerate(blocks):
        if i == len(blocks) - 1:
            if len(blocks) == 1:
                prev = iv
            else:
                prev = blocks[i-1]
            prev_enc = ecb.encrypt(prev)
            pt_block = xor(prev_enc, block)
            pt += pt_block
        elif i == 0:
            decrypted = ecb.decrypt(block)
            pt_block = xor(decrypted, iv)
            pt += pt_block
        else:
            decrypted = ecb.decrypt(block)
            pt_block = xor(decrypted, blocks[i-1])
            pt += pt_block
    return pt


with open("flag.txt.ozed", "rb") as f:
    container = f.read()
assert container.startswith(b"OZED")

metadata = json.loads(container[4:304].rstrip(b"\x00").decode())

stored_hash = metadata["password_hash"]
print("[*] Retrieved metadata:")
print("    User:         ", metadata["user"])
print("    Filename:     ", metadata["filename"])
print("    Size:         ", metadata["size"])
print("    Password hash:", stored_hash)

encrypted_blob = container[304:]
decompressed = zlib.decompress(encrypted_blob)
iv = decompressed[:16]
assert iv[:3] == b"zed"
known_part = iv[3:16]  # first 13 bytes of the password
print("[*] Known part of password (from IV):", known_part)

found_password = None
total = 256**3
print("[*] Brute-forcing last 3 bytes of password ({} possibilities)...".format(total))
for i in range(total):
    suffix = i.to_bytes(3, 'big')
    candidate = known_part + suffix
    if hashlib.sha256(candidate).hexdigest() == stored_hash:
        found_password = candidate
        print("[*] Found password:", found_password)
        break
    if i % 1000000 == 0 and i != 0:
        print("    Tried {} possibilities...".format(i))

if found_password is None:
    print("Password not found!")
    exit(1)

key = hashlib.sha256(found_password).digest()[:16]
plaintext = aes_cbc_zed_decrypt(decompressed, key)
flag = plaintext.decode().strip()

print("[*] Flag:",end=' ')
print(flag)
```
