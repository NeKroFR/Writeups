# Blueprint mirage - 100

The chall provide us a `blueprint.txt` file wich is a Gcode file of the hackday logo.

<img width="500" src="https://i.imgur.com/EqC0kgz.png">

Looking on the file we can see an interesting part:
```
;Set parameters
F072
F065
F067
F075
F068
F065
F089
F123
F080
F114
F051
F083
F115
F095
F070
F095
F055
F079
F095
F112
F114
F065
F089
F125
M82 ;absolute extrusion mode
```
If we try to take the parameters values and convert it in ascii we can get the flag:

```py
Ints = [72,65,67,75,68,65,89,123,80,114,51,83,115,95,70,95,55,79,95,112,114,65,89,125,82]
print(''.join([chr(i) for i in Ints]))
```
and yep we can get the flag this way
```
HACKDAY{...}R
```
