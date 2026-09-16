"""Check the hand-maintained option reference, examples, links and media claims."""
import argparse
import html
import json
from pathlib import Path
import re
import shlex
from urllib.parse import unquote, urlsplit

from PIL import Image

from yautja.cli import parser
from yautja.hud import BLUR_ELEMENTS, OPACITY_ELEMENTS
from yautja.presets import VISUAL_OPTIONS, NULLABLE
from .build_skill_bundle import ROOT, FILES

OPTION_FIELDS = ('Syntax', 'Values', 'Units', 'Default', 'Applies', 'Requires', 'Persistence', 'Example')
AUTOMATIC_DEFAULTS = {
    'help': 'Print help and exit when requested.', 'version': 'Print the installed version and exit when requested.',
    'palette_colors': 'No custom ramp; use the named palette.', 'look_preset': 'No recipe; --thermal classic with Yautja colors.',
    'preset_file': 'No saved settings loaded.', 'save_preset': 'No preset file written.',
    'save_preset_name': 'The output JSON filename stem.',
    'thermal_levels': 'Mode-specific quantization; specify --thermal-levels before using explicit grading controls.',
    'thermal_band_softness': '0.35 when explicit levels are enabled; inactive for continuous color.',
    'outline_width': 'Solid 2, shimmer 3, holographic 8 reference pixels.',
    'target_label': 'No caption.', 'hud_font_file': 'Use the bundled font selected by --hud-font.',
    'hud_colors': 'Standard colors for unspecified elements.', 'neon_elements': 'Every element inherits --neon-intensity.',
    'hud_blur_elements': 'Every element inherits --hud-blur.', 'hud_opacity_elements': 'Every element inherits --hud-opacity.',
    'pixelation': 'Off; --sensor-texture uses --sensor-resolution unless explicitly overridden.',
    'scanlines': 'On for the default Yautja thermal palette or --sensor-texture; otherwise off.',
    'figures': 'No figure catalog.', 'target_colors': 'Resolved target and flash HUD colors.',
    'target_stroke_colors': 'Darker shades of the resolved target colors.',
    'wave_display': 'LED for digital-circuit; plain for the other six styles.',
    'wave_width': '0.12 of frame width for non-trace styles; trace has fixed layout.',
    'wave_height': '0.96 of frame height for non-trace styles; trace has fixed layout.',
    'duration': 'Remaining source duration.', 'fps': 'Source frame rate; still images have one frame.',
    'grain': '0; --sensor-texture uses 0.035 unless explicitly overridden.',
}


def inventory():
    p = parser(); defaults = vars(p.parse_args([])); result = {}
    for action in p._actions:
        if not action.option_strings:
            continue
        record = result.setdefault(action.dest, {'flags': [], 'action': action, 'default': defaults.get(action.dest)})
        record['flags'].extend(action.option_strings)
    return result


def default_text(dest, record):
    return AUTOMATIC_DEFAULTS[dest] if record['default'] is None else json.dumps(record['default'], ensure_ascii=False)


def option_entries(text):
    result = {}
    for section in re.split(r'^#### ', text, flags=re.M)[1:]:
        name, _, body = section.partition('\n')
        fields = dict(re.findall(r'^- (\w+): (.+)$', body, re.M))
        if name in result:
            raise ValueError('Duplicate option heading: '+name)
        result[name] = fields
    return result


def recipes(paths=None):
    paths = paths or [ROOT/'README.md', ROOT/'skills/yautja/references/examples.md']
    result = {}
    for path in paths:
        text = path.read_text(encoding='utf-8')
        for match in re.finditer(r'<!-- example: (\{.*?\}) -->\s*```(?:bash|sh)\n(.*?)```', text, re.S):
            meta = json.loads(match[1]); commands = []
            for line in match[2].strip().splitlines():
                if line.strip() and not line.lstrip().startswith('#'):
                    commands.append(shlex.split(line))
            if meta['id'] in result:
                raise ValueError('Duplicate example ID: '+meta['id'])
            result[meta['id']] = {**meta, 'commands': commands, 'path': path}
    return result


def slug(text):
    text = re.sub(r'<[^>]+>', '', text).strip().lower()
    text = re.sub(r'[^\w\-\s]', '', text)
    return re.sub(r'\s', '-', text)


def anchors(text):
    found = set(re.findall(r'<a\s+(?:name|id)=["\']([^"\']+)', text))
    counts = {}
    # Fenced code can contain comments beginning with #; they aren't headings.
    prose = re.sub(r'^```.*?^```\s*$', '', text, flags=re.M|re.S)
    for name in re.findall(r'^#{1,6}\s+(.+)$', prose, re.M):
        base = slug(name); n = counts.get(base, 0); counts[base] = n+1
        found.add(base + ('-'+str(n) if n else ''))
    return found


def prose_warnings(text):
    """Flag likely revision narration for review, without rejecting ordinary prose."""
    def blank(match):
        return re.sub(r'[^\n]', ' ', match.group())

    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    lines, fence = [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
            lines.append('\n' if line.endswith('\n') else '')
        elif marker:
            fence = (marker[1][0], len(marker[1]))
            lines.append('\n' if line.endswith('\n') else '')
        else:
            lines.append(line)
    text = ''.join(lines)
    text = re.sub(r'(`+).*?\1', blank, text)
    text = re.sub(r'(?<=\]\()[^)]*|<[^>]*>|https?://[^\s<>]+', blank, text)
    pattern = re.compile(
        r'\bClassic\b|'
        r'(?i:\b(?:now|no longer)\s+(?:selects?|supports?|uses?|requires?|enables?|includes?)\b|'
        r'\b(?:new|older)\s+(?:options?|presets?|features?|flags?)\b|'
        r'\boriginal\s+(?:palette|look)\b|\b(?:old|previous)\s+(?:behavior|version)\b|'
        r'\balias(?:es)?\s+(?:remain|still)\b|\bexisting commands still work\b|'
        r'\bretain(?:s)?\s+(?:their|its|the)\s+\d+(?:\.\d+)?%|'
        r'\b(?:is|are)\s+(?:thinner|thicker)\b)')
    return [{'line': number, 'phrase': match.group(),
             'message': 'Review for revision history; describe current behavior.'}
            for number, line in enumerate(text.splitlines(), 1)
            for match in pattern.finditer(line)]


def local_url(url, source):
    url = html.unescape(url); split = urlsplit(url)
    if split.scheme in ('mailto','app'):
        return None, ''
    if not split.scheme:
        return (source.parent/unquote(split.path)).resolve() if split.path else source, unquote(split.fragment)
    prefix = '/petehottelet/yautja/'
    if split.hostname == 'raw.githubusercontent.com' and split.path.startswith(prefix+'main/'):
        return ROOT/unquote(split.path[len(prefix+'main/'):]), unquote(split.fragment)
    if split.hostname == 'github.com' and split.path.startswith(prefix):
        tail = split.path[len(prefix):]
        if tail.startswith(('blob/main/','tree/main/')):
            return ROOT/unquote(tail.split('/',2)[2]), unquote(split.fragment)
    if split.scheme not in ('http','https') or not split.netloc:
        raise ValueError('Malformed URL: '+url)
    return None, ''


def media_info(path):
    """Read GIF block headers without decompressing hundreds of preview frames."""
    if path.suffix.lower()!='.gif':
        with Image.open(path) as im: return {'width':im.width,'height':im.height,'frames':1}
    data=path.read_bytes()
    if data[:6] not in (b'GIF87a',b'GIF89a') or len(data)<13: raise ValueError('Invalid GIF header')
    def number(pos): return int.from_bytes(data[pos:pos+2],'little')
    result={'width':number(6),'height':number(8),'frames':0,'duration_ms':0}
    pos=13+(3*2**((data[10]&7)+1) if data[10]&128 else 0)
    delay=0
    def blocks(pos):
        while True:
            size=data[pos]; pos+=1
            if not size: return pos
            pos+=size
            if pos>=len(data): raise ValueError('Truncated GIF block')
    while pos<len(data):
        marker=data[pos]; pos+=1
        if marker==0x3b: return result
        if marker==0x21:
            extension=data[pos]; pos+=1
            if extension==0xf9: delay=number(pos+2)*10
            pos=blocks(pos)
        elif marker==0x2c:
            packed=data[pos+8]; pos+=9
            if packed&128: pos+=3*2**((packed&7)+1)
            pos=blocks(pos+1)
            result['frames']+=1; result['duration_ms']+=delay; delay=0
        else: raise ValueError('Invalid GIF block marker')
    raise ValueError('Missing GIF trailer')


def check(root=ROOT):
    errors=[]; items=inventory()
    text=(root/'skills/yautja/references/options.md').read_text(encoding='utf-8')
    entries=option_entries(text); examples=recipes()
    flags_to_dest={flag:dest for dest,record in items.items() for flag in record['flags']}
    covered={}
    for name, example in examples.items():
        used={flags_to_dest[token.split('=',1)[0]] for command in example['commands'] for token in command if token.split('=',1)[0] in flags_to_dest}
        covered[name]=used
    expected_names=set()
    for dest, record in items.items():
        name=record['flags'][0].lstrip('-'); expected_names.add(name)
        fields=entries.get(name,{})
        if set(fields)!=set(OPTION_FIELDS): errors.append(f'{name}: missing/unknown definition fields')
        documented=re.findall(r'(?<!\w)--?[A-Za-z][\w-]*', fields.get('Syntax',''))
        if set(documented)!=set(record['flags']): errors.append(f'{name}: spelling/alias drift')
        if fields.get('Default')!=default_text(dest,record): errors.append(f'{name}: default drift')
        if record['action'].choices is not None:
            listed=re.findall(r'`([^`]+)`',fields.get('Values',''))
            if set(listed)!=set(map(str,record['action'].choices)): errors.append(f'{name}: choices drift')
        expected='nullable' if dest in NULLABLE else 'saved' if dest in VISUAL_OPTIONS else 'runtime-only'
        if fields.get('Persistence')!=expected: errors.append(f'{name}: persistence drift')
        match=re.search(r'examples.md#([\w-]+)',fields.get('Example',''))
        if not match or dest not in covered.get(match[1],set()): errors.append(f'{name}: no executable example mapping')
    if set(entries)!=expected_names: errors.append('Option heading inventory differs: '+str(sorted(set(entries)^expected_names)))
    roles=(root/'skills/yautja/references/hud-elements.md').read_text(encoding='utf-8')
    rows=re.findall(r'^\| `([\w-]+)` \| (yes|shared target) \| (yes|no) \| (yes|no) \|',roles,re.M)
    if {r[0] for r in rows}!=set(OPACITY_ELEMENTS): errors.append('HUD role inventory drift')
    for key,blur,opacity,neon in rows:
        if (blur=='yes')!=(key in BLUR_ELEMENTS) or (neon=='yes')!=(key in BLUR_ELEMENTS) or opacity!='yes':
            errors.append('HUD capabilities drift: '+key)
    for required in ('references/options.md','references/examples.md','references/hud-elements.md'):
        if required not in FILES: errors.append('Skill manifest missing '+required)
    documents=[root/'README.md',root/'CHANGELOG.md',*sorted((root/'docs').glob('*.md')),
               root/'skills/yautja/SKILL.md',*sorted((root/'skills/yautja/references').glob('*.md'))]
    seen_media=set()
    for path in documents:
        content=path.read_text(encoding='utf-8')
        # Only real Markdown/HTML links, excluding literal CLI examples.
        urls=re.findall(r'\]\(([^\s)]+)(?:\s+"[^"]*")?\)',content)+re.findall(r'(?:src|href)="([^"]+)"',content)
        for url in urls:
            try: target, anchor=local_url(url,path)
            except ValueError as exc: errors.append(str(exc)); continue
            if target is None: continue
            if not target.exists(): errors.append(f'{path.relative_to(root)}: missing {url}'); continue
            if anchor and target.suffix=='.md' and anchor not in anchors(target.read_text(encoding='utf-8')):
                errors.append(f'{path.relative_to(root)}: missing anchor {url}')
            if target.suffix.lower() in ('.gif','.png'): seen_media.add(target.relative_to(root).as_posix())
    manifest=json.loads((root/'docs/media.json').read_text())
    if set(manifest)!=seen_media: errors.append('Media index differs from referenced GIF/PNG files')
    for relative, expected in manifest.items():
        try:
            actual=media_info(root/relative)
            if actual!=expected: errors.append('Media metadata drift: '+relative)
        except (OSError,ValueError) as exc: errors.append(f'{relative}: {exc}')
    # Machine-readable captions must agree with the same measured files.
    readme=(root/'README.md').read_text(encoding='utf-8')
    for data in re.findall(r'<!-- media: (\{.*?\}) -->',readme):
        claim=json.loads(data); relative=claim.pop('file')
        if any(manifest.get(relative,{}).get(k)!=v for k,v in claim.items()): errors.append('Incorrect README media claim: '+relative)
    return {'families':len(items),'spellings':len(flags_to_dest),'examples':len(examples),'media':len(manifest),
            'warnings':prose_warnings(readme),'errors':errors}


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    result=check(); print(json.dumps(result,indent=2)); return bool(result['errors'])


if __name__=='__main__': raise SystemExit(main())
