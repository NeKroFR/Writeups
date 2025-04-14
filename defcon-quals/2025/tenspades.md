# tenspades 

This challenge provide us a binary wich require us to guess it's shuffling pattern based of a given seed:

```
❯ ./tenspades
tenspades
sA s2 s3 s4 s5 s6 s7 s8 s9 sX sJ sQ sK hA h2 h3 h4 h5 h6 h7 h8 h9 hX hJ hQ hK cA c2 c3 c4 c5 c6 c7 c8 c9 cX cJ cQ cK dA d2 d3 d4 d5 d6 d7 d8 d9 dX dJ dQ dK
seed: 5a3ee4b7
show me your cards
sA s2 s3 s4 s5 s6 s7 s8 s9 sX sJ sQ sK hA h2 h3 h4 h5 h6 h7 h8 h9 hX hJ hQ hK cA c2 c3 c4 c5 c6 c7 c8 c9 cX cJ cQ cK dA d2 d3 d4 d5 d6 d7 d8 d9 dX dJ dQ dK
Oh no, were you bluffing too?
s5 h5 h3 dX h9 d4 s3 h2 d8 cJ h8 s9 c9 hK c8 c4 c5 c2 c6 cQ s2 d9 s8 h7 s4 dA cA dK d2 hX d5 dJ cK cX s7 hJ s6 dQ hA sK d6 sJ h4 c3 h6 sA d7 d3 sX c7 sQ hQ
seed: 69638cad
show me your cards
^C
```

Using ida, we can see three interesting functions:
```c
__int64 __fastcall generate_seed(__int64 seed_buffer, int input_seed)
{
  *(_DWORD *)seed_buffer = input_seed ^ 0x77777777;
  *(_QWORD *)(seed_buffer + 4) = 0x7FFFFFFF000007E5LL;
  random_seed = (unsigned int)std::random_device::_M_getval(...) ^ 0x77777777;
  *(_DWORD *)(seed_buffer + 12) = random_seed;
  return random_seed;
}
```

```c
__int64 __fastcall compute_seed(_DWORD *seed_buffer)
{
  new_seed = (unsigned int)(seed_buffer[1] + *seed_buffer * seed_buffer[3]) % seed_buffer[2];
  seed_buffer[3] = new_seed;
  return new_seed;
}
```

```c
__int64 __fastcall shuffle_deck(_OWORD *a1, _DWORD *a2)
{
  current_index = 51LL;
  do
  {
    swap_index = (unsigned int)compute_seed(a2) % (current_index + 1);
    result = *((unsigned __int8 *)a1 + current_index);
    *((_BYTE *)a1 + current_index) = *((_BYTE *)a1 + swap_index);
    *((_BYTE *)a1 + (unsigned int)swap_index) = result;
    --current_index;
  }
  while (current_index);
  return result;
}
```

The program basically shuffles the deck by first creating random numbers using a [LCG](https://en.wikipedia.org/wiki/Linear_congruential_generator), then it uses the [Fisher-Yates algorithm](https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle) to shuffle the deck.

To solve the challenge, we just need to retrieve the seed and shuffle the deck as the binary does.

## solve.py

```py
from pwn import *

MULTIPLIER = 1337 ^ 0x77777777  # 0x7777724E
INC = 0x7E5
MOD = 0x7FFFFFFF

def lcg(state):
    product = (MULTIPLIER * state) % (1 << 32)
    return (INC + product) % MOD

def shuffle(deck, seed):
    state = int(seed, 16)
    for i in range(51, -1, -1):
        state = lcg(state)
        j = state % (i + 1)
        deck[i], deck[j] = deck[j], deck[i]
    return deck

def shuffle(deck, seed):
    state = int(seed, 16)
    for i in range(51, -1, -1):
        state = lcg(state)
        j = state % (i + 1)
        deck[i], deck[j] = deck[j], deck[i]

cards = ['sA', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 'sX', 'sJ', 'sQ', 'sK',
         'hA', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9', 'hX', 'hJ', 'hQ', 'hK',
         'cA', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'cX', 'cJ', 'cQ', 'cK',
         'dA', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'dX', 'dJ', 'dQ', 'dK']

# r = process('./tenspades')
r = remote("tenspades-vyl6gsuoz7nky.shellweplayaga.me", 1337)
r.sendlineafter(b'Ticket please:', b'ticket{REDACTED}')

r.recvuntil(b'seed: ')
seed = r.recvline().strip()
shuffle(cards, seed)
print(f'seed: {seed.decode()}')
print(f'shuffled: {' '.join(cards)}')
r.recvline()
r.sendline(' '.join(cards).encode())
r.interactive()
```
