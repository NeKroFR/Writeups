# Mr Unlucky

This challenge provide us a `get_rand` binary.
Opening it on ida we get this code:

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
  unsigned int v3; // eax
  int i; // [rsp+8h] [rbp-38h]
  int v6; // [rsp+Ch] [rbp-34h]
  char s[40]; // [rsp+10h] [rbp-30h] BYREF
  unsigned __int64 v8; // [rsp+38h] [rbp-8h]

  v8 = __readfsqword(0x28u);
  init(argc, argv, envp);
  puts("I have always been unlucky. I can't even win a single game of dota2 :(");
  puts("however, I heard that this tool can lift the curse that I have!");
  puts("YET I CAN'T BEAT IT'S CHALLENGE. Can you help me guess the names?");
  v3 = time(0LL);
  srand(v3);
  sleep(3u);
  puts(
    "Welcome to dota2 hero guesser! Your task is to guess the right hero each time to win the challenge and claim the aegis!");
  for ( i = 0; i <= 49; ++i )
  {
    v6 = rand() % 20;
    printf("Guess the Dota 2 hero (case sensitive!!!): ");
    fgets(s, 30, stdin);
    s[strcspn(s, "\n")] = 0;
    if ( strcmp(s, (&heroes)[v6]) )
    {
      printf("Wrong guess! The correct hero was %s.\n", (&heroes)[v6]);
      exit(0);
    }
    printf("%s was right! moving on to the next guess...\n", s);
  }
  puts("Wow you are one lucky person! fine, here is your aegis (roshan will not be happy about this!)");
  print_flag("flag.txt");
  return 0;
}
```

We can see that we need to retrieve the seed to guess the values returned by the `rand()` function.
We can retireve the random values with this simple c program:

```c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

int main() {
    unsigned int v3;
    int i, v6;

    v3 = time(0LL);
    srand(v3);
    sleep(3);

    for (i = 0; i < 100; ++i) {
        v6 = rand() % 20;
        printf("%d\n", v6);
    }
    
    return 0;
}
```

Then we can get the heroes list from ida:

```
.data:0000000000004020 heroes          dq offset aAntiMage     ; DATA XREF: main+110↑o
.data:0000000000004020                                         ; main+158↑o
.data:0000000000004020                                         ; "Anti-Mage"
.data:0000000000004028                 dq offset aAxe          ; "Axe"
.data:0000000000004030                 dq offset aBane         ; "Bane"
.data:0000000000004038                 dq offset aBloodseeker  ; "Bloodseeker"
.data:0000000000004040                 dq offset aCrystalMaiden ; "Crystal Maiden"
.data:0000000000004048                 dq offset aDrowRanger   ; "Drow Ranger"
.data:0000000000004050                 dq offset aEarthshaker  ; "Earthshaker"
.data:0000000000004058                 dq offset aJuggernaut   ; "Juggernaut"
.data:0000000000004060                 dq offset aMirana       ; "Mirana"
.data:0000000000004068                 dq offset aMorphling    ; "Morphling"
.data:0000000000004070                 dq offset aPhantomAssassi ; "Phantom Assassin"
.data:0000000000004078                 dq offset aPudge        ; "Pudge"
.data:0000000000004080                 dq offset aShadowFiend  ; "Shadow Fiend"
.data:0000000000004088                 dq offset aSniper       ; "Sniper"
.data:0000000000004090                 dq offset aStormSpirit  ; "Storm Spirit"
.data:0000000000004098                 dq offset aSven         ; "Sven"
.data:00000000000040A0                 dq offset aTiny         ; "Tiny"
.data:00000000000040A8                 dq offset aVengefulSpirit ; "Vengeful Spirit"
.data:00000000000040B0                 dq offset aWindranger   ; "Windranger"
.data:00000000000040B8                 dq offset aZeus         ; "Zeus"
.data:00000000000040B8 _data           ends
.data:00000000000040B8
.bss:00000000000040C0 ; ===========================================================================
```

Now we just need to connect to the remote wait for it to generate the seed, do the same locally and then just send the heroes:

```py
from pwn import *
import subprocess
from time import sleep

heroes = ["Anti-Mage", "Axe", "Bane", "Bloodseeker", "Crystal Maiden", "Drow Ranger", "Earthshaker", "Juggernaut", "Mirana", "Morphling", "Phantom Assassin", "Pudge", "Shadow Fiend", "Sniper", "Storm Spirit", "Sven", "Tiny", "Vengeful Spirit", "Windranger", "Zeus"]

r = remote("52.59.124.14",5021)
r.recvuntil(b"e names?")

random_numbers = subprocess.check_output("./get_rand").decode().split()
random_numbers = [int(x) for x in random_numbers]

print("Random numbers:", random_numbers)

for i in range(50):
    r.recvuntil(b" (case sensitive!!!):")
    hero_guess = heroes[random_numbers[i]]
    print(f"Guessing: {hero_guess}")
    r.sendline(hero_guess)
    print(r.recvline())
r.interactive()
```
