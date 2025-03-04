# Back to the past

This challenge provide us a binary and a *flag.enc* file wich has been encrypted using the binary. Looking the binary on IDA we get this:

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
  char v3; // cl
  int v5; // edx
  char v6; // cl
  const char *v7; // rsi
  int v8; // edx
  char v9; // cl
  int v10; // eax
  char v11; // cl
  int v13; // [rsp+1Ch] [rbp-124h]
  int v14; // [rsp+20h] [rbp-120h]
  __int64 v15; // [rsp+28h] [rbp-118h]
  char v16[264]; // [rsp+30h] [rbp-110h] BYREF
  unsigned __int64 v17; // [rsp+138h] [rbp-8h]

  v17 = __readfsqword(0x28u);
  if ( argc > 1 )
  {
    v14 = time(0LL);
    printf((unsigned int)"time : %ld\n", v14, v5, v6);
    srand(v14);
    v7 = "rb+";
    v15 = fopen64(argv[1]);
    if ( v15 )
    {
      while ( 1 )
      {
        v13 = getc(v15, v7);
        if ( v13 == -1 )
          break;
        fseek(v15, -1LL, 1LL);
        v10 = rand();
        v7 = (const char *)v15;
        fputc(v13 ^ (unsigned int)(v10 % 127), v15);
      }
      fclose(v15);
      strcpy(v16, argv[1]);
      strcat(v16, ".enc");
      if ( (unsigned int)rename(argv[1], v16) )
      {
        printf((unsigned int)"Can't rename %s filename to %s.enc", (unsigned int)argv[1], (unsigned int)argv[1], v11);
        return 1;
      }
      else
      {
        return 0;
      }
    }
    else
    {
      printf((unsigned int)"Can't open file %s\n", (unsigned int)argv[1], v8, v9);
      return 1;
    }
  }
  else
  {
    printf((unsigned int)"Usage: %s <filename>\n", (unsigned int)*argv, (_DWORD)envp, v3);
    return 1;
  }
}
```
```c
__int64 __fastcall srand(int a1)
{
  __int64 result; // rax

  result = (unsigned int)(a1 - 1);
  seed = result;
  return result;
}
```
```c
unsigned __int64 rand()
{
  seed = 0x5851F42D4C957F2DLL * seed + 1;
  return (unsigned __int64)seed >> 33;
}
```

So basically, we need to retrieve the time where the `time(0LL)` was called and then just reverse the xoring to retrieve the flag.

Looking at the binary properties, we can see that it was last modified the **8 May 2024 22∶47∶37**.


![last modified: 8 May 2024 22∶47∶37](https://i.imgur.com/oV9zZK1.png)

Since we do not have the exact timestamp, we will just bruteforce around it and we should get the flag:


## solve.py

```py
import time

def rand():
    global current_seed
    current_seed = (0x5851F42D4C957F2D * current_seed + 1) & 0xFFFFFFFFFFFFFFFF
    return current_seed >> 33

def srand(seed):
    global current_seed
    current_seed = seed - 1

# last modified: 8 May 2024 22∶47∶37
date = int(time.mktime((2024, 5, 8, 22, 47, 37, 0, 0, 0)))

with open('flag.enc', 'rb') as f:
    ciphertext = f.read()

for t in range(date - 86400, date + 86400):
    srand(t)
    flag = bytearray()
    for c in ciphertext:
        flag.append(c ^ (rand() % 127))
    flag = "".join(map(chr, flag))
    if "PWNME{" in flag:
        print(flag)
        break
```
