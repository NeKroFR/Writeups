# again and again and again and again - 400

The chall provide us a `conversation.zip` file with four `conv.txt` files wich are some bytes encoded in base64.

We have this hint: ```Decrypt the conversation using the fact that they are talking about `Hack107` and one of their team member...```

We can guess that they were xored with the same key and if it is the case then we have:

$c1 = p1 \oplus k$

$c2 = p2 \oplus k$

So: $c1 \oplus c2 = p1 \oplus p2$

Knowing that the conversation was writen in english and that `Hack107` is a part of one plaintext we can try to see if we can perform a [Known-plaintext attack](https://en.wikipedia.org/wiki/Known-plaintext_attack).

```py
import base64

def crib_drag(crib, ciphertext):
    arr = []
    for i in range(len(ciphertext) - len(crib)):
        print(i, xor(crib, ciphertext[i:i+len(crib)]))

def xor(a, b):
    return bytes([x ^ y for x, y in zip(a, b)])

c1 = base64.b64decode("YiEjKycKVGgHX3UFFxVCKAsPVBYIPBEdF3xtKDgEXWMGJAEXLC5ZQFg4bl82RjNnLwlDUQwoHSdabzxCXy00ZE0oFlg5ODpZV0cUARcpNC9UNVs9XDRPAA4cFBAANllSMiRCCFxEDxZnWDIrN2wVPWwpCCIhETknTkYONjhGTgU+HwcXZgICEl1VFE0VKCFeSTk5EVJMTBsPVxBfA0slPCBQEwAHPxZ5PD9HOj8BMWEKJSFHKzhZH2sJOBAncUdtZFYgMiUBRX5/YhscABUEJyoZMVwjbTQCLlNfM0UtLHE4LicUJgBEIi10bg==")
c2 = base64.b64decode("FWlvACkEWnlDB3UaFxMWKBcLVBEFK0cZBjMoByJQW19PMwIgYzFQGB0fYD0=")

crib_drag(b"Hack107", xor(c1, c2))
```

returns:
```
0 b'?)/@?>9'
1 b'\x00-He?>&'
2 b'\x04Jme?!s'
3 b'come to'
4 b'Fomzuh7'
5 b'For/i0('
...
```
Bingo, `b'come to'` sounds very english to me.

Then, I've writen this script:
```py
import base64, os

def crib_drag(crib, ciphertext):
    arr = []
    for i in range(len(ciphertext) - len(crib)):
        arr.append(xor(crib, ciphertext[i:i+len(crib)])) 
        print(i, arr[i])
    return arr, len(crib)
def xor(a, b):
    return bytes([x ^ y for x, y in zip(a, b)])

c1 = base64.b64decode("YiEjKycKVGgHX3UFFxVCKAsPVBYIPBEdF3xtKDgEXWMGJAEXLC5ZQFg4bl82RjNnLwlDUQwoHSdabzxCXy00ZE0oFlg5ODpZV0cUARcpNC9UNVs9XDRPAA4cFBAANllSMiRCCFxEDxZnWDIrN2wVPWwpCCIhETknTkYONjhGTgU+HwcXZgICEl1VFE0VKCFeSTk5EVJMTBsPVxBfA0slPCBQEwAHPxZ5PD9HOj8BMWEKJSFHKzhZH2sJOBAncUdtZFYgMiUBRX5/YhscABUEJyoZMVwjbTQCLlNfM0UtLHE4LicUJgBEIi10bg==")
c2 = base64.b64decode("FWlvACkEWnlDB3UaFxMWKBcLVBEFK0cZBjMoByJQW19PMwIgYzFQGB0fYD0=")
c3 = base64.b64decode("ZSgqKTsCETsWXjFKDwJCOBYZBkUMKgMKACM+RXYEXFQBZxMqNjAVGhcaK1l1FjcpMkZ/VgglSyZbaDwKUmwiIUozV1h5bRFQFFhXXlVrKD8AIF48VXMbHANZVQQCKhkGRS4LREQMCFM0XCYiPGJr")
c4 = base64.b64decode("ZSE9Li0ERWlTfSxKDAIVYRgIEBcIPRRYDCNtHzccUR8cJAsjIjZcXkoxKVo4XzppNQlbUQUnD2JZMWgWWCc1KhkuClgcDBp6M3I/FSYEBwQ7AGgHYRYwJyc0cTgqCi4tNQ02O3kwPiwJdgQYAQ0nFzFqSmwPGSghXwJRdzwTQx4iVhJSMhgCU1BaDggCM3QfB1EsD1JMRhEMEhkefQ==")

P1xorP2 = xor(c1, c2)
P1xorP3 = xor(c1, c3)
P1xorP4 = xor(c1, c4)

P1 = ["?"] * len(c1)

while True:
    os.system('clear')
    print("".join(P1))
    crib = bytes(input("🐒Guess🐒: "), 'utf-8')
    arr, lencrib = crib_drag(crib, P1xorP2)
    replace_index = input("Enter index to replace: ")
    try:
        replace_index = int(replace_index)
        if not replace_index < 0 or replace_index >= len(arr):            
            for i in range(replace_index*lencrib, (replace_index+1)*lencrib):
                P1[i] = chr(arr[replace_index][i%lencrib])
    except:
        pass
```

And after some guessing we get:

```py
P2 = b' - Hack107 putting the accent on the seven.\n'
```

Then we can get the other plaintext with this simple script:
```py
import base64

def xor(a, b):
    return bytes([x ^ y for x, y in zip(a, b)])

c1 = base64.b64decode("YiEjKycKVGgHX3UFFxVCKAsPVBYIPBEdF3xtKDgEXWMGJAEXLC5ZQFg4bl82RjNnLwlDUQwoHSdabzxCXy00ZE0oFlg5ODpZV0cUARcpNC9UNVs9XDRPAA4cFBAANllSMiRCCFxEDxZnWDIrN2wVPWwpCCIhETknTkYONjhGTgU+HwcXZgICEl1VFE0VKCFeSTk5EVJMTBsPVxBfA0slPCBQEwAHPxZ5PD9HOj8BMWEKJSFHKzhZH2sJOBAncUdtZFYgMiUBRX5/YhscABUEJyoZMVwjbTQCLlNfM0UtLHE4LicUJgBEIi10bg==")
c2 = base64.b64decode("FWlvACkEWnlDB3UaFxMWKBcLVBEFK0cZBjMoByJQW19PMwIgYzFQGB0fYD0=")
c3 = base64.b64decode("ZSgqKTsCETsWXjFKDwJCOBYZBkUMKgMKACM+RXYEXFQBZxMqNjAVGhcaK1l1FjcpMkZ/VgglSyZbaDwKUmwiIUozV1h5bRFQFFhXXlVrKD8AIF48VXMbHANZVQQCKhkGRS4LREQMCFM0XCYiPGJr")
c4 = base64.b64decode("ZSE9Li0ERWlTfSxKDAIVYRgIEBcIPRRYDCNtHzccUR8cJAsjIjZcXkoxKVo4XzppNQlbUQUnD2JZMWgWWCc1KhkuClgcDBp6M3I/FSYEBwQ7AGgHYRYwJyc0cTgqCi4tNQ02O3kwPiwJdgQYAQ0nFzFqSmwPGSghXwJRdzwTQx4iVhJSMhgCU1BaDggCM3QfB1EsD1JMRhEMEhkefQ==")
P1xorP2 = xor(c1, c2)
P1xorP3 = xor(c1, c3)
P1xorP4 = xor(c1, c4)
p2 = b' - Hack107 putting the accent on the seven.\n'

p1 = xor(p2, P1xorP2)
print(p1)
print(xor(p1, P1xorP2))
print(xor(p1, P1xorP3))
print(xor(p1, P1xorP4))
```
wich returns:
```
b"Welcome to our irc server, AntiRickRoll. I hope you haven't had too much trouble along the way. We'll be able to "
b' - Hack107 putting the accent on the seven.\n'
b"Please send me your address, then your token, and I'll do the rest. - Hack107 putting the accent on the seven.\n"
b'Perfect! My new address is vale.scafati02@gmail.com and my token is HACKDAY{...}'
```
