#!/usr/bin/env python3
"""Turn a real CV DOCX into a person-agnostic lorem-ipsum template.

Every formatting attribute is preserved because we only ever rewrite the text
inside existing <w:t> nodes. Runs, run properties, tab stops, numbering,
paragraph borders, and section properties are never touched.
"""
import re
import sys
import zipfile
import shutil
from docx import Document

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

SRC, DST = sys.argv[1], sys.argv[2]
MAP = sys.argv[3] if len(sys.argv) > 3 else 'cv'
shutil.copy(SRC, DST)

LOREM = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
         "incididunt ut labore et dolore magna aliqua enim ad minim veniam quis nostrud "
         "exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute irure "
         "in reprehenderit voluptate velit esse cillum eu fugiat nulla pariatur excepteur "
         "sint occaecat cupidatat non proident sunt culpa qui officia deserunt mollit anim "
         "id est laborum sed perspiciatis unde omnis iste natus error voluptatem accusantium "
         "doloremque laudantium totam rem aperiam eaque ipsa quae ab illo inventore veritatis "
         "et quasi architecto beatae vitae dicta explicabo nemo ipsam quia voluptas aspernatur "
         "aut odit fugit sequi nesciunt neque porro quisquam dolorem adipisci numquam eius "
         "modi tempora incidunt magnam quaerat").split()

_cursor = [0]


def lorem(nchars, capitalize=True, end_period=True):
    """Deterministic lorem text of roughly `nchars` characters."""
    out = []
    n = 0
    while n < nchars:
        w = LOREM[_cursor[0] % len(LOREM)]
        _cursor[0] += 1
        out.append(w)
        n += len(w) + 1
    s = ' '.join(out)
    if len(s) > nchars + 6:                       # trim the overshoot
        s = s[:nchars].rsplit(' ', 1)[0]
    if capitalize:
        s = s[0].upper() + s[1:]
    if end_period:
        s = s.rstrip('.,;: ') + '.'
    return s.rstrip('.,;: ') if not end_period else s


def text_nodes(p):
    """Ordered text-bearing nodes in a paragraph: ('run'|'link', element, text)."""
    nodes = []
    for ch in p._p:
        tag = ch.tag
        if tag == W + 'r':
            ts = ch.findall(W + 't')
            if ts:
                nodes.append(('run', ch, ''.join(t.text or '' for t in ts)))
        elif tag == W + 'hyperlink':
            ts = ch.findall('.//' + W + 't')
            if ts:
                nodes.append(('link', ch, ''.join(t.text or '' for t in ts)))
    return nodes


def set_node_text(el, new):
    ts = el.findall('.//' + W + 't')
    ts[0].text = new
    ts[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    for extra in ts[1:]:
        extra.text = ''


# ---------------------------------------------------------------- overrides
# index -> list of replacements, one per text-bearing node. None = auto-lorem.
KEEP = '\x00KEEP\x00'

CV_OVERRIDES = {
    0:  ['FIRSTNAME LASTNAME'],
    1:  ['City, ST  |  first.last@example.com  |  ', 'LinkedIn',
         '  |  GitHub: ', 'username', '  |  Work Authorization'],
    2:  [KEEP],                                            # SUMMARY
    4:  [KEEP],                                            # CORE COMPETENCIES
    6:  [KEEP],                                            # PROFESSIONAL EXPERIENCE
    38: [KEEP],                                            # EDUCATION
    43: [KEEP],                                            # ADDITIONAL
    # --- experience: role line (title, date) + company line ---
    7:  ['Most Recent Role Title, Scope or Product Area', 'Jan 2023 - Dec 2025'],
    8:  ['Company One', ' (parenthetical descriptor)   City, ST'],
    12: ['Previous Role Title, Scope or Product Area', 'Mar 2021 - Dec 2022'],
    13: ['Company Two, short descriptor of the company   City, ST'],
    17: ['Previous Role Title, Scope or Product Area', 'Jun 2019 - Feb 2021'],
    18: ['Company Three, ', 'Named Program', '   City, ST'],
    21: ['Previous Role Title, Scope or Product Area', '2017 - May 2019'],
    22: ['Company Four   City, ST'],
    25: ['Previous Role Title / Second Function / Third Function', '2015 - 2017'],
    26: ['Company Five   City, ST'],
    28: ['Earlier Role Title / Second Title', '2013 - 2015'],
    29: ['Company Six   City, ST'],
    32: ['Earlier Role Title, Employee #1', 'Aug 2011 - Jul 2013'],
    33: ['Company Seven, short descriptor of the company   City, Country'],
    35: ['Earliest Role Title, Function and Area', 'Jul 2009 - Aug 2011'],
    36: ['Company Eight, short descriptor of the company   City, Country'],
    # --- education ---
    39: ['Graduate School or University Name', 'Jun 2015'],
    40: ['Degree  |  GPA 0.0/0.0  |  Honors or Distinction', 'City, ST'],
    41: ['Undergraduate University Name', 'Jul 2009'],
    42: ['B.S. Field of Study and Second Field  |  GPA 0.0/0.0', 'City, Country'],
    # --- additional: bold label + body ---
    44: ['Category One:', None, None, None, None, ' v1.0).'],
    45: ['Category Two: ', None, ' Sub-Category Label: ', None],
    46: ['Category Three: ', None],
    47: ['Category Four:', None, None, None, None, None],
}

COVER_LETTER_OVERRIDES = {
    0:  ['FIRSTNAME LASTNAME'],
    1:  ['City, ST  |  ', 'first.last@example.com', '  |  ', 'LinkedIn',
         '  |  Work Authorization'],
    2:  ['Month DD, YYYY'],
    3:  [KEEP],                                            # Hiring Team
    4:  ['Company Name'],
    5:  [KEEP],                                            # Dear Hiring Team,
    9:  [KEEP],                                            # Best regards,
    10: ['Firstname Lastname'],
}

MAPS = {'cv': CV_OVERRIDES, 'cover_letter': COVER_LETTER_OVERRIDES}
OVERRIDES = MAPS[MAP]

# Core competencies line: same pipe-separated shape, generic labels.
COMPETENCIES = ('Competency Area One  |  Competency Area Two  |  Competency Area Three  |  '
                'Competency Area Four  |  Competency Area Five  |  Competency Area Six  |  '
                'Competency Area Seven  |  Competency Area Eight  |  Competency Area Nine  |  '
                'Competency Area Ten  |  Competency Area Eleven  |  Competency Area Twelve')

GLUE = re.compile(r'^[\s\W\d]*$')          # punctuation/space-only nodes are kept verbatim

doc = Document(DST)
for i, p in enumerate(doc.paragraphs):
    nodes = text_nodes(p)
    if not nodes:
        continue
    if MAP == 'cv' and i == 5:
        set_node_text(nodes[0][1], COMPETENCIES)
        continue
    ov = OVERRIDES.get(i)
    for j, (kind, el, txt) in enumerate(nodes):
        rep = ov[j] if ov and j < len(ov) else None
        if rep == KEEP:
            continue
        if rep is None:
            if kind == 'link':
                set_node_text(el, 'Reference Link')
                continue
            m = re.match(r'^([\s\W]*)(.*?)([\s\W]*)$', txt, re.S)
            pre, core, post = m.groups()
            if len(core) < 8:
                continue                                    # glue: ") ", ", and ", "."
            rep = pre + lorem(len(core), capitalize=(j == 0), end_period=False) + post
        set_node_text(el, rep)

doc.save(DST)

# ------------------------------------------------- neutralize hyperlink targets
GENERIC = {
    'linkedin.com': 'https://www.linkedin.com/in/username/',
    'github.com': 'https://github.com/username',
}
zin = zipfile.ZipFile(SRC)
rels = zin.read('word/_rels/document.xml.rels').decode()


def swap(m):
    url = m.group(1)
    if url.lower().startswith('mailto:'):
        return 'Target="mailto:first.last@example.com"'
    for key, gen in GENERIC.items():
        if key in url:
            return 'Target="%s"' % gen
    return 'Target="https://example.com/reference"'


new_rels = re.sub(r'Target="((?:https?://|mailto:)[^"]+)"', swap, rels)

tmp = DST + '.tmp'
zsrc = zipfile.ZipFile(DST)
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
    for item in zsrc.infolist():
        data = zsrc.read(item.filename)
        if item.filename == 'word/_rels/document.xml.rels':
            data = new_rels.encode()
        elif item.filename == 'docProps/core.xml':
            data = re.sub(r'<dc:creator>[^<]*</dc:creator>', '<dc:creator>Template</dc:creator>',
                          data.decode())
            data = re.sub(r'<cp:lastModifiedBy>[^<]*</cp:lastModifiedBy>',
                          '<cp:lastModifiedBy>Template</cp:lastModifiedBy>', data).encode()
        zout.writestr(item, data)
zsrc.close()
shutil.move(tmp, DST)
print('wrote', DST)
