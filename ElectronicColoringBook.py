#!/usr/bin/env python

# Usage: ElectronicColoringBook file [colors [blocksize [ratio]]] groups
# default blocksize is 16
# default number of colors is 16
# groups: group n tokens together, useful e.g. when 3-byte RGB don't match 16-byte blocksize -> 3 types of equivalent token to paint in the same color
# Most common ECB will be painted in white
# All but (color-1) ECB will be painted in black
# Image size and aspect will only be respected if blocksize is multiple of 4

# TODO: propose other colormaps
# TODO guess ratio based on all colors but black (x==y and x != 0xff), on real pixelsize (1501), use out instead of outmap
#   or fill colormap with black and in ratio test x==y and x < #colors
# TODO raw = -b 1 -c 256 -g 1
# TODO raw colormap, not based on histo

import sys, math, random
from PIL import Image
import colorsys
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
options.add_option('-p', '--pixelwidth', type='int', default=1, help='How many bytes per pixel in the original image')

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

# Construct palette
N = 254
HSV_tuples = [(x*1.0/N, 0.8, 0.8) for x in range(N)]
RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
p=[0,0,0]               # black
for rgb in RGB_tuples:
  p.extend(rgb)         # rainbow
p.extend([1, 1, 1])     # white
p=[int(pp*255) for pp in p]
# Show palette:
#j=Image.fromstring('P', (256, 256), ''.join([chr(a) for a in range(256)]*256))
#j.putpalette(p)
#j.show()

# Let's use random colors = random refs to the colormap...
colormap={}
for i in range(len(histo)/opts.groups):
    if i == 0:
        color=255 # white
    else:
        color=random.randint(1,254)
    for g in range(opts.groups):
        gi =(i*opts.groups)+g
        colormap[histo[gi][0]]=chr(color)
        print "%s %10s #%02X -> #%02X #%02X #%02X" % (histo[gi][0], histo[gi][1], color, p[color*3], p[(color*3)+1], p[(color*3)+2])
blocksleft=len(ciphertext)/opts.blocksize-reduce(lambda x, y: x+y, [n for (t, n) in histo])
# All other blocks will be painted in black:
color=0
print "%s %10i #%02X -> #%02X #%02X #%02X" % ("*" * len(histo[0][0]), blocksleft, color, p[color*3], p[(color*3)+1], p[(color*3)+2])

# Construct output stream
out=""
outlenfloat=0.0
for i in range(len(ciphertext)/opts.blocksize):
    token=ciphertext[i*opts.blocksize:(i+1)*opts.blocksize].encode('hex')
    if token in colormap:
        byte=colormap[token]
    else:
        byte=chr(color)
    out+=byte*(opts.blocksize/opts.pixelwidth)
    outlenfloat+=float(opts.blocksize)/opts.pixelwidth
    if outlenfloat >= len(out) + 1:
        out+=byte

if opts.width is None and opts.height is None and opts.ratio is None:
    M=3
    print "Trying to guess ratio between 1:%i and %i:1 ..." % (M, M)

    outmap=[]
    for i in range(len(ciphertext)/opts.blocksize):
        token=ciphertext[i*opts.blocksize:(i+1)*opts.blocksize].encode('hex')
        outmap+=['\xFF' if token == histo[0][0] else '\x00']
    # outmap is now a condensed view of the data where a 0xff byte represents most common block and 0x00 the other blocks
    sq=int(math.sqrt(len(outmap)/opts.blocksize*opts.pixelwidth))
    r={}
    print "Width: from %i to %i\nStep: %i\nProgress:" % (sq/M*opts.blocksize/opts.pixelwidth, sq*M*opts.blocksize/opts.pixelwidth, opts.step),
    for i in range(sq/M,sq*M):
        if i % 100 == 0:
           print i*opts.blocksize/opts.pixelwidth,
           sys.stdout.flush()
        A=outmap[:-i:opts.step]
        B=outmap[i::opts.step]
        # How many matches?
        m=reduce(lambda x,y: x+y,[x==y for (x,y) in zip(A,B)])
        r[i]=float(m)/(len(A))
    print ""
    r=sorted(r.iteritems(), key=operator.itemgetter(1), reverse=True)
    opts.width = int(r[0][0]*float(opts.blocksize)/opts.pixelwidth)

if opts.ratio is not None:
    # Compute ratio
    ratio=tuple(map(int, opts.ratio.split(':')))
    l=len(out)
    x=math.sqrt(float(ratio[0])/ratio[1]*l)
    y=x/ratio[0]*ratio[1]
    xy=(int(x), int(y))

if opts.width is not None:
    xy=(opts.width, len(out)/opts.width)

if opts.height is not None:
    xy=(len(out)/opts.height, opts.height)

print "Size: ", repr(xy)

# Create image from output stream & ratio
i=Image.fromstring('P', xy,out)
i.putpalette(p)

if opts.flip:
    i=i.transpose(Image.FLIP_TOP_BOTTOM)
i.save(args[0]+'.ecb_%i.png' % opts.colors)
i.show()
