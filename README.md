SN76489 + AY-3-8910 VGM player for CP/M

Based on VGM player by J.B. Langston
https://github.com/jblang/SN76489

Enhanced with multi-chip support by Marco Maccaferri (https://groups.google.com/g/rc2014-z80/c/9nHnETJzGKU)

YMF-262 (OPL3) support added by Ed Brindley

See tools/decompress for a python program for decompressing vgz files to vgm.

Example: `python3 tools/decompress.py ~/Downloads/OPLArchive-full ./output --flat-output --max-size 40K --skip-existing`

OPL archive is downloadable from https://opl.wafflenet.com

