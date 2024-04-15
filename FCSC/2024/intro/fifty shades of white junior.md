# Fifty Shades of White (Junior) - 20

The chall provide us a license and a license verification binnary.

## The license:
```
----BEGIN WHITE LICENSE----
TmFtZTogV2FsdGVyIFdoaXRlIEp
1bmlvcgpTZXJpYWw6IDFkMTE3Yz
VhLTI5N2QtNGNlNi05MTg2LWQ0Y
jg0ZmI3ZjIzMApUeXBlOiAxCg==
-----END WHITE LICENSE-----
```

Decoding the content of the license from base64 we have:

```
Name: Walter White Junior
Serial: 1d117c5a-297d-4ce6-9186-d4b84fb7f230
Type: 1
```


## The verifier:

Looking at the code on ghidra we can see a `parse` function wich basically read the license, then it call a check function wich verify if the license is valid.


Looking at the `check` function we have:
```c

void check(undefined8 *param_1)

{
  int iVar1;
  
  iVar1 = validate(*param_1,param_1[1]);
  if (iVar1 == 0) {
    puts("Invalid license!");
  }
  else if (*(int *)(param_1 + 2) == 1) {
    printf("Valid license for %s!\n",*param_1);
  }
  else if (*(int *)(param_1 + 2) == 0x539) {
    printf("Valid admin license for %s!\n",*param_1);
    show_flag();
  }
  else {
    puts("Invalid license, but nice try! Here: https://www.youtube.com/watch?v=dQw4w9WgXcQ");
  }
  return;
}
```
Here is the `validate` function
```c

uint validate(char *param_1,char *param_2)
{
  size_t serialLength;
  void *hashedSerial;
  undefined localHash [4];
  uint checksum;
  uint hashedByteValue;
  ulong index;
  int sumOfChars;
  int i;
  uint isValid;
  
  serialLength = strlen(param_2);
  sha256(param_2,serialLength,&hashedSerial,localHash);
  isValid = 1;
  for (i = 0; i < 3; i = i + 1) {
    sumOfChars = 0;
    index = (ulong)i;
    while( true ) {
      serialLength = strlen(param_1);
      if (serialLength <= index) break;
      sumOfChars = sumOfChars + param_1[index];
      index = index + 3;
    }
    hashedByteValue = (sumOfChars * 0x13 + 0x37) % 0x7f;
    checksum = ((uint)*(byte *)((long)i + (long)hashedSerial) * 0x37 + 0x13) % 0x7f;
    isValid = isValid & hashedByteValue == checksum;
  }
  CRYPTO_free(hashedSerial);
  return isValid;
}
```


# Exploit

To find the key we need to change the `Type` to 1337 and find a new `Serial` wich pass the `validate` function tests.

I made this python script to find a valid serial:

```py
import hashlib
import uuid

def validate(name, serial):
    hashed_serial = hashlib.sha256(serial.encode()).digest()
    for i in range(3):
        sum_of_chars = sum(ord(name[j]) for j in range(i, len(name), 3))
        hashed_byte_value = (sum_of_chars * 0x13 + 0x37) % 0x7f
        checksum = (hashed_serial[i] * 0x37 + 0x13) % 0x7f
        if hashed_byte_value != checksum:
            return False
    return True

name = "Walter White Junior"
while True:
    serial = str(uuid.uuid4())
    if validate(name, serial):
        print(f"Found valid serial: {serial}")
        exit()
```
wich returned: `Found valid serial: 96d2e476-54fe-46f1-b4f8-7ff6e6541f1d`

So I can make this admin license:
```
----BEGIN WHITE LICENSE----
TmFtZTogV2FsdGVyIFdoaXRlIEp
1bmlvcgpTZXJpYWw6IDk2ZDJlND
c2LTU0ZmUtNDZmMS1iNGY4LTdmZ
jZlNjU0MWYxZApUeXBlOiAxMzM3Cg==
-----END WHITE LICENSE-----
```