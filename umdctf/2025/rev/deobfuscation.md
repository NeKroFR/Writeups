# deobfiscation

This challenge provide us this binary:

```c
void __noreturn start()
{
  signed __int64 write_result; // rax
  signed __int64 read_result; // rax
  __int64 i; // rcx
  char input_char; // al
  __int64 j; // rcx
  signed __int64 exit_sucess; // rax
  signed __int64 exit_fail; // rax
  signed __int64 exit_result; // rax

  write_result = sys_write(1u, buf, 0x15uLL);
  read_result = sys_read(0, byte_40209C, 0x80uLL);
  for ( i = 0LL; ; ++i )
  {
    input_char = byte_40209C[i];
    if ( input_char == 10 )
      break;
    *(_BYTE *)(i + 4202780) = byte_402034[i] ^ input_char;
  }
  if ( i == 52 )
  {
    for ( j = 0LL; j < 52; ++j )
    {
      if ( byte_402000[j] != *(_BYTE *)(j + 4202780) )
        goto FAIL;
    }
    byte_40209C[j] = 0;
    exit_sucess = sys_write(1u, aCorrect, 9uLL);
  }
  else
  {
FAIL:
    exit_fail = sys_write(1u, aWrongPassword, 0x12uLL);
  }
  exit_result = sys_exit(0);
}
```

We can see that the program is justt xoring our input `byte_402034` and look if it match `byte_402000`, so we can get the flag just xoring it back.

## solve.py

```py
byte_402034_hex = "756f646561716f757576694560707f65547763746842535445033d7f31587546754460786a74514f1c5f76790b2d75454b556678"
byte_402000_hex = "202220263537140746005a174435520c7028371c5b1d70167650695c6e6c1b1254692d380623113d2f00024a68453b641a20550575"
    
xor_key = bytes.fromhex(byte_402034_hex)
byte_402000 = bytes.fromhex(byte_402000_hex)
    
flag = ''
for i in range(min(len(xor_key), len(byte_402000))):
    flag += chr(byte_402000[i] ^ xor_key[i])
print(flag)
```
