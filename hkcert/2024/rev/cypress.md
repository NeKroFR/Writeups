# Cyp.ress

The chall provide us a `pyc` file. 

First, we can decompile it using the `dis` python module:

```py
import dis
import marshal


with open('sser.cpython-312.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

with open('disas.txt', 'w') as f:
    dis.dis(code, file=f)
```

```
 1           0 RESUME                   0
              2 LOAD_CONST               0 (0)
              4 LOAD_CONST               1 (None)
              6 IMPORT_NAME              0 (os)
              8 STORE_NAME               0 (os)
             10 LOAD_CONST               0 (0)
             12 LOAD_CONST               1 (None)
             14 IMPORT_NAME              1 (requests)
             16 STORE_NAME               1 (requests)
             18 LOAD_CONST               0 (0)
             20 LOAD_CONST               2 (('AES',))
             22 IMPORT_NAME              2 (Crypto.Cipher)
             24 IMPORT_FROM              3 (AES)
             26 STORE_NAME               3 (AES)
             28 POP_TOP
             30 LOAD_CONST               0 (0)
             32 LOAD_CONST               1 (None)
             34 IMPORT_NAME              4 (hashlib)
             36 STORE_NAME               4 (hashlib)
             38 LOAD_CONST               4 ('What is the flag?> ')
             40 CALL_INTRINSIC_1         1 (INTRINSIC_PRINT)
             42 POP_TOP
             44 LOAD_CONST               3 (<code object get_nonce at 0x772f0df7ef70, file "sser.py", line 6>)
             46 MAKE_FUNCTION            0
             48 STORE_NAME               5 (get_nonce)
             50 PUSH_NULL
             52 LOAD_NAME                6 (input)
             54 BUILD_STRING             0
             56 CALL                     1
             64 LOAD_ATTR               15 (NULL|self + encode)
             84 CALL                     0
             92 STORE_NAME               8 (flag)
             94 PUSH_NULL
             96 LOAD_NAME                5 (get_nonce)
             98 CALL                     0
            106 STORE_NAME               9 (nonce)
            108 PUSH_NULL
            110 LOAD_NAME                1 (requests)
            112 LOAD_ATTR               20 (post)
            132 LOAD_CONST               5 ('https://c12-cypress.hkcert24.pwnable.hk/')
            134 LOAD_CONST               6 ('nonce')
            136 LOAD_NAME                9 (nonce)
            138 LOAD_ATTR               23 (NULL|self + hex)
            158 CALL                     0
            166 BUILD_MAP                1
            168 KW_NAMES                 7 (('json',))
            170 CALL                     2
            178 STORE_NAME              12 (r)
            180 LOAD_NAME               13 (bytes)
            182 LOAD_ATTR               29 (NULL|self + fromhex)
            202 LOAD_NAME               12 (r)
            204 LOAD_ATTR               30 (text)
            224 CALL                     1
            232 STORE_NAME              16 (c0)
            234 PUSH_NULL
            236 LOAD_NAME                4 (hashlib)
            238 LOAD_ATTR               34 (sha256)
            258 LOAD_CONST               8 (b'key/')
            260 LOAD_NAME                9 (nonce)
            262 BINARY_OP                0 (+)
            266 CALL                     1
            274 LOAD_ATTR               37 (NULL|self + digest)
            294 CALL                     0
            302 LOAD_CONST               1 (None)
            304 LOAD_CONST               9 (16)
            306 BINARY_SLICE
            308 STORE_NAME              19 (key)
            310 PUSH_NULL
            312 LOAD_NAME                4 (hashlib)
            314 LOAD_ATTR               34 (sha256)
            334 LOAD_CONST              10 (b'iv/')
            336 LOAD_NAME                9 (nonce)
            338 BINARY_OP                0 (+)
            342 CALL                     1
            350 LOAD_ATTR               37 (NULL|self + digest)
            370 CALL                     0
            378 LOAD_CONST               1 (None)
            380 LOAD_CONST               9 (16)
            382 BINARY_SLICE
            384 STORE_NAME              20 (iv)
            386 PUSH_NULL
            388 LOAD_NAME                3 (AES)
            390 LOAD_ATTR               42 (new)
            410 LOAD_NAME               19 (key)
            412 LOAD_NAME                3 (AES)
            414 LOAD_ATTR               44 (MODE_CFB)
            434 LOAD_NAME               20 (iv)
            436 CALL                     3
            444 STORE_NAME              23 (cipher)
            446 LOAD_NAME               23 (cipher)
            448 LOAD_ATTR               49 (NULL|self + encrypt)
            468 LOAD_NAME                8 (flag)
            470 CALL                     1
            478 STORE_NAME              25 (c1)
            480 PUSH_NULL
            482 LOAD_NAME               26 (print)
            484 LOAD_CONST              11 ('🙆🙅')
            486 LOAD_NAME               16 (c0)
            488 LOAD_NAME               25 (c1)
            490 COMPARE_OP              55 (!=)
            494 BINARY_SUBSCR
            498 CALL                     1
            506 POP_TOP
            508 RETURN_CONST             1 (None)

Disassembly of <code object get_nonce at 0x772f0df7ef70, file "sser.py", line 6>:
  6           0 RESUME                   0

  7           2 NOP

  8     >>    4 LOAD_GLOBAL              1 (NULL + os)
             14 LOAD_ATTR                2 (urandom)
             34 LOAD_CONST               1 (16)
             36 CALL                     1
             44 STORE_FAST               0 (nonce)

  9          46 LOAD_GLOBAL              5 (NULL + hashlib)
             56 LOAD_ATTR                6 (sha256)
             76 LOAD_CONST               2 (b'pow/')
             78 LOAD_FAST                0 (nonce)
             80 BINARY_OP                0 (+)
             84 CALL                     1
             92 LOAD_ATTR                9 (NULL|self + digest)
            112 CALL                     0
            120 LOAD_CONST               0 (None)
            122 LOAD_CONST               3 (3)
            124 BINARY_SLICE
            126 LOAD_CONST               4 (b'\x00\x00\x00')
            128 COMPARE_OP              40 (==)
            132 POP_JUMP_IF_FALSE        2 (to 138)
            134 LOAD_FAST                0 (nonce)
            136 RETURN_VALUE

  7     >>  138 JUMP_BACKWARD           68 (to 4)
```

From this we can reconstruct the source code:

```py
import os
import requests
from Crypto.Cipher import AES
import hashlib

def get_nonce():
    while True:
        nonce = os.urandom(16)
        if hashlib.sha256(b"pow/" + nonce).digest()[:3] == b"\x00\x00\x00":
            return nonce

print('What is the flag?> ', end='')
flag = input().encode()
nonce = get_nonce()

r = requests.post('https://c12-cypress.hkcert24.pwnable.hk/', json={'nonce': nonce.hex()})
c0 = bytes.fromhex(r.text)

key = hashlib.sha256(b"key/" + nonce).digest()[:16]
iv = hashlib.sha256(b"iv/" + nonce).digest()[:16]
cipher = AES.new(key, AES.MODE_CFB, iv)
c1 = cipher.encrypt(flag)
print('🙆🙅'[c0 != c1])
```

We then can retrieve the flag using decrypt instead of encrypt on c1:

```py
import os
import requests
from Crypto.Cipher import AES
import hashlib

def get_nonce():
    while True:
        nonce = os.urandom(16)
        if hashlib.sha256(b"pow/" + nonce).digest()[:3] == b"\x00\x00\x00":
            return nonce


nonce = get_nonce()

r = requests.post('https://c12-cypress.hkcert24.pwnable.hk/', json={"nonce": nonce.hex()})
c0 = bytes.fromhex(r.text)

key = hashlib.sha256(b"key/" + nonce).digest()[:16]
iv = hashlib.sha256(b"iv/" + nonce).digest()[:16]
cipher = AES.new(key, AES.MODE_CFB, iv)
print(cipher.decrypt(c0))
```