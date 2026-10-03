"""Check local links, asset references, document structure, and generated output."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.references = []
        self.h1 = 0
        self.main = 0
        self.images_without_alt = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for attr in ('href', 'src'):
            if attrs.get(attr):
                self.references.append(attrs[attr])
        self.h1 += tag == 'h1'
        self.main += tag == 'main'
        self.images_without_alt += tag == 'img' and 'alt' not in attrs


def check():
    pages = {path: Page(path.read_text(encoding='utf-8')) for path in ROOT.glob('*.html')}
    problems = []
    for path, page in pages.items():
        if page.h1 != 1 or page.main != 1:
            problems.append(f'{path.name}: expected one h1 and one main')
        if page.images_without_alt:
            problems.append(f'{path.name}: image missing alt text')
        for name, count in Counter(page.ids).items():
            if count > 1:
                problems.append(f'{path.name}: duplicate id {name}')
        for reference in page.references:
            url = urlsplit(reference)
            if url.scheme or url.netloc:
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.is_file():
                problems.append(f'{path.name}: missing local target {reference}')
            elif url.fragment and target.suffix == '.html':
                target_page = pages.get(target)
                if target_page and unquote(url.fragment) not in target_page.ids:
                    problems.append(f'{path.name}: missing anchor {reference}')
    data = json.loads((ROOT / 'data/site.json').read_text(encoding='utf-8'))
    for paper in data['publications']:
        if not (ROOT / 'citations' / (paper['id'] + '.bib')).is_file():
            problems.append('Missing citation: ' + paper['id'])
    if problems:
        raise SystemExit('\n'.join(problems))
    print(f'Checked {len(pages)} pages: local links, anchors, assets, headings, image descriptions, and citations passed.')


if __name__ == '__main__':
    check()
