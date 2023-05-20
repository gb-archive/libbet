#!/usr/bin/env python3
import sys
import os
import argparse
from PIL import Image
import pb16

# Find common tools
commontoolspath = os.path.normpath(os.path.join(
    os.path.dirname(sys.argv[0]), "..", "..", "common", "tools"
))
sys.path.append(commontoolspath)
from pilbmp2nes import pilbmp2chr, formatTilePlanar

def snesformat(tile):
    return formatTilePlanar(tile, "0,1;2,3")

def get_bitreverse():
    """Get a lookup table for horizontal flipping."""
    br = bytearray([0x00, 0x80, 0x40, 0xC0])
    for v in range(6):
        bit = 0x20 >> v
        br.extend(x | bit for x in br)
    return br

bitreverse = get_bitreverse()

def hflipGB(tile):
    br = bitreverse
    return bytes(br[b] for b in tile)

hflipSNES = hflipGB

def vflipGB(tile):
    return b"".join(tile[i:i + 2] for i in range(len(tile) - 2, -2, -2))

def vflipSNES(tile):
    return vflipGB(tile[0:16]) + vflipGB(tile[16:32])

def flipuniq(it):
    """Convert list of tiles to unique tiles and 16-bit tilemap.

Tile 0 is hardcoded to the transparent tile.  If tile 0 is not
transparent, the border transition on Super Game Boy briefly blinks
black between the fade out and fade in.
"""
    tiles = [bytes(32)]
    tile2id = {bytes(32): 0}
    tilemap = []
    for tile in it:
        if tile not in tile2id:
            tilenum = len(tiles)
            hf = hflipSNES(tile)
            vf = vflipSNES(tile)
            vhf = vflipSNES(hf)
            tile2id[vhf] = tilenum | 0xC0
            tile2id[vf] = tilenum | 0x80
            tile2id[hf] = tilenum | 0x40
            tile2id[tile] = tilenum
            tiles.append(tile)
        tilemap.append(tile2id[tile])
    return tiles, tilemap

def main(argv=None):
    argv = argv or sys.argv
    infilename, outfilename = argv[1:3]
    im = Image.open(infilename)
    tiles = pilbmp2chr(im, formatTile=snesformat)
    utiles, tilemap = flipuniq(tiles)
    assert len(utiles) <= 64
    pbtiles = b"".join(pb16.pb16(b"".join(utiles)))
    tmrows = [bytes(tilemap[i:i + 32]) for i in range(0, len(tilemap), 32)]

    use_utmrows = False
    use_iur = False

    if use_utmrows:
        from uniq import uniq
        utmrows, tmrowmap = uniq(tmrows)
        if len(utmrows) >= 16:
            raise ValueError("%s: too many unique rows: %d > 15"
                             % (infilename, len(utmrows)))
    else:
        utmrows, tmrowmap = tmrows, list(range(len(tmrows)))
    if use_iur:
        from incruniq import iur_encode_tilemap
        iutmrows = iur_encode_tilemap(b''.join(utmrows))
    else:
        iutmrows = b''.join(pb16.pb16(b''.join(utmrows)))

    palette = im.getpalette()[:48]
    palette.extend(bytes(48 - len(palette)))
    snespalette = bytearray()
    for i in range(0, 48, 3):
        r = palette[i] >> 3
        g = palette[i + 1] >> 3
        b = palette[i + 2] >> 3
        bgr = (b << 10) | (g << 5) | r
        snespalette.append(bgr & 0xFF)
        snespalette.append(bgr >> 8)
    print(snespalette.hex())

    out = b"".join((
        bytes([len(utiles) * 2]), pbtiles,
        bytes([len(utmrows) * 16]) if use_utmrows else b"",
        iutmrows,
        bytes(tmrowmap) if use_utmrows else b"",
        snespalette
    ))
    with open(outfilename, "wb") as outfp:
        outfp.write(out)
    

if __name__=='__main__':
    if 'idlelib' in sys.modules:
        main(["./makeborder.py", "../tilesets/sgbborder.png", "/dev/null"])
    else:
        main()
