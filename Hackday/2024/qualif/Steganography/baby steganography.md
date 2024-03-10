# Baby steganography -100

So we have this image:

<img width="200" src="https://i.imgur.com/nQi9cqD.jpg">

Basically it's a binary encoding on 8 bytes where the `\=0` and `/=1`

After decoding the image we have:
```
01001000
01000001
01000011
01001011
01000100
01000001
01011001
01111011
01110100
00110000
01110101
01110010
01011111
01100100
01100101
01011111
01100011
01101000
01100001
01110101
01100110
01100110
01100101
01111101
```
We can get the flag using cyberchef.

<img width="700" src="https://i.imgur.com/FzAHsjX.jpg">

