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
from optparse import OptionParser

options = OptionParser(usage='%prog [options] file', description='Colorize data file according to repetitive chunks, typical in ECB encrypted data')
options.add_option('-c', '--colors', type='int', default=16, help='Number of colors to use')
options.add_option('-b', '--blocksize', type='int', default=16, help='Blocksize to consider, in bytes')
options.add_option('-g', '--groups', type=int, default=1, help='Groups of N blocks e.g. when blocksize is not multiple of underlying data')
options.add_option('-r', '--ratio', default="4:3", help='Ratio of output image')
options.add_option('-f', '--flip', action="store_true", default=False, help='Flip image top<>bottom')

opts, args = options.parse_args()
if len(args) < 1:
    options.print_help()
    sys.exit()

f=open(args[0], 'rb')
content=f.read()
ciphertext=content

ratio=tuple(map(int, opts.ratio.split(':')))

d={}
for i in range(len(ciphertext)/opts.blocksize):
    token=ciphertext[i*opts.blocksize:(i+1)*opts.blocksize].encode('hex')
    if token not in d:
        d[token]=1
    else:
        d[token]+=1

sorted_d = sorted(d.iteritems(), key=operator.itemgetter(1), reverse=True)

sorted_d=sorted_d[:(opts.colors-1)*opts.groups]
sorted_d=filter(lambda x: x[1]>1, sorted_d)
sorted_d=sorted_d[:len(sorted_d)/opts.groups*opts.groups]
if not sorted_d:
    raise NameError("Did not find any single match :-(")
mode="RGBA"
pxsize=4 # RGBA: 4 bytes per pixel
pxblocksize=max(opts.blocksize/pxsize, 1)
A="\xFF" # Alpha channel, if any
# Let's use random colors...
colormap={}
for i in range(len(sorted_d)/opts.groups):
    if i == 0:
        outtoken=("\xff\xff\xff" + A)* pxblocksize # white
    else:
        outtoken=(chr(random.randint(1,254)) + chr(random.randint(1,254)) + chr(random.randint(1,254)) + A) * pxblocksize
    for g in range(opts.groups):
        gi =(i*opts.groups)+g
        colormap[sorted_d[gi][0]]=outtoken
        print "%s %10s #%s" % (sorted_d[gi][0], sorted_d[gi][1], colormap[sorted_d[gi][0]][:3].encode('hex'))
blocksleft=len(ciphertext)/opts.blocksize-reduce(lambda x, y: x+y, [n for (t, n) in sorted_d])
print "%s %10i #%s" % ("*" * len(sorted_d[0][0]), blocksleft, "000000")

out=""
for i in range(len(ciphertext)/opts.blocksize):
    token=ciphertext[i*opts.blocksize:(i+1)*opts.blocksize].encode('hex')
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
if opts.flip:
    i=i.transpose(Image.FLIP_TOP_BOTTOM)
i.save(args[0]+'.ecb_%i.png' % opts.colors)
i.show()
