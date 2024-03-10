# C'est en forgeant que l'on devient forgeron - 100

We need to abuse this service:
```
>>> nc 89.234.169.8 9123

Since our server is trustworthy, here is our public key : (85430506336481075750733479678936489786366147049320400350200416362642559793393410744058609541677046110838951195841058117673307821124093970834689156622404384798923680695096493726072097789749644553409778638104492781212493796979945880330636347132662423591151078212727114598102580130048145835305374867411550341927, 65537)
Menu:
1. Sign a word from our authorized word list
2. Verify that a signature comes froum our server
Enter your choice >1
Here is our list of words :
potato
tomato
carrot
Enter the word you want to sign >potato
Here is your signature: 10601960878770032647729636198767860442907019899707314605724753669708238772102089204195797665039923070855798744819343684485272012068739768067646114596173395862781674933875183321334211184250003904783637921647250350420625623745213501208990487909719920002972111659953857041815311962360729380611393226437741941835
Menu:
1. Sign a word from our authorized word list
2. Verify that a signature comes froum our server
Enter your choice >2 
You need to provide the word used and its signature for the server to verify
Start with the word >potato
Enter the signature >10601960878770032647729636198767860442907019899707314605724753669708238772102089204195797665039923070855798744819343684485272012068739768067646114596173395862781674933875183321334211184250003904783637921647250350420625623745213501208990487909719920002972111659953857041815311962360729380611393226437741941835
Valid signature.
Menu:
1. Sign a word from our authorized word list
2. Verify that a signature comes froum our server
Enter your choice >
```

The challenge ask us to generate a valid signature.
Due to the fact that we have acess to the signatures of the words  `potato` `tomato` and `carrot`, we can simply multiply the bytes of two words, `potato` and `tomato` for example and the signature will simply be the multiplaction of their signatures:

$x1 = s1$ ^ $x2 = s2 \Rightarrow x1x2 = s1s2$  

We can do it with this script:
```py
from Crypto.Util.number import long_to_bytes, bytes_to_long
from pwn import *

s = remote("89.234.169.8" ,9123)
res = s.recv().decode()[58:-1]
n, e = map(int, res[1:-1].split(", "))

words = ["potato","tomato"]
signatures = []
for word in words:
    res = s.recv()
    s.send(b"1")
    res = s.recv()
    res = s.recv()
    s.send(word.encode())
    res = s.recv()
    signatures.append(int(res.decode()[len("Here is your signature: "):]))

x1 = bytes_to_long(words[0].encode())
x2 = bytes_to_long(words[1].encode())

s1 = signatures[0]
s2 = signatures[1]

s1_s2 = (s1*s2) % n
x1_x2 = (x1*x2) % n

s.send(b"2")
res = s.recv()
s.send(long_to_bytes(x1_x2))
res = s.recv()
res = s.recv()
s.send(str(s1_s2).encode())
res = s.recv()
print(res)
```
