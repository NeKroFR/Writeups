# Baby forensic - 100
The chall contain a `dump.pcap` file. 

On wireshark we can see that it is a TFTP communication.

<img width="500" src="https://i.imgur.com/6fpETaE_d.webp?maxwidth=760&fidelity=petit">

On the export TFTP list we can find a `conf` file.

<img width="500" src="https://i.imgur.com/4Hf1OM9_d.webp?maxwidth=760&fidelity=grand">

In this file we can find this interesting line: 
```
snmp-server host 192.168.1.4 version 2c SEFDS0RBWXsxTjUxZGVfN0hlX25FdFdPckt9 udp-port 161
```
`SEFDS0RBWXsxTjUxZGVfN0hlX25FdFdPckt9` is the flag encoded in base64.
