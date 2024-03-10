# Sound zero - 176

The chall provide us a `challenge.wav` file wich is a rick roll 🐒

We can get the flag using [Stegocracker](https://github.com/W1LDN16H7/StegoCracker)

```
>>>stego -d -f challenge.wav

/usr/local/lib/python3.10/dist-packages/pydub-0.25.1-py3.10.egg/pydub/utils.py:170: RuntimeWarning: Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work
  warn("Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work", RuntimeWarning)
    _____ __                   ______                __            
  / ___// /____  ____ _____  / ____/________ ______/ /_____  _____
  \__ \/ __/ _ \/ __ `/ __ \/ /   / ___/ __ `/ ___/ //_/ _ \/ ___/
 ___/ / /_/  __/ /_/ / /_/ / /___/ /  / /_/ / /__/ ,< /  __/ /    
/____/\__/\___/\__, /\____/\____/_/   \__,_/\___/_/|_|\___/_/     
              /____/                                              

                 By TheKnight
                 v1.1.5


DecodingMode : On 
[*] Please wait... 
[*] Decoding...
Your Secret Message is: HACKDAY{.........}
Done 
```
