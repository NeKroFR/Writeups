# Detic

The goal of this challenge is to find a point on Earth that is equidistant from three given locations on earth.

When we connect to the instance we get the following message:
```
||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
|  Hi, as a `ASIS` driver, you should be in a position where you are   |
|  exactly the same distance from three passengers in Iran. We will    |
|  calculate this distance with an accuracy of ten meters. For this,   |
|  assume that the earth is completely spherical and its radius is     |
|  exactly 6371 km. Hence, in each step you should find the precise    |
|  langitude and altitue and send to server separeted with comma.      |
|  Are you ready? please send [Y]es or [N]o.                           |
||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
```
After aswering `Y`, we get the coordinates :
```
| Consider the following three locations in Iran:
| P1 = ('OWLTAN_CASTLE', (39.60960517227403, 47.75964978116872))
| P2 = ('MOZDORAN_CAVE', (36.15158614723986, 60.54987387810325))
| P3 = ('KUHE_SIAHAN', (27.22154699581871, 62.88183831028374))
| Please send a point with same distance to the above points like x, y:
```

The difficulty comes from calculating on a sphere, using spherical coordinates (latitude, longitude), instead of a flat triangle
While finding the midpoint of a triangle is easy in 2D, it becomes more complex on a sphere.

First, we need convert the points into Cartesian coordinates using the following functions:

```py
def lat_lon_to_cartesian(lat, lon):
    lat = np.radians(lat)
    lon = np.radians(lon)
    x = EARTH_RADIUS * np.cos(lat) * np.cos(lon)
    y = EARTH_RADIUS * np.cos(lat) * np.sin(lon)
    z = EARTH_RADIUS * np.sin(lat)
    return (x, y, z)

def cartesian_to_lat_lon(x, y, z):
    r = np.sqrt(x*x+y*y+z*z)
    # print(f"known radius :{EARTH_RADIUS}\nrecalculated radius:{r}")
    lon = np.arctan2(y, x)
    lat = np.arcsin(z / r)
    return (np.degrees(lat), np.degrees(lon))
```

We found [this article](http://www.geomidpoint.com/calculation.html) that explains how to calculate a geographic midpoint. However, after a closer look, we realized it calculates the **geographic** midpoint, not the **geometrical** one that we need.

After further research, we found [This paper on spherical geometry](http://www.verniana.org/volumes/02/LetterSize/SphericalGeometry.pdf) which provided the formula we were looking for.

![](https://i.imgur.com/8wEyQEV.png)

By applying the described calculations, we get the following code:

```py
def appendix(P1,P2,P3):
    (xa,ya,za) = lat_lon_to_cartesian(*P1)
    (xb,yb,zb) = lat_lon_to_cartesian(*P2)
    (xc,yc,zc) = lat_lon_to_cartesian(*P3)
    #print(f"coordinates:\nx{xa}:{ya}:{za}\ny:{xb}:{yb}:{zb}\nc:{xc}:{yc}:{zc}")
    axb = (ya*zb - za*yb,za*xb - xa*zb, xa*yb - ya*xb)
    bxc = (yb*zc - zb*yc,zb*xc - xb*zc, xb*yc - yb*xc)
    cxa = (yc*za - zc*ya,zc*xa - xc*za, xc*ya - yc*xa)
    m = (axb[0]+bxc[0]+cxa[0],axb[1]+bxc[1]+cxa[1],axb[2]+bxc[2]+cxa[2])
    #print(f"final coordinates:{m[0]}:{m[1]}:{m[2]}")
    return cartesian_to_lat_lon(*m)
```

Full script :

```py
from pwn import remote
import numpy as np
import re

EARTH_RADIUS = 6371

def lat_lon_to_cartesian(lat, lon):
    lat = np.radians(lat)
    lon = np.radians(lon)
    x = EARTH_RADIUS * np.cos(lat) * np.cos(lon)
    y = EARTH_RADIUS * np.cos(lat) * np.sin(lon)
    z = EARTH_RADIUS * np.sin(lat)
    return (x, y, z)

def cartesian_to_lat_lon(x, y, z):
    r = np.sqrt(x*x+y*y+z*z)
    # print(f"known radius :{EARTH_RADIUS}\nrecalculated radius:{r}")
    lon = np.arctan2(y, x)
    lat = np.arcsin(z / r)
    return (np.degrees(lat), np.degrees(lon))

def appendix(P1,P2,P3):
    (xa,ya,za) = lat_lon_to_cartesian(*P1)
    (xb,yb,zb) = lat_lon_to_cartesian(*P2)
    (xc,yc,zc) = lat_lon_to_cartesian(*P3)
    #print(f"coordinates:\nx{xa}:{ya}:{za}\ny:{xb}:{yb}:{zb}\nc:{xc}:{yc}:{zc}")
    axb = (ya*zb - za*yb,za*xb - xa*zb, xa*yb - ya*xb)
    bxc = (yb*zc - zb*yc,zb*xc - xb*zc, xb*yc - yb*xc)
    cxa = (yc*za - zc*ya,zc*xa - xc*za, xc*ya - yc*xa)
    m = (axb[0]+bxc[0]+cxa[0],axb[1]+bxc[1]+cxa[1],axb[2]+bxc[2]+cxa[2])
    #print(f"final coordinates:{m[0]}:{m[1]}:{m[2]}")
    return cartesian_to_lat_lon(*m)

r = remote("65.109.192.143", 13770)
r.settimeout(5)
r.sendline(b"Y")
pattern = re.compile(r"\(([\d\.\-]+), ([\d\.\-]+)\)")

while True:
    try:
        res = r.recvuntil(b"Please send a point with same distance to the above points like x, y:").decode()
        matches = pattern.findall(res)
        P1_lat, P1_lon = matches[0]
        P2_lat, P2_lon = matches[1]
        P3_lat, P3_lon = matches[2]
        P1 = (float(P1_lat), float(P1_lon))
        P2 = (float(P2_lat), float(P2_lon))
        P3 = (float(P3_lat), float(P3_lon))
        #print("P1:", P1)
        #print("P2:", P2)
        #print("P3:", P3)
        centroid_lat, centroid_lon = appendix(P1,P2,P3)
        rounded_answer = f"{round(centroid_lat, 14)},{round(centroid_lon, 14)}"
        #print("Answer:", rounded_answer)
        #print("dist from P1: "+str(P1[0] - centroid_lat)+","+str(P1[1] - centroid_lon))
        #print("dist from P2: "+str(P2[0] - centroid_lat)+","+str(P2[1] - centroid_lon))
        #print("dist from P3: "+str(P3[0] - centroid_lat)+","+str(P3[1] - centroid_lon))
        r.sendline(rounded_answer.encode())
    except:
        while True:
            try:
                print(r.recv().decode())
            except:
                exit()

```

## Acknowledgements
A special thanks to [qt1b](https://github.com/qt1b), for is help with the correct calculations.
Check out [his writeup](https://github.com/qt1b/writeups/blob/main/asis/2024/detic.md).
