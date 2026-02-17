import struct
from pathlib import Path

def unshuffle(c):
    return ((c>>4)&1)<<3 | ((c>>7)&1)<<2 | ((c>>2)&1)<<1 | ((c>>5)&1)

ik1vm = open("crackme_eva.ik1vm", "rb").read()

# header
code_len, ro_data_len, _ = struct.unpack_from("<III", ik1vm)
ro_data = ik1vm[12 + code_len : 12 + code_len + ro_data_len]

# metadata
meta = ro_data.index(b"\x00") + 1
flag_len = ro_data[meta]
offset, length, key = struct.unpack_from("<QQQ", ro_data, meta + 1)

# decrypt the payload
key_bytes = struct.pack("<Q", key)
buf = bytearray(ro_data)
for i in range(length):
    buf[offset + i] ^= key_bytes[i % 8]
payload = bytes(buf[offset : offset + length])

# grab other_buf between the error string and "flag{}"
fmt_end = payload.index(b"Not even the flag format")
fmt_end = payload.index(b"\n", fmt_end) + 1
flag_buf = payload.index(b"flag{}")
other_buf = payload[fmt_end:flag_buf]
assert len(other_buf) == 64

# revert the bit shuffle
flag = "flag{"
for i in range(32):
    hi, lo = other_buf[2*i], other_buf[2*i+1]
    flag += chr(unshuffle(hi) << 4 | unshuffle(lo))
flag += "}"

print(flag)
