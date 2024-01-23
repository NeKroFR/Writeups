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
Bingo, `b'come to'` sends very english to me.
