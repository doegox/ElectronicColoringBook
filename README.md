ElectronicColoringBook
======================

Colorize data file according to repetitive chunks, typical in ECB encrypted.

See usage and examples on the project page:

https://doegox.github.io/ElectronicColoringBook/

This toy is released under the WTFPL (Do What the Fuck You Want to Public License).

Copyright (C) 2014 Philippe Teuwen <phil teuwen org>

```
Usage: ElectronicColoringBook.py [options] file

Colorize data file according to repetitive chunks, typical in ECB encrypted
data

Options:
  -h, --help            show this help message and exit
  -c COLORS, --colors=COLORS
                        Number of colors to use, default=16
  -b BLOCKSIZE, --blocksize=BLOCKSIZE
                        Blocksize to consider, in bytes, default=16
  -g GROUPS, --groups=GROUPS
                        Groups of N blocks e.g. when blocksize is not multiple
                        of underlying data, default=1
  -r RATIO, --ratio=RATIO
                        Ratio of output image
  -x WIDTH, --width=WIDTH
                        Width of output image
  -y HEIGHT, --height=HEIGHT
                        Height of output image
  -s SAMPLING, --sampling=SAMPLING
                        Sampling when guessing image size. Smaller is slower
                        but more precise, default=1000
  -m MAXRATIO, --maxratio=MAXRATIO
                        Max ratio to test when guessing image size. E.g.
                        default=3 means testing ratios from 1:3 to 3:1
  -o OFFSET, --offset=OFFSET
                        Offset to skip original header, in number of blocks
  -f, --flip            Flip image top<>bottom
  -p PIXELWIDTH, --pixelwidth=PIXELWIDTH
                        How many bytes per pixel in the original image
  -R, --raw             Display raw image in 256 colors
```
