# ShiftHappens

The challenge provides an LFSR:

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

int FEEDBACK = REDACTED //its a secret teehee!  
int L = 16;

uint16_t next(uint16_t current_state){
    uint16_t bit = 0;
    for(int i = 0; i < L; i++){
        bit = bit ^ ( ((current_state >> i) & 1) & ((FEEDBACK >> i) & 1 ) );
    }
    uint16_t new_state = (current_state << 1) | (bit);
    return new_state;
}

int main(int argc, char** argv){
    FILE* fp = fopen("./flag.txt","r");
    if(fp == NULL){
        exit(1);
    }
    char flag[61];
    fscanf(fp, "%s", flag);
    fclose(fp);

    uint16_t state = REDACTED // (*-*) - what are you looking for? 

    int bitstream[60*8];
    for(int i = 0; i < 60*8; i++){
        int bit = (state >> 15) & 1;
        bitstream[i] = bit;
        state = next(state);
    }

    for(int i = 0; i < 60; i++){
        for(int j = 0; j < 8; j++){
            int to_print = (flag[i] >> (7-j)) & 1;
            to_print = to_print ^ bitstream[i*8 + j];
            printf("%d",to_print);
        }
        printf("\n");
    }

    

    return 0;
}
```

We can see that the flag is xored with a 16 bits LFSR keystream (480 bits). 

We know the flag starts with `wctf{`. Thanks to that, we can recover the first 40 keystream bits, derive the initial state `S0` and then brute-force the `FEEDBACK` mask to regenerate the full keystream, and decrypt the flag.

## solve.py


```py
def byte_to_bits(b):
    """Convert a byte (0-255) into a list of 8 bits (MSB first)."""
    return [(b >> (7 - i)) & 1 for i in range(8)]

def bits_to_int(bits):
    """Convert a list of bits (MSB first) into an integer."""
    val = 0
    for bit in bits:
        val = (val << 1) | bit
    return val

def lfsr_next(state, feedback):
    """
    Given a 16-bit state and a feedback mask,
    compute the next state using the LFSR rule:
      new_bit = parity(state & feedback)
      new_state = ((state << 1) & 0xFFFF) | new_bit
    """
    bits = state & feedback
    parity = 0
    while bits:
        parity ^= (bits & 1)
        bits >>= 1
    new_state = ((state << 1) & 0xFFFF) | parity
    return new_state

def simulate_lfsr(S0, feedback, num_bits):
    """
    Simulate the LFSR starting from initial state S0 using the given feedback mask,
    and return the first num_bits output bits. Each output bit is (state >> 15) & 1.
    """
    state = S0
    output = []
    for _ in range(num_bits):
        out_bit = (state >> 15) & 1
        output.append(out_bit)
        state = lfsr_next(state, feedback)
    return output


with open("ciphertext.txt", "r") as f:
    lines = f.read().strip().splitlines()
ciphertext = [int(line, 2) for line in lines]

num_bytes = len(ciphertext)
num_bits = num_bytes * 8
print("Read", num_bytes, "bytes of ciphertext.")

prefix = b"wctf{"
prefix_len = len(prefix)


ks_guess_bytes = [ciphertext[i] ^ prefix[i] for i in range(prefix_len)]
ks_guess = []
for b in ks_guess_bytes:
    ks_guess.extend(byte_to_bits(b))
total_known_bits = len(ks_guess)
print("Recovered", total_known_bits, "keystream bits from known plaintext.")

if total_known_bits < 16:
    print("Not enough known bits; need at least 16.")
    exit(1)

S0 = bits_to_int(ks_guess[:16])
print("Initial state (from known keystream bits): 0x{:04x}".format(S0))

candidate_feedback = None
num_to_check = total_known_bits
for fb in range(0, 1 << 16):
    sim_bits = simulate_lfsr(S0, fb, num_to_check)
    if sim_bits == ks_guess[:num_to_check]:
        candidate_feedback = fb
        print("Found candidate FEEDBACK mask: 0x{:04x}".format(fb))
        break
if candidate_feedback is None:
    print("No candidate FEEDBACK mask found that reproduces the known keystream bits.")
    exit(1)

full_keystream_bits = simulate_lfsr(S0, candidate_feedback, num_bits)
keystream_bytes = []
for i in range(num_bytes):
    b = 0
    for j in range(8):
        b = (b << 1) | full_keystream_bits[i * 8 + j]
    keystream_bytes.append(b)

flag = bytes([ciphertext[i] ^ keystream_bytes[i] for i in range(num_bytes)])
print(flag.decode(errors='replace'))
```
