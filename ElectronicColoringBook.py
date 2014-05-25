#!/usr/bin/env python

# Usage: ElectronicColoringBook file [colors [blocksize [ratio]]] groups
# default blocksize is 16
# default number of colors is 16
# groups: group n tokens together, useful e.g. when 3-byte RGB don't match 16-byte blocksize -> 3 types of equivalent token to paint in the same color
# Most common ECB will be painted in white
# All but (color-1) ECB will be painted in black
# Image size and aspect will only be respected if blocksize is multiple of 4

# TODO: autocorrelation to guess the proper aspect ratio
# TODO: if histogram by group of 3 tokens this means 3-byte RGB -> should use the same color for the 3 ECB variants

import sys, math, random
from PIL import Image
import operator

# How many ECB to colorize?
colors=16

assert len(sys.argv) >= 2
f=open(sys.argv[1], 'rb')
content=f.read()
ciphertext=content

if len(sys.argv) > 2:
  colors=int(sys.argv[2])
else:
  colors=16

if len(sys.argv) > 3:
  blocksize=int(sys.argv[3])
else:
  blocksize=16

ratio=(4,3)
if len(sys.argv) > 4:
  ratio=tuple(map(int, sys.argv[4].split(':')))

groups=1
if len(sys.argv) > 5:
  groups=int(sys.argv[5])

d={}
for i in range(len(ciphertext)/blocksize):
    token=ciphertext[i*blocksize:(i+1)*blocksize].encode('hex')
    if token not in d:
        d[token]=1
    else:
        d[token]+=1

sorted_d = sorted(d.iteritems(), key=operator.itemgetter(1), reverse=True)

sorted_d=sorted_d[:(colors-1)*groups]
sorted_d=filter(lambda x: x[1]>1, sorted_d)
sorted_d=sorted_d[:len(sorted_d)/groups*groups]
if not sorted_d:
    raise NameError("Did not find any single match :-(")
mode="RGBA"
pxsize=4 # RGBA: 4 bytes per pixel
pxblocksize=max(blocksize/pxsize, 1)
A="\xFF" # Alpha channel, if any
# Let's use random colors...
colormap={}
for i in range(len(sorted_d)/groups):
    if i == 0:
        outtoken=("\xff\xff\xff" + A)* pxblocksize # white
    else:
        outtoken=(chr(random.randint(1,254)) + chr(random.randint(1,254)) + chr(random.randint(1,254)) + A) * pxblocksize
    for g in range(groups):
        gi =(i*groups)+g
        colormap[sorted_d[gi][0]]=outtoken
        print "%s %10s #%s" % (sorted_d[gi][0], sorted_d[gi][1], colormap[sorted_d[gi][0]][:3].encode('hex'))
blocksleft=len(ciphertext)/blocksize-reduce(lambda x, y: x+y, [n for (t, n) in sorted_d])
print "%s %10i #%s" % ("*" * len(sorted_d[0][0]), blocksleft, "000000")

out=""
for i in range(len(ciphertext)/blocksize):
    token=ciphertext[i*blocksize:(i+1)*blocksize].encode('hex')
    if token in colormap:
        out+=colormap[token]
    else:
        out+=("\x00\x00\x00" + A)* pxblocksize # black
l=len(out)/4
x=math.sqrt(float(ratio[0])/ratio[1]*l)
y=x/ratio[0]*ratio[1]
xy=(int(x), int(y))
print "Size: ", repr(xy)
i=Image.fromstring(mode, xy,out)
#i=i.transpose(Image.FLIP_TOP_BOTTOM)
i.save(sys.argv[1]+'.ecb_%i.png' % colors)
i.show()
