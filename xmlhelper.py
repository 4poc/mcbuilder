
# - reads and writes xml files
# - construct xml files out of a tree

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

from xmlcomb import XMLCombiner

import sys
import os
import logging
import re

log = logging.getLogger(__name__)
formatter = logging.Formatter('[%(filename)s:%(lineno)s] %(levelname)s - %(message)s')
log.setLevel(logging.DEBUG)
print_handler = logging.StreamHandler(sys.stdout)
print_handler.setFormatter(formatter)
log.addHandler(print_handler)

class XMLWriter(object):
    def __init__(self, root):
        self.root = root

    def to_string(self):
        """Returns the root as prettified xml."""
        # needs to reparse using minidom, because etree doesnt support this
        reparsed = minidom.parseString(ET.tostring(self.root, 'utf-8'))
        xml = reparsed.toprettyxml(indent='    ')
        # cleanup:
        xml = re.sub(r'[ ]+\n', '', xml)
        xml = re.sub(r'\n\n+', '\n', xml)
        return xml

class XMLReader(object):
    def __init__(self, filename):
        self.filename = filename
        self.root = None
        if os.path.isfile(filename):
            self._load()

    def _load(self):
        tree = ET.parse(self.filename)
        self.root = tree.getroot()

    @property
    def get_root(self):
        log.info('foo')
        return self.root



