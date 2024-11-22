# Lagrange 1

This challenge is a crackme that asks us for a password and verify if it is the flag:
```
❯ ./lagrange_1 test
Welcome to Lagrange's password checker!
Nice try, but your password is invalid.
```

Oppening the binary on ida we get this `main` function:

```c
__int64 __fastcall main(int argc, char **argv, char **envp)
{
  char *match_count; // rax
  char *current_char; // [rsp+20h] [rbp-18h]
  int match_count_1; // [rsp+28h] [rbp-10h]
  unsigned int checksum_index; // [rsp+2Ch] [rbp-Ch]

  process_and_print((__int64)&unk_401B60, 0x28u);
  if ( argc == 2 )
  {
    checksum_index = 0;
    match_count_1 = 0;
    current_char = argv[1];
    do
    {
      if ( (unsigned int)calculate_checksum(dword_401F00, 32u, checksum_index) == (unsigned __int8)*current_char )
        ++match_count_1;
      ++checksum_index;
      match_count = current_char++;
    }
    while ( *match_count );
    if ( checksum_index == match_count_1 && checksum_index == 32 )
      process_and_print((__int64)&unk_401DA0, 0x53u);
    else
      process_and_print((__int64)&unk_401D00, 0x28u);
    return 0LL;
  }
  else
  {
    format_and_print(dword_401C00, 0x3Au, *argv);
    return 1LL;
  }
}
```
We can see that it compares each chars of our input with chars from `dword_401F00`. Let's analyse the `calculate_checksum` and the `process_and_print` functions:

```c
__int64 __fastcall calculate_checksum(unsigned int *data, unsigned int n, unsigned int multiplier)
{
  unsigned __int64 i; // [rsp+10h] [rbp-10h]
  unsigned int current_multiplier; // [rsp+18h] [rbp-8h]
  unsigned int checksum; // [rsp+1Ch] [rbp-4h]

  checksum = *data;
  current_multiplier = multiplier;
  for ( i = 1LL; i < n; ++i )
  {
    checksum = (checksum + current_multiplier * data[i]) % 127;
    current_multiplier = multiplier * current_multiplier % 127;
  }
  return checksum;
}
```

```c
__int64 __fastcall process_and_print(__int64 a1, unsigned int a2)
{
  __int64 result; // rax
  unsigned int i; // [rsp+1Ch] [rbp-Ch]

  for ( i = 0; ; ++i )
  {
    result = i;
    if ( i >= a2 )
      break;
    result = calculate_checksum(a1, a2, i);
    if ( !(_DWORD)result )
      break;
    putchar(result);
  }
  return result;
}
```

We can observe that `process_and_print` calculates the checksum for each character and displays the result until it encounters a `null` checksum.


To retrieve the flag, we simply need to extract the value of `dword_401F00` and apply the process_and_print function to it.
This leads to the following solve script:

```py
def ints_from_hex(s):
    arr = []
    for e in [int(s[i:i+2], 16) for i in range(0, len(s), 2)]:
        if e != 0:
            arr.append(e)
    arr.append(0)
    return arr

def calculate_checksum(data, n, multiplier):
    checksum = data[0]
    current_multiplier = multiplier
    for i in range(1, n):
        checksum = (checksum + current_multiplier * data[i]) % 127
        current_multiplier = (multiplier * current_multiplier) % 127
    return checksum


def print_message(data, n):
    for i in range(n):
        res = calculate_checksum(data, n, i)
        if not res:
            break
        print(chr(res), end="")
    return res

flag = ints_from_hex("47000000090000004b000000680000003600000004000000620000002b00000049000000690000001d0000006e0000004f0000002a000000350000001e00000071000000780000005b00000049000000790000001c0000001f000000230000001d0000004a000000290000004900000076000000650000007500000057000000")
print_message(flag, 32)
print()
```
