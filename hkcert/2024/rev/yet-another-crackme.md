# Yet Another Crackme

This challenge provide us an apk.

First, let's decompile it using jadx:

```
❯ jadx -d crackme com.hkcert24.crackme-Signed.apk
```


Looking at the assemblies we can find some [blob files](https://www.thecobraden.com/posts/unpacking_xamarin_assembly_stores/).
```
❯ ls crackme/resources/assemblies
assemblies.arm64_v8a.blob    assemblies.blob      assemblies.x86_64.blob  rc.bin
assemblies.armeabi_v7a.blob  assemblies.manifest  assemblies.x86.blob
```

We can unpack them using [pyxamstore](https://github.com/jakev/pyxamstore):

```
❯ pyxamstore unpack -d crackme/resources/assemblies
```

Looking at the `out` directory we can find a dll with an interesting name: `CrackMe.dll`.

Let's open it on [dnSpy](https://github.com/dnSpy/dnSpy) we can see this function:

<details>
<summary>Code:</summary>

```csharp
private bool checkFlag(string f)
		{
			int[] array = new int[]
			{
				9,
				10,
				11,
				12,
				13,
				32,
				33,
				34,
				35,
				36,
				37,
				38,
				39,
				40,
				41,
				42,
				43,
				44,
				45,
				46,
				47,
				48,
				49,
				50,
				51,
				52,
				53,
				54,
				55,
				56,
				57,
				58,
				59,
				60,
				61,
				62,
				63,
				64,
				65,
				66,
				67,
				68,
				69,
				70,
				71,
				72,
				73,
				74,
				75,
				76,
				77,
				78,
				79,
				80,
				81,
				82,
				83,
				84,
				85,
				86,
				87,
				88,
				89,
				90,
				91,
				92,
				93,
				94,
				95,
				96,
				97,
				98,
				99,
				100,
				101,
				102,
				103,
				104,
				105,
				106,
				107,
				108,
				109,
				110,
				111,
				112,
				113,
				114,
				115,
				116,
				117,
				118,
				119,
				120,
				121,
				122,
				123,
				124,
				125,
				126
			};
			int[] array2 = new int[]
			{
				58,
				38,
				66,
				88,
				78,
				39,
				80,
				125,
				64,
				106,
				48,
				49,
				98,
				32,
				42,
				59,
				126,
				93,
				33,
				56,
				112,
				120,
				60,
				117,
				111,
				45,
				87,
				35,
				10,
				68,
				61,
				77,
				11,
				55,
				121,
				74,
				107,
				104,
				65,
				63,
				46,
				110,
				34,
				41,
				102,
				97,
				81,
				12,
				47,
				51,
				103,
				89,
				115,
				75,
				54,
				92,
				90,
				76,
				113,
				122,
				114,
				52,
				72,
				70,
				50,
				94,
				91,
				73,
				84,
				95,
				36,
				82,
				124,
				53,
				108,
				101,
				9,
				13,
				44,
				96,
				67,
				85,
				116,
				123,
				100,
				37,
				43,
				119,
				71,
				105,
				118,
				69,
				99,
				79,
				86,
				109,
				62,
				83,
				40,
				57
			};
			ulong[] array3 = new ulong[]
			{
				16684662107559623091UL,
				13659980421084405632UL,
				11938144112493055466UL,
				17764897102866017993UL,
				11375978084890832581UL,
				14699674141193569951UL
			};
			ulong num = 14627333968358193854UL;
			int num2 = 8;
			Dictionary<int, int> dictionary = new Dictionary<int, int>();
			for (int i = 0; i < array.Length; i++)
			{
				dictionary[array[i]] = array2[i];
			}
			StringBuilder stringBuilder = new StringBuilder();
			foreach (char c in f)
			{
				stringBuilder.Append((char)dictionary[(int)c]);
			}
			int num3 = num2 - f.Length % num2;
			string text = stringBuilder.ToString() + new string('\u0001', num3);
			List<ulong> list = new List<ulong>();
			for (int k = 0; k < text.Length - 1; k += num2)
			{
				ulong num4 = BitConverter.ToUInt64(Encoding.ASCII.GetBytes(text.Substring(k, num2)), 0);
				list.Add(num4);
			}
			List<ulong> list2 = new List<ulong>();
			foreach (ulong num5 in list)
			{
				ulong num6 = num ^ num5;
				list2.Add(num6);
			}
			for (int l = 0; l < array3.Length; l++)
			{
				if (array3[l] != list2[l])
				{
					return false;
				}
			}
			return true;
		}
```
</details>

We can easiyly reverse it and get the flag with this python script:

```py
arr1 = [
    9, 10, 11, 12, 13, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 
    48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 
    69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 
    90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 
    109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126
]

arr2 = [
    58, 38, 66, 88, 78, 39, 80, 125, 64, 106, 48, 49, 98, 32, 42, 59, 126, 93, 33, 56, 
    112, 120, 60, 117, 111, 45, 87, 35, 10, 68, 61, 77, 11, 55, 121, 74, 107, 104, 65, 
    63, 46, 110, 34, 41, 102, 97, 81, 12, 47, 51, 103, 89, 115, 75, 54, 92, 90, 76, 113, 
    122, 114, 52, 72, 70, 50, 94, 91, 73, 84, 95, 36, 82, 124, 53, 108, 101, 9, 13, 44, 
    96, 67, 85, 116, 123, 100, 37, 43, 119, 71, 105, 118, 69, 99, 79, 86, 109, 62, 83, 
    40, 57
]

arr3 = [
    16684662107559623091, 13659980421084405632, 11938144112493055466, 
    17764897102866017993, 11375978084890832581, 14699674141193569951
]

dico = {arr1[i]: arr2[i] for i in range(len(arr1))}
inverse_dico = {v: k for k, v in dico.items()}

decrypted = [(c ^ 14627333968358193854) for c in arr3]

flag = []
for c in decrypted:
    flag_bytes = c.to_bytes(8, byteorder='little')
    for byte in flag_bytes:
        if byte in inverse_dico:
            flag.append(chr(inverse_dico[byte]))
        else:
            flag.append('?')

print(''.join(flag))
```