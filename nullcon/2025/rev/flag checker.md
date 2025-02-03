# Flag Checker

This challenge provide us a `flag_checker` binnary. Looking at it on ida we get this code:

```c
__int64 __fastcall main(int a1, char **a2, char **a3)
{
  char s[40]; // [rsp+0h] [rbp-30h] BYREF
  unsigned __int64 v5; // [rsp+28h] [rbp-8h]

  v5 = __readfsqword(0x28u);
  printf("Enter the flag: ");
  fgets(s, 35, stdin);
  s[strcspn(s, "\n")] = 0;
  if ( (unsigned int)check(s) )
    puts("Correct!");
  else
    puts("Incorrect!");
  return 0LL;
}
```

```c
__int64 __fastcall check(const char *a1)
{
  int i; // [rsp+1Ch] [rbp-34h]
  _BYTE transformed_input[40]; // [rsp+20h] [rbp-30h] BYREF
  unsigned __int64 stack_canary; // [rsp+48h] [rbp-8h]

  stack_canary = __readfsqword(0x28u);
  if ( strlen(a1) != 34 )
    return 0LL;
  sub_11E9((__int64)a1, (__int64)transformed_input);
  for ( i = 0; i <= 33; ++i )
  {
    if ( transformed_input[i] != byte_2020[i] )
      return 0LL;
  }
  return 1LL;
}
```

Looking at `byte_2020` we get those bytes: `f8a8b8216073908380c39b80ab0959d321d3dbd8fb4999e0793c4c492c29ccd4dc42`

From this we can easily retrieve the flag:

```py
byte_2020 = bytes.fromhex("f8a8b8216073908380c39b80ab0959d321d3dbd8fb4999e0793c4c492c29ccd4dc42")

original = bytearray(len(byte_2020))
    
for i in range(34):
    transformed_byte = byte_2020[i]
    reversed_byte = ((transformed_byte << 5) & 0xFF) | (transformed_byte >> 3)
    original[i] = reversed_byte - i ^ 0x5A

print(original.decode())
```
