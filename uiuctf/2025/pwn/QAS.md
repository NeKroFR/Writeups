# QAS 

This challenge requires us to bypass this vulnerable authentication system:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Quantum-grade type definitions for maximum security
typedef int not_int_small;
typedef short int_small;
typedef int not_int_big;
typedef not_int_small int_big;
typedef unsigned char quantum_byte;
typedef quantum_byte* quantum_ptr;

// Advanced authentication structures
typedef struct {
    not_int_big val;
} PASSWORD_QUANTUM;

typedef struct {
    int_small val;
    quantum_byte padding[2];
    quantum_byte checksum;
    quantum_byte reserved;
} INPUT_QUANTUM;

// Memory-aligned structure for optimal quantum processing
struct __attribute__((packed)) quantum_data_s {
    INPUT_QUANTUM input;
    PASSWORD_QUANTUM password;
    quantum_byte entropy_pool[8];
    quantum_byte quantum_state[16];
};

typedef struct quantum_data_s quantum_data_t;

// Quantum random number generator (patent pending)
static inline quantum_byte generate_quantum_entropy() {
    static quantum_byte seed = 0x42;
    seed = ((seed << 3) ^ (seed >> 5)) + 0x7f;
    return seed;
}

// Initialize quantum security subsystem
void init_quantum_security(quantum_data_t* qdata) {
    for (int i = 0; i < 8; i++) {
        qdata->entropy_pool[i] = generate_quantum_entropy();
    }

    // Initialize quantum state with pseudo-random values
    for (int i = 0; i < 16; i++) {
        qdata->quantum_state[i] = (quantum_byte)(i * 0x11 + 0x33);
    }

    qdata->input.padding[0] = 0;
    qdata->input.padding[1] = 0;
}

// Quantum hash function (revolutionary technology)
not_int_big quantum_hash(INPUT_QUANTUM input, quantum_byte* entropy) {
    int_small input_val = input.val;
    not_int_big hash = input_val;

    // Apply quantum transformation matrix
    hash ^= (entropy[0] << 8) | entropy[1];
    hash ^= (entropy[2] << 4) | (entropy[3] >> 4);
    hash += (entropy[4] * entropy[5]) & 0xff;
    hash ^= entropy[6] ^ entropy[7];
    hash |= 0xeee;
    hash ^= input.padding[0] << 8 | input.padding[1];

    return hash;
}

// Decrypt the victory condition
void access_granted() {
    printf("Quantum authentication successful!\n");
    printf("Accessing secured vault...\n");

    FILE *fp = fopen("flag.txt", "r");
    if (fp == NULL) {
        printf("Error: Quantum vault is offline\n");
        printf("Please contact the quantum administrator.\n");
        return;
    }

    char flag[100];
    if (fgets(flag, sizeof(flag), fp) != NULL) {
        printf("CLASSIFIED FLAG: %s\n", flag);
    } else {
        printf("Error: Quantum decryption failed\n");
        printf("Please contact the quantum administrator.\n");
    }
    fclose(fp);
}

int main() {
    quantum_data_t qdata;

    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    // Initialize quantum security subsystem
    init_quantum_security(&qdata);

    // Set quantum password (TODO: implement proper quantum key derivation)
    qdata.password.val = 0x555;

    printf("=== QUANTUM AUTHENTICATION SYSTEM v2.7.3 ===\n");
    printf("Initializing quantum security protocols...\n");

    // Simulate quantum initialization delay
    for (volatile int i = 0; i < 100000; i++) { /* quantum processing */ }

    printf("Quantum entropy generated. System ready.\n");
    printf("Please enter your quantum authentication code: ");

    // Read user input
    if (scanf("%d", (int*)&qdata.input.val) != 1) {
        printf("Invalid quantum input format!\n");
        return 1;
    }

    // Calculate input checksum for integrity
    qdata.input.checksum = (quantum_byte)(qdata.input.val & 0xff);

    // Apply quantum hash transformation
    not_int_big hashed_input = quantum_hash(qdata.input, qdata.entropy_pool);

    printf("Quantum hash computed: 0x%x\n", hashed_input);

    // Verify quantum authentication
    if (hashed_input == qdata.password.val) {
        access_granted();
    } else {
        printf("Quantum authentication failed!\n");
        printf("Access denied. Incident logged.\n");
    }

    return 0;
}
```

Our goal is to bypass the authentication system by crafting a 16-bit integer that, when processed by `quantum_hash` with padding bytes fixed at 0, produces the target hash `0x555`. The system is vulnerable due to a predictable entropy pool and a small input (only 16 bits).

To solve it, we can just bruteforce until we find a valid input.

## solve.py:

```py
from pwn import *

def gen_entropy():
    seed = 0x42
    pool = []
    for _ in range(8):
        seed = (((seed << 3) & 0xff) ^ (seed >> 5)) + 0x7f
        seed &= 0xff
        pool.append(seed)
    return pool

def quantum_hash(iv_signed, p0, p1, entropy):
    iv = iv_signed & 0xffff
    if iv & 0x8000:
        iv -= 0x10000

    h = iv
    h ^= (entropy[0] << 8) | entropy[1]
    h ^= (entropy[2] << 4) | (entropy[3] >> 4)
    h = (h + ((entropy[4] * entropy[5]) & 0xff)) & 0xffffffff
    h ^= entropy[6] ^ entropy[7]
    h |= 0xeee
    h ^= (p0 << 8) | p1
    return h & 0xffffffff

entropy = gen_entropy()
target = 0x555

for iv in range(-0x8000, 0x8000):
    h = iv
    h ^= (entropy[0] << 8) | entropy[1]
    h ^= (entropy[2] << 4) | (entropy[3] >> 4)
    h = (h + ((entropy[4] * entropy[5]) & 0xff)) & 0xffffffff
    h ^= entropy[6] ^ entropy[7]
    h |= 0xeee
    # h ^ ((p0<<8)|p1) == target  => pad = h ^ target
    pad = h ^ target
    if not (0 <= pad < 0x10000):
        continue
    p0 = (pad >> 8) & 0xff
    p1 = pad & 0xff
    
    # Formating
    iv16 = iv & 0xffff
    N = (p1 << 24) | (p0 << 16) | iv16
    X = N if N < 0x80000000 else N - 0x100000000

    if quantum_hash(iv, p0, p1, entropy) == target:
        log.success(f"Found X = {X} (0x{N:08x}), iv={iv}, pad=0x{pad:04x}")
        r = remote("qas.chal.uiuc.tf", 1337, ssl=True)
        r.recvuntil(b"code: ")
        r.sendline(str(X).encode())
        print(r.recvall().decode())
        exit()

print("No solution found")
```
