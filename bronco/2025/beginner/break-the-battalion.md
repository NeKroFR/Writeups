# Break the Battalion

This chall provide us a binary. Looking at it on ida we get this source code:

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
  char s1[264]; // [rsp+0h] [rbp-110h] BYREF
  unsigned __int64 v5; // [rsp+108h] [rbp-8h]

  v5 = __readfsqword(0x28u);
  friendlyFunction(argc, argv, envp);
  puts("What is ze passcode monsieur?");
  __isoc99_scanf("%255s", s1);
  encrypt(s1);
  if ( !strcmp(s1, "brigade") )
    puts("correct password");
  else
    puts("wrong password");
  return 0;
}
```

```c
int __fastcall encrypt(const char *a1)
{
  size_t i; // rax
  size_t v3; // [rsp+18h] [rbp-8h]

  v3 = 0LL;
  for ( i = strlen(a1); v3 < i; i = strlen(a1) )
  {
    a1[v3] ^= 0x50u;
    putchar(a1[v3++]);
  }
  return putchar(10);
}
```

From this we can easilly retrieve the password:

```py
def decrypt(encrypted_password, key):
    password = ""
    for char in encrypted_password:
        char_code = ord(char) ^ key
        password += chr(char_code)
    return password

print("The password is:", decrypt("brigade", 0x50))
```

```
❯ python solve.py
The password is: 2"97145
❯ ./a.out
What is ze passcode monsieur?
 2"97145
brigade
correct password
```
