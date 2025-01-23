# Anodic Music

This challenge provides a binary that hashes user input and compares it against a list of hashes stored in the `hardcore.bnk` file.

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
    const char *dialogue; // rax
    int i; // [rsp+Ch] [rbp-64h]
    void *hash_buff; // [rsp+10h] [rbp-60h]
    __int64 bank_handle; // [rsp+18h] [rbp-58h]
    _QWORD input_buff[7]; // [rsp+20h] [rbp-50h] BYREF
    int v9; // [rsp+58h] [rbp-18h]
    __int16 v10; // [rsp+5Ch] [rbp-14h]
    unsigned __int64 v11; // [rsp+68h] [rbp-8h]

    v11 = __readfsqword(0x28u);
    memset(input_buff, 0, sizeof(input_buff));
    v9 = 0;
    v10 = 0;
    hash_buff = malloc(0x10uLL);
    bank_handle = load_bank(16LL, argv);
    setbuf(_bss_start, 0LL);
    setbuf(stdin, 0LL);
    for (i = 0; i <= 61; ++i)
    {
        dialogue = (const char *)get_dialogue();
        printf("%s", dialogue);
        *((_BYTE *)input_buff + i) = getc(stdin);
        getc(stdin);
        md5String(input_buff, hash_buff);
        if ((unsigned __int8)lookup_bank(hash_buff, bank_handle))
        {
            puts("There has to be some way to talk to this person, you just haven't found it yet.");
            return -1;
        }
    }
    printf("Hey it looks like you have input the right flag. Why are you still here?");
    return 0;
}
```

We can see that the binary that the flag is verified char by char, so we can just bruteforce each char of the flag and look if the md5 is stored in the database.

# solve.py

```py
import string
from hashlib import md5

bank = open("hardcore.bnk", "rb").read()
bank = {bank[i:i+16] for i in range(0, len(bank), 16)}
alphabet = string.ascii_lowercase + string.ascii_uppercase + string.digits + r"{}_"

def solve(flag="srdnlen{"):
    if len(flag) == 62:
        return flag
    for c in alphabet:
        if md5((flag + c).encode()).digest() not in bank:
            res = solve(flag + c)
            if res:
                return res

print(solve())
```
