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
import xml.dom.minidom as minidom

import sys
import os
import os.path
import re
import shutil

import logging

from xmlcomb import XMLCombiner
from nbtxml import parse_nbt

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
    def __init__(self, sign, block):
        self.sign = sign
        self.block = block
        self.data = sign.data
        self.nbt = None

    @staticmethod
    def from_xml(buildfile, node):
        sign_id = node.attrib['sign']
        sign = buildfile.get_sign(sign_id)

        # block by ID:
        if 'blockId' in node.attrib:
            block_id = int(node.attrib['blockId'])
            block = buildfile.level.materials.blockWithID(block_id)

        if 'blockName' in node.attrib:
            block_name = node.attrib['blockName']
            blocks = buildfile.level.materials.blocksMatching(block_name)
            if len(blocks) > 0: block = blocks[0]

        if not block:
            log.warn('unable to find block for element '+str(node))
            return None

        block = Block(sign, block)

        # block data value
        if 'data' in node.attrib:
            if re.match('^\d+$', node.attrib['data']):
                data = node.attrib['data']
            else:
                data = value_format(node.attrib['data'], facing=sign.facing, data=sign.data)
            block.data = int(data)

        for child in node:
            if child.tag == 'Compound':
                params = {
                        'x': sign.x,
                        'y': sign.y,
                        'z': sign.z
                        }
                block.nbt = parse_nbt(child, params)

        return block

    def replace(self, level):
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

    def __str__(self):
        return "Block(%s, %s)" % (str(self.sign), str(self.block))

class Sign(object):
    def __init__(self, x, y, z, data, id, name, facing):
        self.x = x
        self.y = y
        self.z = z
        self.data = data
        self.id = id
        self.name = name
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
            return Sign(x, y, z, data, desc['id'], desc['name'], facing)
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
    def from_xml(node):
        x = int(node.attrib['x'])
        y = int(node.attrib['y'])
        z = int(node.attrib['z'])
        data = node.attrib['data']
        id = node.attrib['id']
        name = node.attrib['name']
        facing = node.attrib['facing']
        return Sign(x, y, z, data, id, name, facing)

    def create_xml(self, parent):
        node = ET.SubElement(parent, "sign")
        node.set("id", self.id)
        node.set("name", self.name)
        node.set("x", str(self.x))
        node.set("y", str(self.y))
        node.set("z", str(self.z))
        node.set("data", str(self.data))
        node.set("facing", str(self.facing))
        return node

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
        return "Sign x%d y%d z%d data=%d facing=%d" % (self.x, self.y, self.z, self.data, self.facing)

class Buildfile(object):
    def __init__(self, path, world_path):
        self.path = path
        log.info('loading minecraft world, path: %s' % world_path)
        self.level = mclevel.fromFile(world_path)
        log.info('world loaded, title: %s' % self.level.displayName)
        self.post_title = '0.1'
        self.force_sign = False # replace non-existing signs just by xml definition

        self.signs = []
        self.blocks = []
        

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
                        self.signs.append(sign)

            if i % 100 == 0:
                log.info('reading tiles from chunk %d' % i)

    def load_xml(self):
        """Loads the xml buildfile."""
        if not self.existing_xml(): return

        tree = ET.parse(self.path)
        root = tree.getroot()

        for inc in root.findall('./include'):
            print inc
            # TODO: ...

        for sign in root.findall('./signs/sign'):
            self.load_sign_xml(sign)

        for block in root.findall('./blocks/block'):
            self.load_block_xml(block)

        # load replacments etc...

    def load_sign_xml(self, node):
        sign = Sign.from_xml(node)
        if sign:
            if not self.find_sign(sign):
                log.warn('xml world mismatch, cancel, set force to override')
                log.warn('no sign in world, can replace non-existing sign if -f is set')
                if not self.force_sign:
                    sys.exit()

                self.signs.append(sign)

    def load_block_xml(self, node):
        """Used to replace signs with blocks/tiles of any type."""
        self.blocks.append(Block.from_xml(self, node))

    def find_sign(self, sign):
        for x in self.signs:
            if x.x == sign.x and x.y == sign.y and x.z == sign.z:
                return x

    def get_sign(self, id):
        for sign in self.signs:
            if sign.id == id:
                return sign

    def existing_xml(self):
        return os.path.isfile(self.path)

    def create_xml(self):
        """Creates a xml file with all the data from the signs and exising xml."""
        root = ET.Element("mcbuilder")
        signs = ET.SubElement(root, "signs")
        for sign in self.signs:
            sign.create_xml(signs)
        # ... replacements
        reparsed = minidom.parseString(ET.tostring(root, 'utf-8'))
        return reparsed.toprettyxml(indent="    ")

    def write_xml(self):
        with open(self.path, 'w') as f:
            xml = self.create_xml()
            if xml:
                f.write(xml)

    def block_replace(self):
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
    build.post_title = args['--post']
    build.force_sign = args['--force']

    build.load_signs()

    if build.existing_xml():
        build.load_xml()
 
    # just saves a buildfile with all sign data found in the world
    # the world is not modified, and the buildfile should not already exist
    if args['init']:
        if len(build.blocks) <= 0:
            log.info('write buildfile: %s' % build.path)
            build.write_xml()
        else:
            log.warn('unable to init non-empty buildfile')

    # replace all signs in the world with the specified replacements
    elif args['build']:
        build.block_replace()
        log.info('save changed world to %s' % out_world)
        build.level.generateLights()
        build.level.saveInPlace()


