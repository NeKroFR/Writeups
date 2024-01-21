# Secret password - 100

The chall consists in retrieving a password and they tell us to connect to this instance: `nc challenges.hackday.fr 50393`

```
>> nc challenges.hackday.fr 50393

Charset is abcdefghijklmnopqrstuvwxyz
Size is 5
>>> a
Bad length input. Expected 1, got 5
>>> abcd
Bad length input. Expected 4, got 5
>>> abcde
1 character are correct 
```
It seems like we need to guess a 5 chars strings to get the password, let's write a script to bruteforce it.
After some searchs, we can see that the chall had 3 steps:

|step | charsets | size
|---|---|---|
| 1 | abcdefghijklmnopqrstuvwxyz | 5 |
| 2 | abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ | 15 |
| 3 | abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 | 35 |


So we made this garbage code: 
 ```py

```

it could be optimized but it works so it's fine.

