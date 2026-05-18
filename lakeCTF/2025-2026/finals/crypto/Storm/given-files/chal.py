import hashlib, os, random
from Crypto.Cipher import AES

storm = os.urandom(17)
random.seed(storm)

key = os.urandom(16)

def attempt(key, pt, status):
    c = AES.new(key, AES.MODE_GCM, nonce=b'{status}')
    c.update(status)
    ct, t = c.encrypt_and_digest(pt)
    
    # It's getting dark and stormy, you have difficulty finding anything in the dark
    ct = bytes([a & b for a,b in zip(ct, random.getrandbits(len(ct)*8).to_bytes(len(ct),"little"))])
    # Who knows what will even be heard when you speak!
    t = bytes([a & b for a,b in zip(t, random.getrandbits(len(t)*8).to_bytes(len(t),"little"))])
    return c.nonce.hex(), ct.hex(), t.hex()


print("scour the stormy wastelands to find the magic phrase to calm lain down")

used = 0
while True:
    if used >= 624:
        break

    print("1) explore:")
    print("2) fight:")
    m = input("> ").strip().lower()

    if m != "1":
        break

    pt = input("What are you looking for?: ").encode()

    if used + max(len(pt),16) > 624:
        print("You searched too deep!")
        break

    nonce, secret_phrase, magic_word = attempt(key, pt, b"explorarationing")
    used += max(len(pt),16)
    print(f"you found {nonce}:{secret_phrase}:{magic_word}")


print("Speak the magic word and save the world")
for _ in range(16):
    inp = input("Speak the magic word: ").strip()

    nonce, secret_phrase, magic_word = attempt(key, b"give me the flag", storm)
    
    if inp == magic_word:
        print("       [  Lain descends, the storm dissipating...  ]")
        with open("flag.txt", "r") as f:
            print(f.read())
        exit()
    else:
        print(f"The word was incorrect, maybe carried away by the harsh winds... If only you'd yelled a little more clearly {nonce}:{secret_phrase}:{magic_word}!")
    

