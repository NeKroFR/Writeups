# Flag checker

The challenge provide us a `flag_checker` elf binary:

```
❯ file flag_checker
flag_checker: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=882faf8d5956c82f64466dffe662c734b564ea43, for GNU/Linux 3.2.0, not stripped
```

Looking at it on ida we have:


```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
  _BYTE v4[40]; // [rsp+0h] [rbp-30h] BYREF
  unsigned __int64 v5; // [rsp+28h] [rbp-8h]

  v5 = __readfsqword(0x28u);
  get_input(v4, argv, envp);
  if ( (unsigned __int8)check_input(v4) )
  {
    puts("PRINTING FLAG: ");
    print_flag(v4);
  }
  return 0;
}

__int64 __fastcall get_input(__int64 a1)
{
  __int64 result; // rax
  int i; // [rsp+18h] [rbp-8h]
  int j; // [rsp+1Ch] [rbp-4h]

  for ( i = 0; i <= 7; ++i )
  {
    printf("> ");
    result = __isoc99_scanf("%u", 4LL * i + a1);
  }
  for ( j = 0; j <= 7; ++j )
  {
    result = *(_DWORD *)(4LL * j + a1) % 0xFFFFFF2F;
    *(_DWORD *)(a1 + 4LL * j) = result;
  }
  return result;
}

__int64 __fastcall check_input(__int64 a1)
{
  int i; // [rsp+10h] [rbp-8h]

  for ( i = 0; i <= 7; ++i )
  {
    if ( (unsigned int)F(test_pt[i], *(unsigned int *)(4LL * i + a1), 4294967087LL) != test_ct[i] )
      return 0LL;
  }
  return 1LL;
}

__int64 __fastcall F(__int64 a1, __int64 a2, unsigned __int64 a3)
{
  __int64 v5; // [rsp+18h] [rbp-10h]
  __int64 v6; // [rsp+20h] [rbp-8h]

  v5 = 1LL;
  v6 = a1 % (__int64)a3;
  while ( a2 > 0 )
  {
    if ( (a2 & 1) != 0 )
      v5 = v6 * v5 % a3;
    v6 = v6 * v6 % a3;
    a2 >>= 1;
  }
  return v5;
}
```

Basically the binary takes 8 `unsigned int` as input, then put them modulo `0xFFFFFF2F` and checks if they match the flag once applyed the `F` function.
This function is just a modular exponentiation btw. 

To solve the challenge, we can just reverses the process using the [Baby-Step Giant-Step algorithm](https://fr.wikipedia.org/wiki/Baby-step_giant-step) to solve the discrete logarithm problem for each pair of `test_pt[i]` and `test_ct[i]` modulo `0xFFFFFF2F`.

## solve.py:

```py
from math import sqrt

def mod_exp(base, exp, mod):
    result = 1
    base = base % mod
    while exp > 0:
        if exp & 1:
            result = (base * result) % mod
        base = (base * base) % mod
        exp >>= 1
    return result

def baby_step_giant_step(g, h, p):
    n = int(sqrt(p)) + 1
    
    baby_steps = {}
    gamma = 1
    for j in range(n):
        if gamma == h:
            return j
        baby_steps[gamma] = j
        gamma = (gamma * g) % p
    
    factor = mod_exp(g, p - 1 - n, p)
    y = h
    
    for i in range(n):
        if y in baby_steps:
            x = i * n + baby_steps[y]
            if x < p - 1:
                return x
        y = (y * factor) % p
    
    return None

MOD = 0xFFFFFF2F

test_pt = [
    0x2265B1F5, 0x91B7584A, 0xD8F16ADF, 0xCD613E30,
    0xC386BBC4, 0x1027C4D1, 0x414C343C, 0x1E2FEB89
]

test_ct = [
    0xDC44BF5E, 0x5AFF1CEC, 0xE1E9B4C2, 0x01329B92,
    0x8F9CA92A, 0x0E45C5B4, 0x604A4B91, 0x7081EB59
]


solutions = []

for i in range(8):
    x = baby_step_giant_step(test_pt[i], test_ct[i], MOD)
    
    if x:
        assert mod_exp(test_pt[i], x, MOD)  == test_ct[i]
        solutions.append(x)
    else:
        print(f"  No solution found for case {i+1}")
        exit()

print(" ".join(map(str, solutions)))
```

```
❯ python solve.py
2127877499 1930549411 2028277857 2798570523 901749037 1674216077 3273968005 3294916953
❯ ./flag_checker
> 2127877499 1930549411 2028277857 2798570523 901749037 1674216077 3273968005 3294916953
> > > > > > > PRINTING FLAG:
sigpwny{CrackingDiscreteLogs4TheFun/Lols}%
```
