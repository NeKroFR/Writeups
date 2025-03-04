# My betterzed

This challenge presents a web application that implements a custom encryption scheme named **"OpenZED"**. The application allows users to encrypt and decrypt files using a provided username, password, and optional IV.
The application, built with Flask, provides endpoints to encrypt/decrypt user-uploaded files. The encryption process involves generating metadata, encrypting the data using a custom AES implementation, and creating a container that includes the header, metadata, and encrypted data. The goal is to recover the flag, which is encrypted using this custom scheme.

Looking at **aes_cbc_zed.py** we can see that the challenge implements a hybrid encryption mode, combining AES-CBC and AES-CFB:

<details>
<summary>aes_cbc_zed.py</summary>

```py
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256


def xor(a: bytes, b: bytes) -> bytes:
	return bytes(x^y for x,y in zip(a,b))

class AES_CBC_ZED:
	def __init__(
		self, 
		user : str, 
		password : str, 
		iv : bytes
	):
		self.user = user
		self.iv = iv
		self.password = password
		self.derive_password()

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

		return ciphertext


	def decrypt(self, ciphertext: bytes):
		plaintext = b""
		ecb_cipher = AES.new(key=self.key, mode=AES.MODE_ECB)
		iv = self.iv
		
		for pos in range(0, len(ciphertext), 16):
			chunk = ciphertext[pos:pos+16]
			
			# AES CFB for the last block or if there is only one block
			if len(ciphertext[pos+16:pos+32]) == 0 :
				
				#if plaintext length <= 16, iv = self.iv
				if len(ciphertext) <= 16 :
					prev = iv
				# else, iv = previous ciphertext
				else:
					prev = ciphertext[pos-16:pos]

				prev = ecb_cipher.encrypt(prev)
				plaintext += xor(prev, chunk)
				
			# AES CBC for the n-1 firsts block
			# First block if not the only one is decrypted and xored with IV (CBC)
			elif not plaintext:
				xored = ecb_cipher.decrypt(chunk)
				plaintext += bytes(xor(xored, iv))
				
			# Next blocks are decrypted and xored with the previous ciphertext (CBC)
			else:
				xored = ecb_cipher.decrypt(chunk)
				plaintext += bytes(xor(xored, ciphertext[pos-16:pos]))
				
		return plaintext
			
	
	def derive_password(self):
		salt = b"LESELFRANCAIS!!!"
		self.key = PBKDF2(self.password, salt, 16, count=10000, hmac_hash_module=SHA256)
```
</details>

Here, the vulnerability lies in the fact that the last (or only) block of the encryption is handled using AES-CFB mode.
Specifically, when the plaintext is 16 bytes or shorter, the IV is directly used in the CFB operation. Moreover, the service *always reuses* the same IV.
As detailed in [this post](https://crypto.stackexchange.com/questions/22324/effect-of-cfb-iv-reuse),
*"if the two messages encrypted with the same IV started with blocks M0 and M′0, then the attacker learns the value M0⊕M′0 (and if those were the same, then the attacker also learns the corresponding xor with the second block, etc)."*

Therefore, we can simply encrypt 16 zero bytes with the same IV used to encrypt the flag, and recover the flag by XORing the resulting ciphertexts.

## solve.py

```py
import requests
import zlib
import json

url = 'https://mybetterzed-0c5db0a683b388bf.deploy.phreaks.fr/'

# Step 1: Get the encrypted flag and extract IV and ciphertext
flag_container = requests.get(f'{url}/encrypt_flag/').content
ciphertext1 = zlib.decompress(flag_container[304:])

# Extract metadata (first 300 bytes after 'OZED')
metadata_part = flag_container[4:304]
# Remove trailing null bytes and parse JSON
metadata_json = metadata_part.split(b'\x00')[0].decode()
metadata = json.loads(metadata_json)
iv_flag = bytes.fromhex(metadata['iv'])

# Step 2: Encrypt 16 zeros with the same IV and default credentials
files = {'file': ('zeros.bin', b'\x00' * 16)}
data = {
    'username': '',
    'password': '',
    'iv': iv_flag.hex()
}

encrypted_container = requests.post(f'{url}/encrypt/', files=files, data=data).content
ciphertext2 = zlib.decompress(encrypted_container[304:])

# Step 3: XOR to get the flag
flag = bytes([a ^ b for a, b in zip(ciphertext1, ciphertext2)]).decode()
print(flag)
```
