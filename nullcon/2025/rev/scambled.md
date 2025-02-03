# Scrambled

The challenge provide us this python script:

```py
import random

def encode_flag(flag, key):
    xor_result = [ord(c) ^ key for c in flag]

    chunk_size = 4
    chunks = [xor_result[i:i+chunk_size] for i in range(0, len(xor_result), chunk_size)]
    seed = random.randint(0, 10)
    random.seed(seed)
    random.shuffle(chunks)
    
    scrambled_result = [item for chunk in chunks for item in chunk]
    return scrambled_result, chunks

def main():
    flag = "REDACTED"
    key = REDACTED

    scrambled_result, _ = encode_flag(flag, key)
    print("result:", "".join([format(i, '02x') for i in scrambled_result]))


if __name__ == "__main__":
    main()
```

With this `output.txt` file:

```
result: 1e78197567121966196e757e1f69781e1e1f7e736d6d1f75196e75191b646e196f6465510b0b0b57
```


To retrieve the flag, we will first convert the ciphertext into chunks of 4 bytes. 
We then brute-force the seed, reorder the chunks accordingly, and use the known prefix `ENO{` to recover the XOR key.

# solve.py

```py
import random

ciphertext = "1e78197567121966196e757e1f69781e1e1f7e736d6d1f75196e75191b646e196f6465510b0b0b57"
scrambled_bytes = [int(ciphertext[i:i+2], 16) for i in range(0, len(ciphertext), 2)]

chunk_size = 4
chunks = [scrambled_bytes[i:i+chunk_size] for i in range(0, len(scrambled_bytes), chunk_size)]

prefix = [ord(c) for c in "ENO{"]

for seed in range(11):
    random.seed(seed)
    shuffled_indices = list(range(len(chunks)))
    random.shuffle(shuffled_indices)
    
    reordered_chunks = [None] * len(chunks)
    for i, idx in enumerate(shuffled_indices):
        reordered_chunks[idx] = chunks[i]
    
    reordered_bytes = [b for chunk in reordered_chunks for b in chunk]

    key = prefix[0] ^ reordered_bytes[0]
    
    flag_chars = [chr(b ^ key) for b in reordered_bytes]
    flag = "".join(flag_chars)

    if flag.startswith("ENO{") and flag.endswith("}"):
        print(f"Seed: {seed}, Key: {key}")
        print(f"Recovered flag: {flag}")
        break
```
