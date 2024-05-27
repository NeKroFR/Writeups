# Indicium - 157

The chall provide us a bunch of numbers wich looks like ASCII values:
```
103 109 98 104 124 99 99 50 54 53 99 101 103 49 49 51 98 55 51 49 101 99 55 54 56 99 57 101 103 57 53 98 57 56 49 55 53 126
```

Converting them to ASCII we get: `gmbh|cc265ceg113b731ec768c9eg95b98175~`
```py
t = [103, 109, 98, 104, 124, 99, 99, 50, 54, 53, 99, 101, 103, 49, 49, 51, 98, 55, 51, 49, 101, 99, 55, 54, 56, 99, 57, 101, 103, 57, 53, 98, 57, 56, 49, 55, 53, 126]
print(''.join([chr(i) for i in t])) # gmbh|cc265ceg113b731ec768c9eg95b98175~
```
We know that the flag start with `flag{` and that `f` is the previous character of `g` in the ASCII table.

We can get the flag by substracting 1 to each ASCII value:
```py
t = [103, 109, 98, 104, 124, 99, 99, 50, 54, 53, 99, 101, 103, 49, 49, 51, 98, 55, 51, 49, 101, 99, 55, 54, 56, 99, 57, 101, 103, 57, 53, 98, 57, 56, 49, 55, 53, 126]
msg = [chr(i-1) for i in t]
print(''.join(msg))
```