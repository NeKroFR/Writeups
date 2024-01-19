# The fish trap - 100

The chall provide us this **corruptedfile**:
```
xxkxxxxkdddddddddddddddccdcddddddddddddddddcxxxxxxxxxxxxxxxxxcdcxcdddddddddddddddddcxxxxxxxxxxxxxxxxxcdcxxxcdddddddddddddddddddcxxxxxxxxxxxxxxxxxccxxcdddddddddddddddddddcxxxxxxxxxxxxxxxxxcdcxxxxcddddddddddddddddddddcxxxxxxxxxxxxxxxxxcdcxcdddddddddddddddddcxxxxxxxxxxxxxxxxxcxxcddcdddddddddddddddddcxxxxxxxxxxxxxxxxxcxxxxxxcddddcdddddddddddddddddddcxxxxxxxxxxxxxxxxxcxccddddddddddddddddddcxxxxxxxxxxxxxxxxxxxxxxcddddddcddddddddddddddddcxxxxxxxxxxxxxxxxxcdcxxxxcddddddddddddddddddddcxxxxxxxxxxxxxxxxxcxxcxxxxcdddddddddddddddddddddddcxxxxxxxxxxxxxxxxxcxcddcddddddddddddddddcxxxxxxxxxxxxxxxxxccdcddddddddddddddddcxxxxxxxxxxxxxxxxxxxxxxcdddddcdddddddddddddddddcxxxxxxxxxxxxxxxxxcxcxcdddddddddddddddddddcxxxxxxxxxxxxxxxxxccdcddddddddddddddddcxxxxxxxxxxxxxxxxxxxxxxcdddddcdddddddddddddddddcxxxxxxxxxxxxxxxxxccxxxxxcddddddddddddddddddddddcxxxxxxxxxxxxxxxxxcdcxxxxxxxcdddddddddddddddddddddddcxxxxxxxxxxxxxxxxxcxxcxxxxcdddddddddddddddddddddddcxxxxxxxxxxxxxxxxxxxxxxcdddddcdddddddddddddddddcxxxxxxxxxxxxxxxxxcxcxcdddddddddddddddddddcxxxxxxxxxxxxxxxxxcxxcxxxxcdddddddddddddddddddddddcxxxxxxxxxxxxxxxxxxxxxxcddcddddddddddddddddddddcxxxxxxxxxxxxxxxxxcxcxxxxxcdddddddddddddddddddddddcxxxxxxxxxxxxxxxxxxxxxxcdddcdddddddddddddddddddcxxxxxxxxxxxxxxxxxcxcxcdddddddddddddddddddcxxxxxxxxxxxxxxxxxxxxxxcddddddcddddddddddddddddcxxxxxxxxxxxxxxxxxccxxxxcdddddddddddddddddddddcxxxxxxxxxxxxxxxxxxxxxxcdddcdddddddddddddddddddcxxxxxxxxxxxxxxxxxcxxxxxxcddc%
```

After some search we can find that it's some [Deadfish](https://esolangs.org/wiki/Deadfish#Python_3.x) code

After runing it we get this output:
```
49 49 48 32 49 48 49 32 49 48 51 32 49 49 51 32 49 48 52 32 49 48 49 32 49 51 49 32 49 55 51 32 49 50 50 32 54 48 32 49 48 52 32 49 51 55 32 49 50 48 32 49 49 48 32 54 49 32 49 50 51 32 49 49 48 32 54 49 32 49 49 54 32 49 48 55 32 49 51 55 32 54 49 32 49 50 51 32 49 51 55 32 54 52 32 49 50 55 32 54 51 32 49 50 51 32 54 48 32 49 49 53 32 54 51 32 49 55 53
```
Then we do `from decimal -> from octal` on cyberchef and boom we have the flag

<img width="700" src="https://i.imgur.com/VLOvJjN_d.webp?maxwidth=760&fidelity=grand">
