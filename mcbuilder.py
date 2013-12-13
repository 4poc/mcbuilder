#!/usr/bin/env python
"""Minecraft world build system.

Usage:
  mcbuilder.py [--post=<title> | -f] -i <path> init <buildfile>
  mcbuilder.py [--post=<title> | -f] -i <path> -o <path> build <buildfile>
  mcbuilder.py (-h | --help)

Options:
  -h --help            Show this screen.
  -i --input=<path>    Original world, with placed descriptive signs.
  -o --output=<path>   Must not exist already, copied original world with signs replaced.
  -p --post=<title>    Adds something to world display title.
  -f --force           Replace non-existing signs just by definition in buildfile.

"""
from docopt import docopt


import pymclevel as mclevel
import pymclevel.mclevelbase as mclevelbase
import pymclevel.nbt as nbt
from pymclevel.box import BoundingBox, Vector

import xml.etree.ElementTree as ET

import sys
import os
import os.path
import re
import shutil

import logging

from nbtxml import parse_nbt

from xmlhelper import XMLReader, XMLWriter

log = logging.getLogger(__name__)
formatter = logging.Formatter('[%(filename)s:%(lineno)s] %(levelname)s - %(message)s')
log.setLevel(logging.DEBUG)
print_handler = logging.StreamHandler(sys.stdout)
print_handler.setFormatter(formatter)
log.addHandler(print_handler)

BLOCK_SIGN = 63
BLOCK_WALL_SIGN = 68

# the same facing data values as ladders, wall signs, furnaces and chests
NORTH = 2
SOUTH = 3
WEST = 4
EAST = 5

def value_format(fmt, **kwargs):
    for kw, value in kwargs.iteritems():
        print '%%(%s)' % kw
        print 'fmt='+fmt
        print 'value='+str(value)
        fmt = re.sub('%%\\(%s\\)' % kw, str(value), fmt)
    return fmt

class Block(object):
    def __init__(self, signs, block, node):
        self.signs = signs
        self.block = block
        self.node = node

    @staticmethod
    def from_xml(buildfile, node):
        sign_id = node.attrib['sign']
        signs = buildfile.signs.get_signs(sign_id)

        # block by ID:
        if 'blockId' in node.attrib:
            block_id = int(node.attrib['blockId'])
            block = buildfile.level.materials.blockWithID(block_id)

        if 'blockName' in node.attrib:
            block_name = node.attrib['blockName']
            blocks = buildfile.level.materials.blocksMatching(block_name)
            if len(blocks) > 0: block = blocks[0]

        if not block:
            log.error('unable to find block for element '+str(node))
            return None

        """
        # block data value
        data = None
        if 'data' in node.attrib:
            if re.match('^\d+$', node.attrib['data']):
                data = node.attrib['data']
            else:
                data = value_format(node.attrib['data'], facing=sign.facing, data=sign.data)

        compound = node.find('Compound')
        """

        return Block(signs, block, node)

    def replace(self, level):
        log.info('apply block replacement: ' + str(self))
        for sign in self.signs:
            log.info('replace sign with spec block,')
            log.info('sign: ' + str(sign))



        """
        # try to just copy the data value: TODO: foo
        self.block.blockData = self.data

        log.info('replace block:')
        log.info(str(self))

        bb = BoundingBox((self.sign.x, self.sign.y, self.sign.z),
                (1, 1, 1))

        # remove the tile entity of the sign:
        level.removeTileEntitiesInBox(bb)

        level.fillBlocks(bb, self.block)

        if self.nbt:
            level.addTileEntity(self.nbt)
        """

    def __str__(self):
        return "Block(%d signs, %s)" % (len(self.signs), str(self.block))

class SignList(object):
    def __init__(self):
        self.signs = {}

    def add_sign(self, sign):
        if not sign.id in self.signs:
            self.signs[sign.id] = []
        self.signs[sign.id].append(sign)

    def get_caption(self, id):
        caption = None
        for sign in self.signs[id]:
            if sign.caption and sign.caption != '':
                caption = sign.caption
                break
        return caption

    def create_xml(self):
        group = ET.Element("signs")
        for id, signs in self.signs.iteritems():
            caption = self.get_caption(id)
            node = ET.SubElement(group, "sign")
            node.set('id', str(id))
            if caption:
                node.text = caption
        return group

class Sign(object):
    def __init__(self, x, y, z, data, id, caption, facing):
        self.x = x
        self.y = y
        self.z = z
        self.data = data
        self.id = id
        self.caption = caption
        self.facing = facing

    @staticmethod
    def from_tile(tile, id, data):
        x = tile["x"].value
        y = tile["y"].value
        z = tile["z"].value
        text = []
        for i in range(4):
            txt = tile["Text%d" % (i+1)].value 
            if txt and txt != '': text.append(txt)
        content = ' '.join(text)
        log.info('check sign with content: ' + content)
        desc = Sign.parse_content(content)

        if desc:
            facing = Sign.get_facing(id, data)
            return Sign(x, y, z, data, int(desc['id']), desc['name'], facing)
        else:
            log.warn('ignore sign with content: ' + content)

    @staticmethod
    def get_facing(id, data):
        """http://minecraft.gamepedia.com/Data_values"""
        if id == BLOCK_WALL_SIGN:
            return data
        else:
            if data in (0xF, 0x0, 0x1, 0x2):
                return SOUTH
            elif data in (0x3, 0x4, 0x5, 0x6):
                return WEST
            elif data in (0x7, 0x8, 0x9, 0xA):
                return NORTH
            elif data in (0xB, 0xC, 0xD, 0xE):
                return EAST

    @staticmethod
    def parse_content(content):
        """Parses signs formatted like '1# description'"""
        matches = re.match('^(\d+)# ?(.*)$', content)
        if matches:
            return {
                'id': matches.group(1),
                'name': matches.group(2)
            }

    def __str__(self):
        return "Sign x%d y%d z%d id=%d data=%d facing=%d" % (self.x, self.y, self.z, self.id, self.data, self.facing)

class Buildfile(object):
    def __init__(self, path, world_path):
        self.path = path
        log.info('loading minecraft world, path: %s' % world_path)
        self.level = mclevel.fromFile(world_path)
        log.info('world loaded, title: %s' % self.level.displayName)
        self.post_title = None
        self.force_sign = False # replace non-existing signs just by xml definition

        self.signs = SignList()
        self.blocks = []
        self.root = None

        self._load_xml()
        

    def load_signs(self):
        for i, cPos in enumerate(self.level.allChunks):
            try:
                chunk = self.level.getChunk(*cPos)
            except mclevelbase.ChunkMalformed:
                continue

            for tile in chunk.TileEntities:
                if tile["id"].value == "Sign":
                    x = tile['x'].value
                    y = tile['y'].value
                    z = tile['z'].value

                    blockId = self.level.blockAt(x, y, z)
                    blockData = self.level.blockDataAt(x, y, z)

                    log.info('sign found @ x%d y%d z%d ID=%d Data=%d' %(x, y, z, blockId, blockData))
                    
                    sign = Sign.from_tile(tile, blockId, blockData)
                    if sign: # this returns None if the sign is not in the correct format
                        self.signs.add_sign(sign)

            if i % 100 == 0:
                log.info('reading tiles from chunk %d' % i)

    def _load_xml(self):
        """Loads the xml buildfile."""
        try:
            self.root = XMLReader(self.path).root


            #for sign in self.root.findall('./signs/sign'):
            #    self.load_sign_xml(sign)

            for block in self.root.findall('./blocks/block'):
                self.load_block_xml(block)

            # load replacments etc...
        except:
            pass

    def load_block_xml(self, node):
        """Used to replace signs with blocks/tiles of any type."""
        self.blocks.append(Block.from_xml(self, node))

    def existing_xml(self):
        return os.path.isfile(self.path)

    def create_xml(self):
        """Creates a xml file with all the data from the signs and exising xml."""
        if self.root is not None:
            root = self.root
            signs = root.find('signs')
            if signs is not None: root.remove(signs)
        else:
            root = ET.Element("mcbuilder")

        signs = self.signs.create_xml()
        root.insert(0, signs)

        return XMLWriter(root).to_string()

    def write_xml(self):
        with open(self.path, 'w') as f:
            xml = self.create_xml()
            if xml and xml != '':
                f.write(xml)

    def block_replace(self):
        #if self.post_title:
        #    self.level.displayName += ' ' + self.post_title

        for block in self.blocks:
            block.replace(self.level)

if __name__ == '__main__':
    args = docopt(__doc__, version='mcbuilder 0.1')
    log.debug('docopt args: ' + str(args))

    world = args['--input']
    if not os.path.isdir(world):
        log.error('world not found: %s' % world)
        sys.exit(1)
    log.info('using input world: %s' % world)

    out_world = None
    if args['--output']:
        out_world = args['--output']
        log.info('using existing world: %s' % world)
        log.info('using output world: %s' % out_world)
        if os.path.isdir(out_world):
            log.error('output world does already exist!')
            sys.exit(1)

        log.info('copy world original world to working/output...')
        shutil.copytree(world, out_world)

    else:
        out_world = world

    build = Buildfile(args['<buildfile>'], out_world)
    # TODO: kwargs..
    build.post_title = args['--post']
    build.force_sign = args['--force']

    build.load_signs()
 
    # init loads the signs and writes the xml file, adding found signs to it
    if args['init']:
        log.info('init signs in buildfile: %s' % build.path)
        build.write_xml()

    # replace all signs in the world with the specified replacements
    elif args['build']:
        build.block_replace()
        log.info('save changed world to %s' % out_world)
        build.level.generateLights()
        build.level.saveInPlace()


