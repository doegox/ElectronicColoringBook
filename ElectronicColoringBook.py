#!/usr/bin/env python

# Usage: ElectronicColoringBook file [colors [blocksize [ratio]]] groups
# default blocksize is 16
# default number of colors is 16
# groups: group n tokens together, useful e.g. when 3-byte RGB don't match 16-byte blocksize -> 3 types of equivalent token to paint in the same color
# Most common ECB will be painted in white
# All but (color-1) ECB will be painted in black
# Image size and aspect will only be respected if blocksize is multiple of 4

# TODO: propose other modes than 4 bytes pixels

import sys, math, random
from PIL import Image
import operator
from optparse import OptionParser

options = OptionParser(usage='%prog [options] file', description='Colorize data file according to repetitive chunks, typical in ECB encrypted data')
options.add_option('-c', '--colors', type='int', default=16, help='Number of colors to use, default=16')
options.add_option('-b', '--blocksize', type='int', default=16, help='Blocksize to consider, in bytes, default=16')
options.add_option('-g', '--groups', type=int, default=1, help='Groups of N blocks e.g. when blocksize is not multiple of underlying data, default=1')
options.add_option('-r', '--ratio', help='Ratio of output image')
options.add_option('-x', '--width', type='int', help='Width of output image')
options.add_option('-y', '--height', type='int', help='Height of output image')
options.add_option('-s', '--step', type='int', default=100, help='Step when guessing image size. Smaller is slower but more precie, default=100')
options.add_option('-o', '--offset', type='int', default=0, help='Offset to skip original header, in number of blocks')
options.add_option('-f', '--flip', action="store_true", default=False, help='Flip image top<>bottom')

def histogram(data, blocksize):
    d={}
    for i in range(len(data)/blocksize):
        token=data[i*blocksize:(i+1)*blocksize].encode('hex')
        if token not in d:
            d[token]=1
        else:
            d[token]+=1
    return sorted(d.iteritems(), key=operator.itemgetter(1), reverse=True)

opts, args = options.parse_args()
if len(args) < 1:
    options.print_help()
    sys.exit()

if opts.colors < 2:
    print "Please choose at least two colors"
    sys.exit()

if opts.width is not None and opts.height is not None:
    print "Please indicate only -x or -y, not both!"
    sys.exit()

if opts.ratio is not None and (opts.width is not None or opts.height is not None):
    print "Please don't mix -r with -x or -y!"
    sys.exit()

with open(args[0], 'rb') as f:
    f.read(opts.offset * opts.blocksize)
    ciphertext=f.read()

histo=histogram(ciphertext, opts.blocksize)
# Cut histo to those we need to colorize
histo=histo[:(opts.colors-1)*opts.groups]
# Cut histo to discard singletons
histo=filter(lambda x: x[1]>1, histo)
# Cut histo to keep exact multiple of group
histo=histo[:len(histo)/opts.groups*opts.groups]
if not histo:
    raise NameError("Did not find any single match :-(")

mode="RGBA"
pxsize=4 # RGBA: 4 bytes per pixel
pxblocksize=max(opts.blocksize/pxsize, 1)
A="\xFF" # Alpha channel, if any
# Let's use random colors...
colormap={}
for i in range(len(histo)/opts.groups):
    if i == 0:
        outtoken=("\xff\xff\xff" + A)* pxblocksize # white
    else:
        outtoken=(chr(random.randint(1,254)) + chr(random.randint(1,254)) + chr(random.randint(1,254)) + A) * pxblocksize
    for g in range(opts.groups):
        gi =(i*opts.groups)+g
        colormap[histo[gi][0]]=outtoken
        print "%s %10s #%s" % (histo[gi][0], histo[gi][1], colormap[histo[gi][0]][:3].encode('hex'))
blocksleft=len(ciphertext)/opts.blocksize-reduce(lambda x, y: x+y, [n for (t, n) in histo])
print "%s %10i #%s" % ("*" * len(histo[0][0]), blocksleft, "000000")

# Construct output stream
out=""
for i in range(len(ciphertext)/opts.blocksize):
    token=ciphertext[i*opts.blocksize:(i+1)*opts.blocksize].encode('hex')
    if token in colormap:
        out+=colormap[token]
    else:
        out+=("\x00\x00\x00" + A)* pxblocksize # black

if opts.width is None and opts.height is None and opts.ratio is None:
    print "Trying to guess ration between 1:2 and 2:1 ..."

    outmap=[]
    for i in range(len(ciphertext)/opts.blocksize):
        token=ciphertext[i*opts.blocksize:(i+1)*opts.blocksize].encode('hex')
        outmap+=['\xFF' if token == histo[0][0] else '\x00']
    # outmap is now a condensed view of the data where a 0xff byte represents most common block and 0x00 the other blocks
    sq=int(math.sqrt(len(outmap)/pxblocksize))
    r={}
    print "Width: from %i to %i\nStep: %i\nProgress:" % (sq/2*pxblocksize, sq*2*pxblocksize, opts.step),
    for i in range(sq/2,sq*2):
        if i % 100 == 0:
           print i*pxblocksize,
           sys.stdout.flush()
        A=outmap[:-i:opts.step]
        B=outmap[i::opts.step]
        # How many matches?
        m=reduce(lambda x,y: x+y,[x==y for (x,y) in zip(A,B)])
        r[i]=float(m)/(len(A))
    print ""
    r=sorted(r.iteritems(), key=operator.itemgetter(1), reverse=True)
    opts.width = r[0][0]*pxblocksize

if opts.ratio is not None:
    # Compute ratio
    ratio=tuple(map(int, opts.ratio.split(':')))
    l=len(out)/4
    x=math.sqrt(float(ratio[0])/ratio[1]*l)
    y=x/ratio[0]*ratio[1]
    xy=(int(x), int(y))

if opts.width is not None:
    xy=(opts.width, len(out)/4/opts.width)

if opts.height is not None:
    xy=(len(out)/4/opts.height, opts.height)

print "Size: ", repr(xy)

# Create image from output stream & ratio
i=Image.fromstring(mode, xy,out)

if opts.flip:
    i=i.transpose(Image.FLIP_TOP_BOTTOM)
i.save(args[0]+'.ecb_%i.png' % opts.colors)
i.show()
