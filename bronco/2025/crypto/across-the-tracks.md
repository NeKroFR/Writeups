# Across the Tracks Writeup

In this challenge, we are given this ciphertext:
```
`Samddre··ath·dhf@_oesoere·ebun·yhot·no··oso·i·a·lr1rcm·iS·aruf·toibadhn·nadpikudynea{l_oeee·ch·oide·f·n·aoe·sae·aonbdhgo_so·rr.i·tYnl·s·tdot·xs·hdtyy'·.t·cfrlca·epeo·iufiyi.t·yaaf·.a.·ts··tn33}i·tvhr·.tooho···rlmwuI·h·e·iHshonppsoleaseecrtudIdet.·n·BtIpdheiorcihr·or·ovl·c··i·acn·t·su··ootr·:b3cesslyedheIath·e·_`
```
We are also provide some hints:

*I've been working on the railroad, all my live long day. We really should put up a fence, a deer just ran onto the tracks in a zig-zag pattern. After crossing my _tenth_ track tracing the deer, I have found this message! What could it mean?*


We can guess that the ciphertext was produced using a [rail fence cipher](https://en.wikipedia.org/wiki/Rail_fence_cipher) with 10 rails, as hinted by the clues about railroads and a "tenth track." In this cipher, the plaintext is written in a zig-zag (or fence) pattern and then read row by row to form the ciphertext. 

To retrieve the flag, we need to reconstructs the original zig-zag pattern by marking the positions where characters should be placed, filling those positions with the ciphertext characters in order, and then reading off the plaintext in the correct zig-zag order.

## solve.py

```py
def rail_fence_decode(ciphertext, rails):
    n = len(ciphertext)
    fence = [['' for _ in range(n)] for _ in range(rails)]
    rail = 0
    direction = 1 # 1 for down, -1 for up

    # Mark the positions with '*' where text should be placed
    for col in range(n):
        fence[rail][col] = '*'
        rail += direction
        if rail == rails - 1 or rail == 0:
            direction = -direction

    index = 0
    for i in range(rails):
        for j in range(n):
            if fence[i][j] == '*':
                fence[i][j] = ciphertext[index]
                index += 1

    # Read the fence in zig-zag manner to get the original text
    result = []
    rail = 0
    direction = 1
    for col in range(n):
        result.append(fence[rail][col])
        rail += direction
        if rail == rails - 1 or rail == 0:
            direction = -direction

    return "".join(result)

ciphertext = "Samddre··ath·dhf@_oesoere·ebun·yhot·no··oso·i·a·lr1rcm·iS·aruf·toibadhn·nadpikudynea{l_oeee·ch·oide·f·n·aoe·sae·aonbdhgo_so·rr.i·tYnl·s·tdot·xs·hdtyy'·.t·cfrlca·epeo·iufiyi.t·yaaf·.a.·ts··tn33}i·tvhr·.tooho···rlmwuI·h·e·iHshonppsoleaseecrtudIdet.·n·BtIpdheiorcihr·or·ovl·c··i·acn·t·su··ootr·:b3cesslyedheIath·e·_"
rails = 10
plaintext = rail_fence_decode(ciphertext, rails)
print(plaintext)
```
