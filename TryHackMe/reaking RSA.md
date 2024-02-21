# [Breaking RSA [medium]](https://tryhackme.com/room/breakrsa)

# Enumeration

## nmap
```
>>> nmap -T4 10.10.65.39
Starting Nmap 7.80 ( https://nmap.org ) at 2024-02-21 17:44 CET
Nmap scan report for 10.10.65.39
Host is up (0.041s latency).
Not shown: 998 closed ports
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http

Nmap done: 1 IP address (1 host up) scanned in 0.80 seconds
```

## gobuster

```
>>> gobuster  -u http://10.10.65.39  -w ~/wordlists/SecLists/Discovery/Web-Content/common.txt 

=====================================================
Gobuster v2.0.1              OJ Reeves (@TheColonial)
=====================================================
[+] Mode         : dir
[+] Url/Domain   : http://10.10.65.39/
[+] Threads      : 10
[+] Wordlist     : /home/nk0/wordlists/SecLists/Discovery/Web-Content/common.txt
[+] Status codes : 200,204,301,302,307,403
[+] Timeout      : 10s
=====================================================
2024/02/21 17:44:45 Starting gobuster
=====================================================
/development (Status: 301)
/index.html (Status: 200)
```

![alt text](https://i.imgur.com/BxGGeF3.png)

Here we can get this rsa public key:

```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDrZh8oe8Q8j6kt26IZ906kZ7XyJ3sFCVczs1Gqe8w7ZgU+XGL2vpSD100andPQMwDi3wMX98EvEUbTtcoM4p863C3h23iUOpmZ3Mw8z51b9DEXjPLunPnwAYxhIxdP7czKlfgUCe2n49QHuTqtGE/Gs+avjPcPrZc3VrGAuhFM4P+e4CCbd9NzMtBXrO5HoSV6PEw7NSR7sWDcAQ47cd287U8h9hIf9Paj6hXJ8oters0CkgfbuG99SVVykoVkMfiRXIpu+Ir8Fu1103Nt/cv5nJX5h/KpdQ8iXVopmQNFzNFJjU2De9lohLlUZpM81fP1cDwwGF3X52FzgZ7Y67Je56Rz/fc8JMhqqR+N5P5IyBcSJlfyCSGTfDf+DNiioRGcPFIwH+8cIv9XUe9QFKo9tVI8ElE6U80sXxUYvSg5CPcggKJy68DET2TSxO/AGczxBjSft/BHQ+vwcbGtEnWgvZqyZ49usMAfgz0t6qFp4g1hKFCutdMMvPoHb1xGw9b1FhbLEw6j9s7lMrobaRu5eRiAcIrJtv+5hqX6r6loOXpd0Ip1hH/Ykle2fFfiUfNWCcFfre2AIQ1px9pL0tg8x1NHd55edAdNY3mbk3I66nthA5a0FrKrnEgDXLVLJKPEUMwY8JhAOizdOCpb2swPwvpzO32OjjNus7tKSRe87w==
```

also on the `log.txt` file we get redirected to [this](https://github.com/murtaza-u/zet/tree/main/20220808171808) github repo wich is an implementation of the **Fermat's Factorization Method**.

# Break the key

## What is the length of the discovered RSA key? (in bits)

We can get the len of the key using 
```
>>> ssh-keygen -l -f id_rsa.pub                                  
4..6 SHA256:DIqTDIhboydTh2QU6i58JP+5aDRnLBPT8GwVun1n0Co no comment (RSA)
```

## What are the last 10 digits of n? (where 'n' is the modulus for the public-private key pair)

We can get the last 10 digit of n with this python script:

```py
from Crypto.PublicKey import RSA

f = open("id_rsa.pub", "r")
key = RSA.importKey(f.read())
print(str(key.n)[-10:]) 
```

## Factorize n into prime numbers p and q

Let's try using the [repo](https://github.com/mineiwik/cybersec-writeups/blob/main/thm/breakrsa/README.md)

```py
from Crypto.PublicKey import RSA
from math import *

def factorize(n):
    # since even nos. are always divisible by 2, one of the factors will always
    # be 2
    if (n & 1) == 0:
        return (n/2, 2)

    a = floor(sqrt(n))

    # if n is a perfect square the factors will be ( sqrt(n), sqrt(n) )
    if a * a == n:
        return (a, a)

    # n = (a - b) * (a + b)
    # n = a^2 - b^2
    # b^2 = a^2 - n
    while True:
        a += 1
        _b = a * a - n
        b = int(sqrt(_b))
        if (b * b == _b):
            break

    return (a + b, a - b)


f = open("id_rsa.pub", "r")
key = RSA.importKey(f.read())
print(factorize(key.n))
```
unfortunatly n is too big:
```
Traceback (most recent call last):
  File "/tmp/a/a.py", line 31, in <module>
    print(factorize(key.n)) 
  File "/tmp/a/a.py", line 10, in factorize
    a = floor(sqrt(n))
OverflowError: int too large to convert to float
```
Let's try to use [gmpy2](https://ctftime.org/writeup/25818) to find p and q:

```py
from Crypto.PublicKey import RSA
import gmpy2
def fermat_factor(n):
    assert n % 2 != 0

    a = gmpy2.isqrt(n)
    b2 = gmpy2.square(a) - n

    for i in range(100000000):
        a += 1
        b2 = gmpy2.square(a) - n

        if gmpy2.is_square(b2):
            p = a + gmpy2.isqrt(b2)
            q = a - gmpy2.isqrt(b2)

            return True,(int(p), int(q))
    return False,()

f = open("id_rsa.pub", "r")
key = RSA.importKey(f.read())
print(fermat_factor(key.n))
```


## What is the numerical difference between p and q?

Once we get p and q we can simply do:

```py
(true,(p,q)) = fermat_factor(key.n)
print(p-q)
```

## Generate the private key using p and q (take e = 65537)

To generate the key using [Crypto.PublicKey](https://www.dlitz.net/software/pycrypto/api/current/Crypto.PublicKey.RSA-module.html#construct) we need to find d.
Luckily for us, we know e and we know that d is the inverse of e mod phi(n) wich means that e is also the inverse of d.
So we know that `d= e^-1 mod phi`.

We can generate the key using this script:
```py
from Crypto.PublicKey import RSA
import gmpy2
def fermat_factor(n):
    assert n % 2 != 0

    a = gmpy2.isqrt(n)
    b2 = gmpy2.square(a) - n

    for i in range(100000000):
        a += 1
        b2 = gmpy2.square(a) - n

        if gmpy2.is_square(b2):
            p = a + gmpy2.isqrt(b2)
            q = a - gmpy2.isqrt(b2)

            return True,(int(p), int(q))
    return False,()

f = open("id_rsa.pub", "r")
key = RSA.importKey(f.read())
n = key.n
e = key.e
(true,(p,q)) = fermat_factor(key.n)
phi = (p-1)*(q-1)
d = pow(e, -1, phi) 
private_key = RSA.construct((n, e, d))
open("key.priv","wb").write(private_key.exportKey())
```

# root flag

Once we have the key, we simply had to connect as root:

```
>>> chmod 400 key.priv
>>> ssh -i key.priv root@10.10.65.39                      
The authenticity of host '10.10.65.39 (10.10.65.39)' can't be established.
ED25519 key fingerprint is SHA256:p8ToZTCl6UDL9y+eR4LyuFIrGt62U3kJ+oLKS6Iua84.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '10.10.65.39' (ED25519) to the list of known hosts.
Welcome to Ubuntu 20.04.4 LTS (GNU/Linux 5.4.0-124-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Wed 21 Feb 2024 05:58:39 PM UTC

  System load:  0.0               Processes:             108
  Usage of /:   70.1% of 4.84GB   Users logged in:       0
  Memory usage: 45%               IPv4 address for eth0: 10.10.65.39
  Swap usage:   0%


0 updates can be applied immediately.


The list of available updates is more than a week old.
To check for new updates run: sudo apt update


The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

Last login: Sat Aug 13 09:35:51 2022 from 10.0.0.11
root@thm:~#
```
