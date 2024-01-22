# Baby cryptography - 100


The chall provide us a `secret.txt`:

```
SGRub2slUTd6ZDl4eD58IxobWnZmcDZ2anw6b3R4PnZOUlZRUUZSTkdHWQtYQg5JX11eXEMPPBcVGWNUSR1fTSVhJSwtKyFnPCZqPj8objs4NHImJyA3O3gwNyswPDArQBUNQwELEgIaSR4DCU0NAB0BEx0NUgVXDhAIDwkcEl/l7+Hv6/bz9e2p/e6s+e/j+/T2s/X3+eLsufb67+m+68nMx42uiIbzwMyKwsHdws7exZLE3dnal9rcmt/ZydvctKSm46WjsqK66avrqqi577Swq6D0t6/3rLG/+56xq7rAtYeCicnGkICAiYPMhJ3PgJSAlZGWgpuB2ZSUjpCfky4hVmttdiZgYX9veCx4fS9gfXd9YGw2eH45bnJxeD5rTwFRQEVLBlNATApFSVlZQEJaHhNVRhZAXVVWG11OHksoJGICJzEvMS1pDiI+KC07PyMrczYwPj42PXoyKHNUckA4DRYWRQkJBBBKBA4HCwwEGAQWVBwFVwwWWgsdDxVf6e+i9+zgptT86Pjp+e7l/LD+4uP75v/j/bnu8/m9/fDN0cPN3YXHycyJycTAwcvMxJHG29GV0tbM2Jre0dTKy6Wl4qG95bKvremjpryhr6Gk/9j+9Jq4tL35o7Sp+qi6wIKNjpSJg5ONjcqfhIjOnJOQnN/UmoTXi42Vi4yYmt90aWcjbWh2a2lnficsdGF6N31+M2dweHM4bGk7aHV7P0VPQVFdVVJCTAlOSlhMDltfEUZbURVQWFRVVUxVU1kfISUmMSE2NX1oCnguIik+IDk/JhMmMCciMTw3GG5zKjcNTwoXBksUCkYPGGFmIQsbVwJSFBEBVgMXWQ0UDhZf
```

Also they tell us that `We know that the agent knows how to xor and how to count...` and that the file `was base64 for portability` .

Flag format: `HACKDAY{email}`

decoding it from base we get some bytes so let's xor it with the index of the byte we have this error:
`ValueError: bytes must be in range(0, 256)`

We then write this script to get the flag:

```py
import base64

secret = base64.b64decode(open('secret.txt', 'r').read())
flag = b""
for i in range(len(secret)):
    res = secret[i] ^ i
    if res < 0 or res > 255:
        res = res % 256
    flag += bytes([res])
print(flag)
```
