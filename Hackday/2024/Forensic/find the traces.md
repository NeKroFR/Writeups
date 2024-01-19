# Find the traces - 100

We have a huge `dump.dd` file (920MB).

First, we will try to see if the flag is already in the dump

```
>> strings dump.dd | grep HACKDAY{   
```

And yeah that's was it, we get the flag.
