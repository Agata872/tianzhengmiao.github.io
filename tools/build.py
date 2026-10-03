"""Build a complete, dependency-free static site from data/site.json."""
from datetime import date
from html import escape
from pathlib import Path
from string import Template
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/site.json').read_text(encoding='utf-8'))
BASE = Template((ROOT / 'templates/base.html').read_text(encoding='utf-8'))
PROFILE = DATA['profile']
PROJECTS = {project['id']: project for project in DATA['projects']}


def e(value):
    return escape(str(value), quote=True)


def rich(text):
    """Escape text, then turn [label](https://...) into links."""
    def anchor(match):
        label, url = match.groups()
        css = '' if ' ' in label else ' class="nobreak"'  # keep one-word names such as IS-Wireless on a single line
        return f'<a{css} href="{url}">{label}</a>'
    return re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', anchor, e(text))


# Technical terms that should not wrap at their hyphen or dash.
TERMS = re.compile(r'\b(?:AI-RAN|O-RAN|IS-Wireless|EMPOWER-6G|DU–RU|AP–user|(?:[Ll]ow|[Hh]igh)-PHY)\b')


def keep_together(html):
    """Wrap TERMS in nowrap spans in text nodes only (never inside tags or inline SVG)."""
    parts = re.split(r'(<svg.*?</svg>|<[^>]+>)', html, flags=re.DOTALL)
    return ''.join(part if part.startswith('<') else TERMS.sub(lambda m: f'<span class="nobreak">{m.group(0)}</span>', part) for part in parts)


def link(url, label):
    return f'<a href="{e(url)}">{label}</a>'


def page_head(title, lead='', crumb=None):
    back = f'<p class="crumb"><a href="{crumb[0]}">← {e(crumb[1])}</a></p>' if crumb else ''
    intro = f'<p class="lead">{lead}</p>' if lead else ''
    return f'<header class="page-head">{back}<h1>{title}</h1>{intro}</header>'


# Interactive schematic: ceiling-mounted APs and users (system model) or the bipartite graph used by the GNN.
NETWORK = {
    'scale': 170,
    'bounds': [36, 185, 604, 338],
    'anchor': [13, -13],
    'system': {'aps': [[70 + 100 * i, 128] for i in range(6)], 'users': [[140, 270], [330, 235], [500, 290]]},
    'graph': {'aps': [[70 + 100 * i, 100] for i in range(6)], 'users': [[170, 290], [320, 290], [470, 290]]},
}
AP_GLYPH = '<path d="M-8-12a9 9 0 0 0 0 11M8-12a9 9 0 0 1 0 11M-13-15a15 15 0 0 0 0 17M13-15a15 15 0 0 1 0 17"/><circle cy="-6" r="3.5"/><path d="M-6 14 0-2 6 14 0 10Z"/>'
USER_GLYPH = '<path d="M0-10V9"/><circle cy="-12.5" r="2.6"/><ellipse cy="11" rx="8" ry="3"/>'
NETWORK_TEXT = {
    'system': 'Drag a user, or focus it and use the arrow keys: the channels H change, shown here as line weight. Select a node to highlight its links.',
    'graph': 'Every AP–user wireless link is an edge of the bipartite graph. Select a node to see its edges, or step through the layers.',
}


def link_weight(ap, user):
    return 1 / (1 + (math.hypot(ap[0] - user[0], ap[1] - user[1]) / NETWORK['scale']) ** 2)


def network_figure(number, view='system'):
    pos = NETWORK[view]
    links = ''
    blend = 1 if view == 'system' else 0  # links attach to the icons in the system view and to the node centres in the graph view
    for m, ap in enumerate(pos['aps']):
        for k, user in enumerate(pos['users']):
            w = link_weight(ap, user)
            links += f'<line class="link" data-m="{m}" data-k="{k}" x1="{ap[0]}" y1="{ap[1] + NETWORK['anchor'][0] * blend}" x2="{user[0]}" y2="{user[1] + NETWORK['anchor'][1] * blend}" style="stroke-width:{.5 + 2 * w:.2f};opacity:{.1 + .8 * w:.2f}"/>'
    sys_aps = NETWORK['system']['aps']
    fronthaul = f'<path d="M320 50V84M{sys_aps[0][0]} 84H{sys_aps[-1][0]}' + ''.join(f'M{x} 84V108' for x, _ in sys_aps) + '"/>'
    nn_in, nn_mid, nn_out = [(412, 25), (412, 41)], [(434, 17), (434, 33), (434, 49)], [(456, 33)]
    nn_edges = ''.join(f'M{a[0]} {a[1]}L{b[0]} {b[1]}' for left, right in ((nn_in, nn_mid), (nn_mid, nn_out)) for a in left for b in right)
    nn_nodes = ''.join(f'<circle cx="{x}" cy="{y}" r="4.5"' + (' class="fill"' if (x, y) in nn_in else '') + '/>' for x, y in nn_in + nn_mid + nn_out)
    ap_nodes = ''.join(f'<g class="node ap" data-m="{i}" transform="translate({x} {y})"><circle class="hit" r="28"/><g class="glyph">{AP_GLYPH}</g><g class="disc"><circle r="19"/><text y="4"><tspan class="ix">m</tspan> = {i + 1}</text></g><text class="node-label ap-label" x="20" y="-2">AP {i + 1}</text></g>' for i, (x, y) in enumerate(pos['aps']))
    user_nodes = ''.join(f'<g class="node user" data-k="{k}" transform="translate({x} {y})"><circle class="hit" r="28"/><g class="glyph">{USER_GLYPH}</g><g class="disc"><circle r="19"/><text y="4"><tspan class="ix">k</tspan> = {k + 1}</text></g><text class="node-label" y="32">User {k + 1}</text></g>' for k, (x, y) in enumerate(pos['users']))
    layout = e(json.dumps(NETWORK, separators=(',', ':')))
    caption = (f'<strong>Figure {number}.</strong> Schematic of a cell-free massive MIMO network with M = {len(sys_aps)} ceiling-mounted access points (APs) and '
               f'K = {len(NETWORK["system"]["users"])} users. The APs are connected to a central processing unit (CPU) over the fronthaul, and the CPU maps the channel matrix <strong>H</strong> to the precoder <strong>W</strong>. '
               'The bipartite-graph view shows the same network as the GNN sees it, with one edge per AP–user wireless link. Line weights are illustrative, not measured. <span class="nojs-note">The interactive views need JavaScript.</span>')
    pressed_system = 'true' if view == 'system' else 'false'
    pressed_graph = 'true' if view == 'graph' else 'false'
    return f"""<figure class="network-figure" data-network data-view="{view}" data-step="0" data-layout="{layout}">
      <svg class="network-svg" viewBox="0 0 640 380" role="group" aria-labelledby="net-title net-desc"><title id="net-title">Cell-free massive MIMO network and its bipartite graph</title><desc id="net-desc">Six ceiling-mounted access points are linked to three users by wireless links and to a CPU by the fronthaul. The CPU maps the channel matrix H to the precoder W. The graph view redraws the same network as a bipartite graph with access points on one side and users on the other.</desc>
        <g class="sys-only"><path class="floor" d="M30 350H610"/><g class="fronthaul">{fronthaul}</g><rect class="cpu" x="272" y="14" width="96" height="36" rx="2"/><text class="cpu-label" x="320" y="37">CPU</text><text class="matrix" x="384" y="38">H</text><g class="nn"><path d="{nn_edges}"/>{nn_nodes}</g><text class="matrix" x="478" y="38">W</text>
          <g class="legend"><path d="M36 369h30" class="fronthaul-key"/><text x="74" y="373">fronthaul</text><path d="M160 369h30" class="link-key"/><text x="198" y="373">wireless link</text></g></g>
        <g class="graph-only"><text class="row-label" x="320" y="52">Access points <tspan class="ix">m</tspan> = 1, …, <tspan class="ix">M</tspan></text><text class="row-label" x="320" y="344">Users <tspan class="ix">k</tspan> = 1, …, <tspan class="ix">K</tspan></text>
          <g class="badge badge-h"><text x="20" y="200">H</text><path d="M34 196h16m-5-4 5 4-5 4"/></g><g class="badge badge-w"><path d="M590 196h16m-5-4 5 4-5 4"/><text x="614" y="200">W</text></g></g>
        <g class="links">{links}</g><g class="aps">{ap_nodes}</g><g class="users">{user_nodes}</g></svg>
      <div class="net-controls"><div class="net-views" role="group" aria-label="Choose a view"><button type="button" data-view-btn="system" aria-pressed="{pressed_system}">System model</button><button type="button" data-view-btn="graph" aria-pressed="{pressed_graph}">Bipartite graph</button></div><button type="button" class="net-step" data-advance disabled>Step through the layers ▸</button></div>
      <p class="net-readout" role="status" aria-live="polite" data-readout>{e(NETWORK_TEXT[view])}</p>
      <figcaption>{caption}</figcaption>
    </figure>"""


def bibtex(pub):
    entry_type = 'article' if pub['type'].lower() == 'journal' else 'inproceedings'
    venue_field = 'journal' if entry_type == 'article' else 'booktitle'
    fields = {'title': pub['title'], 'author': ' and '.join(pub['authors']), venue_field: pub.get(venue_field, pub['venue']), 'year': pub['year']}
    if pub.get('pages'):
        fields['pages'] = pub['pages']
    if pub.get('doi'):
        fields['doi'] = pub['doi']
    fields['url'] = pub['url']
    return '@' + entry_type + '{miao' + pub['id'].replace('-', '') + ',\n' + ',\n'.join(f'  {k} = {{{v}}}' for k, v in fields.items()) + '\n}'


def publication_item(pub):
    authors = ', '.join(f'<strong>{e(a)}</strong>' if a == PROFILE['name'] else e(a) for a in pub['authors'])
    venue = pub.get('booktitle', pub['venue'])
    where = f'<em>{e(venue)}</em>'
    if pub.get('pages'):
        where += ', pp. ' + e(pub['pages'].replace('--', '–'))
    where += f', {pub["year"]}.'
    if pub.get('doi') and not pub['doi'].startswith('10.48550/'):  # arXiv DOIs are linked as "arXiv" instead
        where += f' doi: {link("https://doi.org/" + pub["doi"], e(pub["doi"]))}.'
    links = [link(pub['url'], 'Paper')]
    if pub.get('preprint'):
        links.append(link(pub['preprint'], 'arXiv'))
    if pub.get('project'):
        links.append(link(pub['project'], 'Project page'))
    bib = f'<details class="bibtex"><summary>BibTeX</summary><pre><code>{e(bibtex(pub))}</code></pre><a href="citations/{e(pub["id"])}.bib" download>Download .bib</a></details>'
    return f'''<li class="publication"><p class="pub-title">{link(pub['url'], e(pub['title']))}</p><p class="pub-authors">{authors}</p><p class="pub-venue">{where}</p><div class="pub-links">{''.join(links)}{bib}</div></li>'''


def publication_list(limit=None, project_ids=None, group_by_year=False):
    papers = sorted(DATA['publications'], key=lambda p: p['year'], reverse=True)
    if project_ids is not None:
        papers = [p for p in papers if p.get('project') in project_ids]
    if limit is not None:
        papers = papers[:limit]
    if not group_by_year:
        return '<ul class="publication-list">' + ''.join(publication_item(p) for p in papers) + '</ul>'
    result = ''
    for year in sorted({p['year'] for p in papers}, reverse=True):
        items = ''.join(publication_item(p) for p in papers if p['year'] == year)
        result += f'<section class="year-group" id="y{year}"><h2>{year}</h2><ul class="publication-list">{items}</ul></section>'
    return result


def timeline(rows):
    """rows: (label, html) pairs rendered as an aligned two-column list."""
    return '<dl class="timeline">' + ''.join(f'<dt>{e(label)}</dt><dd>{body}</dd>' for label, body in rows) + '</dl>'


def education():
    rows = []
    for item in DATA['education']:
        body = f'<strong>{e(item["title"])}</strong><br>{e(item["institution"])}'
        if item.get('detail'):
            body += f'<br><span class="muted">{e(item["detail"])}</span>'
        if item.get('supervisor'):
            body += '<br><span class="muted">Supervisor: ' + link(item['url'], e(item['supervisor'])) + '</span>'
        rows.append((item['year'], body))
    return timeline(rows)


def experience():
    rows = []
    for item in DATA['experience']:
        place = link(item['url'], e(item['institution'])) if item.get('url') else e(item['institution'])
        body = f'<strong>{e(item["title"])}</strong><br>{place}'
        if item.get('detail'):
            body += f'<br><span class="muted">{e(item["detail"])}</span>'
        rows.append((item['year'], body))
    return timeline(rows)


def awards_rows():
    return timeline([(a['year'], f'<strong>{e(a["title"])}</strong><br><span class="muted">{e(a["event"])}</span>') for a in DATA['awards']])


def home():
    p = PROFILE
    email = e(p['email'])
    about = ''.join(f'<p>{rich(text)}</p>' for text in p['about'])
    perspective = ''.join(f'<p>{e(text)}</p>' for text in p['perspective'])
    interests = ''.join(f'<li>{e(item)}</li>' for item in p['interests'])
    research = ''.join(f'<li><h3>{link(x["slug"], e(x["title"]))}</h3><p>{e(x["summary"])}</p></li>' for x in DATA['projects'])
    return f'''<section class="profile">
      <div class="profile-text"><h1>{e(p['name'])} <span class="name-zh" lang="zh-CN">{e(p['name_zh'])}</span></h1>
      <p class="position">{e(p['position'])}<br>{e(p['department'])}<br>{e(p['institution'])}</p>
      <p class="secondment">{rich(p['secondment'])}</p>
      <p class="address">{e(p['address'])}<br>Email: <a href="mailto:{email}">{email}</a></p></div>
      <img class="portrait" src="{e(p['portrait'])}" alt="Portrait of {e(p['name'])}" width="1280" height="1706">
    </section>
    <section class="block" id="about"><h2>About</h2>{about}</section>
    <section class="block" id="perspective"><h2>Research Perspective</h2>{perspective}</section>
    <section class="block" id="interests"><h2>Research Interests</h2><p>{e(p['interests_intro'])}</p><ul>{interests}</ul></section>
    <section class="block" id="research"><h2>Research</h2><ul class="research-list">{research}</ul></section>
    <section class="block" id="publications"><h2>Selected Publications</h2>{publication_list(limit=5)}<p class="more">{link('publication.html', 'All publications →')}</p></section>
    <section class="block" id="experience"><h2>Experience</h2>{experience()}</section>
    <section class="block" id="education"><h2>Education</h2>{education()}</section>
    <section class="block" id="awards"><h2>Awards</h2>{awards_rows()}</section>
    <section class="block" id="contact"><h2>Contact</h2><p>{e(p['contact_note'])}</p><p><a href="mailto:{email}">{email}</a></p></section>'''


def publications():
    lead = f'Peer-reviewed papers, with links to the publisher or arXiv and a BibTeX record for each. My name is shown in <strong>bold</strong>.'
    return page_head('Publications', lead) + publication_list(group_by_year=True)


def services():
    content = page_head('Professional Service')
    for group in DATA['services']:
        items = group['items']
        if all(item.get('year') for item in items):
            rows = [(item['year'], e(item['title']) + (f'<br><span class="muted">{e(item["detail"])}</span>' if item.get('detail') else '')) for item in items]
            body = timeline(rows)
        else:
            body = '<ul>' + ''.join(f'<li>{e(item["title"])}</li>' for item in items) + '</ul>'
        content += f'<section class="block"><h2>{e(group["role"])}</h2>{body}</section>'
    return content


def awards():
    return page_head('Awards', crumb=('index.html#awards', 'Home')) + f'<section class="block">{awards_rows()}</section>'


def figure(number, image, preview, alt, caption):
    return f'<figure><a href="{e(image)}"><img src="{e(preview)}" alt="{e(alt)}" loading="lazy"></a><figcaption><strong>Figure {number}.</strong> {e(caption)}</figcaption></figure>'


def cellfree():
    p = PROJECTS['cellfree']
    content = page_head(e(p['title']), e(p['summary']), crumb=('index.html#research', 'Research'))
    content += '<p class="keywords"><strong>Keywords:</strong> cell-free massive MIMO, graph neural networks, transfer learning, real-world CSI</p>'
    content += '<section class="block"><h2>Overview</h2><p>Cell-free massive MIMO brings distributed access points together to serve users. My work explores learning-based precoding, transfer learning, and validation with real channel measurements.</p>'
    content += network_figure(1, 'system')
    content += figure(2, p['image'], p.get('preview', p['image']), p['image_alt'], 'The Techtile testbed with ceiling-mounted distributed access points and a mobile user.') + '</section>'
    content += f'<section class="block"><h2>Featured Study</h2><p>{link("cellfree-gnn.html", e(DATA["gnn"]["title"]))}<br><span class="muted">Training on synthetic channels, adapting to real measurements. The page covers the system model, architecture, testbed, results, and dataset.</span></p></section>'
    content += '<section class="block"><h2>Related Publications</h2>' + publication_list(project_ids=['cellfree.html', 'cellfree-gnn.html']) + '</section>'
    return content


def gnn():
    g = DATA['gnn']
    content = page_head(e(g['title']), e(g['overview']), crumb=('cellfree.html', 'AI-driven signal processing in distributed MIMO'))
    results = ''.join(f'<li>{e(item)}</li>' for item in g['results'])
    content += f'<section class="block"><h2>Key Results</h2><ul>{results}</ul><p>{link(g["dataset_url"], "Download the dataset")} <span class="muted">(original measurements from the Techtile testbed)</span></p></section>'
    content += '<section class="block" id="overview"><h2>Interactive Overview</h2>' + network_figure(1, 'graph') + '</section>'
    for number, f in enumerate(g['figures'], 2):
        content += f'<section class="block" id="{e(f["id"])}"><h2>{e(f["title"])}</h2>{figure(number, f["image"], f.get("preview", f["image"]), f["alt"], f["caption"])}</section>'
    content += '<section class="block" id="publication"><h2>Publication</h2>' + publication_list(project_ids=['cellfree-gnn.html']) + '</section>'
    return content


def compress():
    p = PROJECTS['compress']
    content = page_head(e(p['title']), e(p['summary']), crumb=('index.html#research', 'Research'))
    questions = ''.join(f'<li>{e(q)}</li>' for q in DATA['compression_questions'])
    content += '<section class="block"><h2>Background</h2><p>Distributed wireless systems connect many access points and processing units. Moving radio information between them puts communication capacity and computation in the same design picture.</p><p>This research area explores efficient fronthaul compression for distributed wireless network architectures. It complements my work on cell-free networking and physical-layer signal processing, where coordination and computational cost both matter.</p></section>'
    content += f'<section class="block"><h2>Questions I Am Exploring</h2><ol>{questions}</ol></section>'
    content += f'<section class="block"><h2>Related Work</h2><p>See also {link("cellfree.html", "AI-driven signal processing in cell-free massive MIMO")}, {link("oran.html", "AI-RAN and O-RAN: DU–RU cooperation")}, and my {link("publication.html", "publications")}.</p></section>'
    return content


# Protocol stack covered by the O-RAN direction: (label, part of the core scope?), top to bottom.
STACK = [('RRC', False), ('PDCP', False), ('RLC', True), ('MAC', True), ('High-PHY', True), ('Low-PHY', True)]


def protocol_stack_figure(number):
    x, w, h, gap, top = 190, 170, 34, 8, 16
    top_of = lambda i: top + i * (h + gap)
    bottom_of = lambda i: top_of(i) + h
    boxes = ''.join(f'<g class="layer{"" if core else " extension"}"><rect x="{x}" y="{top_of(i)}" width="{w}" height="{h}" rx="2"/><text x="{x + w // 2}" y="{top_of(i) + 22}">{label}</text></g>' for i, (label, core) in enumerate(STACK))

    def left(first, last, label):
        y1, y2 = top_of(first), bottom_of(last)
        return f'<path class="bracket" d="M{x - 8} {y1}h-7V{y2}h7"/><text class="side-label" x="160" y="{(y1 + y2) // 2 + 5}">{label}</text>'

    def right(first, last, lines, dashed=False):
        y1, y2 = top_of(first), bottom_of(last)
        mid = (y1 + y2) // 2
        text = ''.join(f'<tspan x="392" y="{mid + 5 + (i - (len(lines) - 1) / 2) * 20:.0f}">{line}</tspan>' for i, line in enumerate(lines))
        return f'<path class="bracket{" dashed" if dashed else ""}" d="M{x + w + 8} {y1}h7V{y2}h-7"/><text class="note">{text}</text>'

    brackets = left(0, 0, 'Layer 3') + left(1, 3, 'Layer 2') + left(4, 5, 'Layer 1') + right(2, 5, ['Core scope', 'of the secondment']) + right(0, 1, ['Possible', 'extension'], dashed=True)
    return f"""<figure><svg class="stack-svg" viewBox="0 0 600 282" role="img" aria-labelledby="stack-title stack-desc"><title id="stack-title">Protocol-stack layers covered by the research</title><desc id="stack-desc">From top to bottom: RRC and PDCP, shown dashed as possible extensions, then RLC, MAC, high-PHY and low-PHY as the core scope. Low-PHY and high-PHY form Layer 1; MAC, RLC and PDCP belong to Layer 2; RRC to Layer 3.</desc>{boxes}{brackets}</svg><figcaption><strong>Figure {number}.</strong> Protocol-stack layers covered by this research direction. The core scope is low-PHY, high-PHY, MAC and RLC; PDCP and RRC (dashed) are possible extensions.</figcaption></figure>"""


def oran():
    p = PROJECTS['oran']
    content = page_head(e(p['title']), e(p['summary']), crumb=('index.html#research', 'Research'))
    content += '<p class="keywords"><strong>Keywords:</strong> AI-RAN, O-RAN, DU–RU cooperation, limited fronthaul, inter-user interference, protocol stack</p>'
    content += f'<section class="block"><h2>Context</h2><p>This research direction is pursued during my 18-month industrial secondment at {link(PROFILE["secondment_url"], "IS-Wireless")}, where I work as a Junior Research Engineer in the Research and Innovation Department. The secondment is part of the second phase of EMPOWER-6G, and the work is carried out in close collaboration with industry.</p></section>'
    content += '<section class="block"><h2>Problem</h2><p>In a disaggregated radio access network, processing is shared between distributed units (DUs) and radio units (RUs) that are connected by a fronthaul link. Two practical limits shape how well they can cooperate: the fronthaul has limited capacity, and users served in the same area interfere with each other. This work asks how DUs and RUs should cooperate under both limits.</p></section>'
    content += '<section class="block"><h2>From Layer 1 to Layers 1 and 2</h2><p>The work builds on the physical-layer signal-processing research of the first phase of my Ph.D., on cell-free networking and fronthaul compression, and extends its scope from Layer 1 to a joint view of Layers 1 and 2. It covers the low-PHY, high-PHY, MAC and RLC, and may extend to PDCP and RRC.</p>' + protocol_stack_figure(1) + '</section>'
    content += f'<section class="block"><h2>Related Work</h2><p>See also {link("cellfree.html", "AI-driven signal processing in cell-free massive MIMO")}, {link("compress.html", "efficient fronthaul compression")}, and my {link("publication.html", "publications")}.</p></section>'
    return content


def validate_data():
    for group, key in [('projects', 'id'), ('publications', 'id')]:
        ids = [item[key] for item in DATA[group]]
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate IDs in {group}')
    for image in [PROFILE['portrait'], *[p[k] for p in DATA['projects'] for k in ('image', 'preview') if p.get(k)], *[f[k] for f in DATA['gnn']['figures'] for k in ('image', 'preview') if f.get(k)]]:
        if not (ROOT / image).is_file():
            raise ValueError(f'Missing image: {image}')


def build():
    validate_data()
    name = PROFILE['name']
    pages = {
        'index.html': (f'{name} ({PROFILE["name_zh"]})', 'home-page', 'home', home),
        'publication.html': (f'Publications — {name}', 'list-page', 'publications', publications),
        'services.html': (f'Professional Service — {name}', 'list-page', 'service', services),
        'awards.html': (f'Awards — {name}', 'list-page', '', awards),
        'cellfree.html': (f'AI-Driven Signal Processing in Distributed MIMO — {name}', 'research-page', 'research', cellfree),
        'cellfree-gnn.html': (f'GNN-Based Precoding — {name}', 'research-page', 'research', gnn),
        'compress.html': (f'Fronthaul Compression — {name}', 'research-page', 'research', compress),
        'oran.html': (f'AI-RAN and O-RAN — {name}', 'research-page', 'research', oran),
    }
    descriptions = {
        'index.html': PROFILE['bio'],
        'publication.html': 'Publications by Tianzheng Miao on machine learning, distributed MIMO, and real-world wireless systems.',
        'services.html': 'Journal and conference peer review and technical program committee service by Tianzheng Miao.',
        'awards.html': 'Awards and academic milestones of Tianzheng Miao.',
        'cellfree.html': PROJECTS['cellfree']['summary'],
        'cellfree-gnn.html': DATA['gnn']['overview'],
        'compress.html': PROJECTS['compress']['summary'],
        'oran.html': PROJECTS['oran']['summary'],
    }
    nav_items = [('home', 'Home', 'index.html'), ('research', 'Research', 'index.html#research'), ('publications', 'Publications', 'publication.html'), ('service', 'Service', 'services.html')]
    today = date.today()
    for filename, (title, css, active, render) in pages.items():
        nav = ''.join(
            f'<a href="{href}"' + (' class="is-active"' if key == active else '') + (' aria-current="page"' if href == filename else '') + f'>{label}</a>'
            for key, label, href in nav_items
        )
        content = keep_together(render())
        scripts = '<script src="network.js?v=1" defer></script>' if 'data-network' in content else ''
        html = BASE.substitute(scripts=scripts, title=e(title), description=e(descriptions[filename]), body_class=css, navigation=nav, content=content, email=e(PROFILE['email']), name=e(name), location=e(PROFILE['location']), year=today.year, updated=today.strftime('%B %Y'))
        (ROOT / filename).write_text(html, encoding='utf-8', newline='\n')
        print(f'Built {filename}')
    (ROOT / 'citations').mkdir(exist_ok=True)
    for pub in DATA['publications']:
        (ROOT / 'citations' / f'{pub["id"]}.bib').write_text(bibtex(pub) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    build()
