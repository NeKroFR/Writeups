# PicturePerfect - Forensics

This challenge provide us this picture:

![hi_snowman.jpg](https://i.imgur.com/pGpvWp5.jpeg)

The flag is stored in the metadata of the image:

```
❯ exiftool hi_snowman.jpg
ExifTool Version Number         : 12.76
File Name                       : hi_snowman.jpg
Directory                       : .
File Size                       : 4.1 MB
File Modification Date/Time     : 2025:03:22 09:39:12+01:00
File Access Date/Time           : 2025:03:24 14:16:12+01:00
File Inode Change Date/Time     : 2025:03:22 09:41:15+01:00
File Permissions                : -rw-rw-r--
File Type                       : JPEG
File Type Extension             : jpg
MIME Type                       : image/jpeg
JFIF Version                    : 1.01
Resolution Unit                 : inches
X Resolution                    : 96
Y Resolution                    : 96
Exif Byte Order                 : Big-endian (Motorola, MM)
Padding                         : (Binary data 268 bytes, use -b option to extract)
XMP Toolkit                     : Image::ExifTool 11.88
About                           : uuid:faf5bdd5-ba3d-11da-ad31-d33d75182f1b
Title                           : wctf{.....}
Image Width                     : 3024
Image Height                    : 4032
Encoding Process                : Baseline DCT, Huffman coding
Bits Per Sample                 : 8
Color Components                : 3
Y Cb Cr Sub Sampling            : YCbCr4:2:0 (2 2)
Image Size                      : 3024x4032
Megapixels                      : 12.2
```
