# 
#
#

import xml.etree.ElementTree as ET

import re

import pymclevel as mclevel
import pymclevel.mclevelbase as mclevelbase
import pymclevel.nbt as nbt
from pymclevel.box import BoundingBox, Vector

def replace_params(fmt, params):
    for key, value in params.iteritems():
        fmt = re.sub('%%\\(%s\\)' % key, str(value), fmt)
    return fmt

def parse_nbt(node, params={}):
    """Recursivly build nbt datastructure from xml."""

    if 'name' in node.attrib:
        name = node.attrib['name']
    else:
        name = ''

    if node.text and node.text != '':
        text = replace_params(node.text, params)
    else:
        text = ''

    if node.tag == 'Compound':
        values = [] # list of other tags
        for child in node:
            values.append(parse_nbt(child, params))
        return nbt.TAG_Compound(values, name)

    if node.tag == 'List':
        values = [] # list of other tags
        for child in node:
            values.append(parse_nbt(child, params))
        return nbt.TAG_List(values, name)

    elif node.tag == 'String':
        return nbt.TAG_String(text, name)

    elif node.tag == 'Int':
        return nbt.TAG_Int(text, name)

    elif node.tag == 'Byte':
        return nbt.TAG_Byte(text, name)

    elif node.tag == 'Short':
        return nbt.TAG_Short(text, name)

    elif node.tag == 'Long':
        return nbt.TAG_Long(text, name)

    elif node.tag == 'Float':
        return nbt.TAG_Float(text, name)

    elif node.tag == 'Double':
        return nbt.TAG_Double(text, name)

    else:
        raise 'Unsupported'

