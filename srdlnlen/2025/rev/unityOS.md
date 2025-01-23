# UnityOs

The challenge provide us a `UnityOS.rar` archive, extracting it we can see a bunch of files
Let's just try to grep the flag and well... It worked.

```
❯ grep -R srdnlen{
grep: UnityOs_Linux/Unity_Os_Data/level3: binary file matches
grep: UnityOs_Windows/UnityOS_Data/level3: binary file matches
❯ stringcheese srdnlen{ --file  UnityOs_Linux/Unity_Os_Data/level3
MATCH FOUND! In stream, using encoding ASCII:
srdnlen{yUo_8RoK3_Th3_S1muLaT1oN}
100%|█████████████████████████████████████████████| 529/529 [00:00<00:00, 1096.43it/s]
```