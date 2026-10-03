"""Build a complete, dependency-free static site from data/site.json."""
from datetime import date
from html import escape
from pathlib import Path
from string import Template
import json

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/site.json').read_text(encoding='utf-8'))
BASE = Template((ROOT / 'templates/base.html').read_text(encoding='utf-8'))
PROFILE = DATA['profile']


def e(value):
    return escape(str(value), quote=True)


def external(url, label, css='text-link'):
    return f'<a class="{css}" href="{e(url)}" target="_blank" rel="noopener noreferrer">{label} <span aria-hidden="true">↗</span></a>'


def tags(values):
    return ''.join(f'<span class="tag">{e(t)}</span>' for t in values)


def heading(number, label, title, link=''):
    return f'<div class="section-heading"><div><p class="eyebrow"><span>{number}</span> / {e(label)}</p><h2>{title}</h2></div>{link}</div>'


def intro(label, title, description):
    return f'<section class="page-intro container"><a class="back-link" href="index.html">← Back to home</a><p class="eyebrow">{e(label)}</p><h1>{title}</h1><p class="page-description">{e(description)}</p></section>'


def network():
    positions = [(70, 70), (180, 48), (310, 60), (420, 105), (75, 185), (210, 135), (385, 230), (150, 290), (290, 285)]
    lines = ''.join(f'<line class="signal-link" data-link="{i}" x1="{x}" y1="{y}" x2="250" y2="210"/>' for i, (x, y) in enumerate(positions))
    nodes = ''.join(f'<g class="access-point" data-node="{i}" data-x="{x}" data-y="{y}" role="button" tabindex="0" aria-label="Inspect access point {i + 1}" aria-pressed="false" transform="translate({x} {y})"><circle class="node-hit" r="22"/><circle class="node-ring" r="13"/><circle class="node-core" r="4"/><text x="18" y="-13">AP.{i + 1:02}</text></g>' for i, (x, y) in enumerate(positions))
    return f'''<figure class="network-panel" data-network>
      <div class="panel-topline"><span><span class="tiny-dot"></span> DISTRIBUTED NETWORK</span><span>FIG. 01</span></div>
      <div class="network-stage"><svg class="network-svg" viewBox="0 0 500 350" aria-labelledby="network-title network-description"><title id="network-title">Explore a cell-free wireless network</title><desc id="network-description">Nine access points connect to a mobile user. Move the user with the slider or pointer and select an access point to inspect its connection. This is a conceptual illustration.</desc><defs><pattern id="network-grid" width="25" height="25" patternUnits="userSpaceOnUse"><path d="M25 0H0V25" fill="none" stroke="currentColor" stroke-width=".5"/></pattern></defs><rect width="500" height="350" fill="url(#network-grid)" class="network-grid"/><path class="room-boundary" d="M35 25H455V320H35Z"/><g class="signal-links">{lines}</g>{nodes}<g class="mobile-user" transform="translate(250 210)"><circle class="user-aura" r="25"/><circle class="user-ring" r="11"/><circle class="user-core" r="4"/><text x="18" y="23">USER.01</text></g><text class="diagram-axis" x="35" y="341">x / SPACE</text><text class="diagram-axis" x="380" y="341">CELL-FREE MIMO</text></svg></div>
      <div class="network-legend"><span><i class="legend-ap"></i> Access point</span><span><i class="legend-user"></i> Mobile user</span><span class="schematic-label">Conceptual schematic</span></div>
      <div class="network-controls enhancement"><label for="user-position">MOVE THE USER</label><input id="user-position" type="range" min="0" max="100" value="50" aria-label="Mobile user position"><button class="icon-button" type="button" data-network-pause aria-label="Pause signal animation" aria-pressed="false">Ⅱ</button></div>
      <p class="network-readout" aria-live="polite">Shared coverage. Distributed intelligence.</p>
    </figure>'''


def fronthaul_art():
    return '''<div class="fronthaul-art" aria-label="Conceptual fronthaul architecture"><span class="art-label">SIGNAL PATH / FRONTHAUL</span><div class="architecture"><div class="ap-stack"><span>AP.01</span><span>AP.02</span><span>AP.03</span></div><span class="architecture-lines" aria-hidden="true">〉</span><div class="processing-node"><span class="tiny-dot"></span> COMPRESS<br><small>Distributed unit</small></div><span class="data-stream" aria-hidden="true"><i></i><i></i><i></i><i></i></span><div class="cpu-node">CPU<br><small>Central processor</small></div></div><div class="art-bottom"><span>I/Q SAMPLES → COMPACT REPRESENTATION</span><span aria-hidden="true">↗</span></div></div>'''


def project_cards():
    result = ''
    for i, project in enumerate(DATA['projects'], 1):
        if project.get('image'):
            art = f'<div class="project-photo"><img src="{e(project.get("preview", project["image"]))}" alt="{e(project["image_alt"])}" loading="lazy" width="3219" height="1565"><span class="photo-label">TECHTILE / REAL-WORLD TESTBED</span></div>'
        else:
            art = fronthaul_art()
        result += f'''<article class="project-card" data-filter-item data-categories="{e(' '.join(project['categories']))}">{art}<div class="project-copy"><p class="project-meta"><span>R.{i:02}</span> {e(project['category_label'])}</p><h3><a href="{e(project['slug'])}">{e(project['title'])}</a></h3><p>{e(project['summary'])}</p><a class="text-link" href="{e(project['slug'])}">Explore the research <span aria-hidden="true">↗</span></a></div></article>'''
    return result


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


def publication_rows(limit=None, project_ids=None):
    rows = ''
    papers = sorted(DATA['publications'], key=lambda p: p['year'], reverse=True)
    if project_ids is not None:
        papers = [p for p in papers if p.get('project') in project_ids]
    if limit is not None:
        papers = papers[:limit]
    for pub in papers:
        authors = ', '.join(f'<strong>{e(a)}</strong>' if a == PROFILE['name'] else e(a) for a in pub['authors'])
        citation_path = f'citations/{pub["id"]}.bib'
        links = external(pub['url'], 'Paper', 'small-link')
        if pub.get('preprint'):
            links += external(pub['preprint'], 'arXiv', 'small-link')
        if pub.get('project'):
            links += f'<a class="small-link" href="{e(pub["project"])}">Project ↗</a>'
        links += f'<button class="small-link cite-button enhancement" type="button" data-citation="{e(bibtex(pub))}" aria-label="Show BibTeX for {e(pub["title"])}">Cite <span aria-hidden="true">↗</span></button><a class="small-link bib-download" href="{citation_path}" download>BibTeX ↓</a>'
        rows += f'''<article class="publication-row" data-filter-item data-year="{pub['year']}" data-categories="{e(' '.join(pub.get('tags', [])))}"><div class="publication-year">{pub['year']}<span>{e(pub['type'])}</span></div><div class="publication-body"><p class="eyebrow publication-venue">{e(pub['venue'])} / {pub['year']}</p><h3>{external(pub['url'], e(pub['title']), 'paper-title')}</h3><p class="authors">{authors}</p><div class="paper-links">{links}</div></div><span class="publication-index" aria-hidden="true">↗</span></article>'''
    return rows


def filters(scope, choices, search=False, years=False):
    controls = f'<div class="filter-tabs" role="group" aria-label="Filter {scope}">' + ''.join(f'<button class="filter-button {"is-selected" if key == "all" else ""}" type="button" data-filter="{key}" aria-pressed="{"true" if key == "all" else "false"}">{e(label)}</button>' for key, label in choices) + '</div>'
    if search:
        controls = f'<label class="search-field"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg><span class="sr-only">Search {scope}</span><input type="search" data-search placeholder="Search {scope}…" autocomplete="off"></label>' + controls
    if years:
        options = ''.join(f'<option value="{y}">{y}</option>' for y in sorted({p['year'] for p in DATA['publications']}, reverse=True))
        controls += f'<label class="year-filter"><span class="sr-only">Publication year</span><select data-year-filter><option value="all">All years</option>{options}</select></label>'
    return f'<div class="filter-bar enhancement">{controls}</div><p class="filter-status sr-only" role="status" aria-live="polite"></p>'


def empty_state(label):
    return f'<div class="empty-state" hidden><span aria-hidden="true">⌕</span><h3>No matching {label}.</h3><p>Try another search or clear your filters.</p><button class="button button-outline" type="button" data-reset-filters>Clear filters</button></div>'


def education():
    rows = ''
    for item in DATA['education']:
        detail = e(item.get('detail', ''))
        if item.get('supervisor'):
            detail += ' Supervised by ' + external(item['url'], e(item['supervisor'])) + '.'
        rows += f'<article class="timeline-item"><span class="timeline-date">{e(item["year"])}</span><div><h3>{e(item["title"])}</h3><p class="timeline-institution">{e(item["institution"])}</p><p class="timeline-detail">{detail}</p></div></article>'
    return rows


def note_previews():
    return ''.join(f'<a class="note-preview" href="updates.html#{e(p["id"])}"><div class="note-preview-meta"><time datetime="{p["date"]}">{p["date"].replace("-", ".")}</time><span>{e(p["tags"][0])}</span></div><h3 lang="{e(p["lang"])}">{e(p["title"])}</h3><p lang="{e(p["lang"])}">{e(p["paragraphs"][0][:76])}…</p><span class="text-link">Read the note <span aria-hidden="true">↗</span></span></a>' for p in sorted(DATA['posts'], key=lambda p: p['date'], reverse=True)[:2])


def contact():
    email = e(PROFILE['email'])
    return f'''<section class="contact-section container" id="contact"><div class="contact-grid"><div><p class="eyebrow">NEXT CONNECTION / YOUR IDEA</p><h2>Good ideas start<br>with a conversation<span class="accent">.</span></h2><p>Wireless systems, machine learning, or something worth exploring together.</p></div><div class="contact-actions"><a class="button button-primary" href="mailto:{email}">Get in touch <span aria-hidden="true">↗</span></a><button class="copy-email enhancement" type="button" data-copy="{email}" aria-label="Copy email address">{email} <span aria-hidden="true">⧉</span></button></div></div></section>'''


def home():
    p = PROFILE
    intro_copy = e(p['bio'])
    return f'''<section class="hero container" id="about">
      <div class="hero-topline"><span>WIRELESS SYSTEMS × MACHINE LEARNING</span><span class="hero-coordinate">PERSONAL RESEARCH LAB / TM</span></div>
      <div class="hero-grid"><div class="hero-copy"><p class="hero-greeting">Hi, I’m <strong>{e(p['name'])}.</strong> <span lang="zh-CN">{e(p['name_zh'])}</span></p><h1>Intelligence,<br><span class="accent">connected.</span></h1><p class="hero-description">Building smarter wireless networks.<br>From learning algorithms to real-world experiments.</p><div class="hero-actions"><a class="button button-primary" href="#research">Explore my research <span aria-hidden="true">↘</span></a><a class="button button-outline" href="publication.html">Publications <span aria-hidden="true">↗</span></a></div><div class="hero-affiliation"><span class="status-dot" aria-hidden="true"></span><span>{e(p['role_short'])} <span class="muted">/</span> {e(p['institution'])}<br><small>{e(p['lab'])} · {e(p['location'])}</small></span></div></div>{network()}</div>
      <div class="hero-bottomline"><a href="#research"><span aria-hidden="true">↓</span> SCROLL TO EXPLORE</a><span>RESEARCH, WITH A REAL-WORLD SIGNAL.</span></div>
    </section>
    <section class="about-section container" aria-labelledby="about-title"><div class="portrait"><img src="{e(p['portrait'])}" alt="Portrait of {e(p['name'])}" width="1280" height="1706"><span class="portrait-label">THE HUMAN / TM</span></div><div class="about-copy"><p class="eyebrow">A LITTLE ABOUT ME</p><h2 id="about-title">Curiosity meets the physical world.</h2><p>{intro_copy}</p><p>I’m a {e(p['role_short'])} at <strong>{e(p['institution'])}</strong>, supervised by {external(p['supervisor_url'], 'Prof. ' + e(p['supervisor']))}. My work is part of {external(p['project_url'], 'EMPOWER-6G')}.</p><div class="interest-tags">{tags(['Cell-free massive MIMO', 'Graph neural networks', 'Wireless sensing'])}</div></div></section>
    <section class="section container" id="research">{heading('01', 'Research directions', 'Ideas. Algorithms. Experiments.', '<span class="section-aside">FROM THE MODEL TO THE TESTBED ↘</span>')}<div data-filter-scope="projects">{filters('projects', [('all', 'All research'), ('learning', 'AI & learning'), ('wireless', 'Wireless systems'), ('signal', 'Signal processing')])}<div class="project-grid">{project_cards()}</div>{empty_state('projects')}</div></section>
    <section class="section publication-section container" id="publications">{heading('02', 'Selected publications', 'Written. Tested. Shared.', '<a class="text-link" href="publication.html">All publications ↗</a>')}<div class="publication-list">{publication_rows(limit=3)}</div></section>
    <section class="section container" id="journey">{heading('03', 'The path so far', 'Always a little further.')}<div class="journey-grid"><div class="timeline">{education()}</div><aside class="community-panel"><div class="community-mark" aria-hidden="true">✳</div><p class="eyebrow">PART OF A BIGGER CONVERSATION</p><h3>Research is a<br>team effort.</h3><p>Contributing through peer review and technical program committees.</p><a class="text-link" href="services.html">Professional service ↗</a><a class="text-link" href="awards.html">Awards & milestones ↗</a></aside></div></section>
    <section class="section container" id="notes">{heading('04', 'Beyond the papers', 'Notes from the process.', '<a class="text-link" href="updates.html">All notes ↗</a>')}<div class="note-grid">{note_previews()}</div></section>{contact()}'''


def publications():
    return intro('RESEARCH OUTPUT / PUBLICATIONS', 'From ideas<br>to <span class="accent">published work.</span>', 'Papers on learning-based signal processing and distributed wireless systems. Explore the work, read a preprint, or grab a citation.') + f'''<section class="container archive-section" data-filter-scope="publications">{filters('publications', [('all', 'All topics'), ('learning', 'AI & learning'), ('wireless', 'Wireless systems')], search=True, years=True)}<div class="archive-summary"><span>PUBLICATION ARCHIVE</span><span data-result-count>{len(DATA['publications'])} papers</span></div><div class="publication-list">{publication_rows()}</div>{empty_state('publications')}</section>'''


def services():
    content = intro('COMMUNITY / PROFESSIONAL SERVICE', 'The conversation<br><span class="accent">continues.</span>', 'Supporting the research community through journal and conference peer review, and technical program committees.')
    content += '<section class="container service-section">'
    for i, group in enumerate(DATA['services'], 1):
        rows = ''.join(f'<li><span class="service-year">{e(item.get("year", "—"))}</span><div><h3>{e(item["title"])}</h3>' + (f'<p>{e(item["detail"])}</p>' if item.get('detail') else '') + '</div></li>' for item in group['items'])
        content += f'<section class="service-group"><div class="service-heading"><p class="eyebrow">S.{i:02} / {len(group["items"]):02} ENTRIES</p><h2>{e(group["role"])}</h2><p>{e(group["description"])}</p></div><ul class="service-list">{rows}</ul></section>'
    return content + '</section>'


def awards():
    content = intro('JOURNEY / AWARDS', 'Small milestones.<br><span class="accent">Lasting motivation.</span>', 'A few moments of recognition along the way, from mathematical modeling to innovation and entrepreneurship.')
    rows = ''.join(f'<article class="award-row"><span class="award-year">{a["year"]}</span><div><p class="eyebrow">RECOGNITION / {i:02}</p><h2>{e(a["title"])}</h2><p>{e(a["event"])}</p></div><span class="award-symbol" aria-hidden="true">✳</span></article>' for i, a in enumerate(DATA['awards'], 1))
    return content + f'<section class="container award-list">{rows}<a class="text-link" href="index.html#journey">Explore my academic journey ↗</a></section>'


def updates():
    content = intro('FIELD NOTES / UPDATES', 'A work in<br><span class="accent">progress.</span>', 'Research logs, small discoveries, and thoughts beyond the lab. Some in English, some in Chinese. All part of the process.')
    focus = ''.join(f'<li>{e(f)}</li>' for f in DATA['focus'])
    content += f'<section class="container notes-archive"><aside class="pinned-note"><div><p class="eyebrow"><span aria-hidden="true">↗</span> PINNED / CURRENT FOCUS</p><h2>On my radar.</h2></div><ul>{focus}</ul></aside><div data-filter-scope="notes">'
    choices = [('all', 'All notes')] + [(tag, tag.capitalize()) for tag in sorted({tag for p in DATA['posts'] for tag in p['tags']})]
    content += filters('notes', choices, search=True)
    content += f'<div class="archive-summary"><span>NOTES / LATEST FIRST</span><span data-result-count>{len(DATA["posts"])} notes</span></div><div class="posts">'
    for p in sorted(DATA['posts'], key=lambda p: p['date'], reverse=True):
        paragraphs = ''.join(f'<p>{e(text)}</p>' for text in p['paragraphs'])
        content += f'''<article class="post" id="{e(p['id'])}" data-filter-item data-categories="{e(' '.join(p['tags']))}"><div class="post-meta"><time datetime="{e(p['date'])}">{p['date'].replace('-', '.')}</time><div>{tags(p['tags'])}</div><a class="post-permalink" href="#{e(p['id'])}" aria-label="Permanent link to {e(p['title'])}">#</a></div><details><summary><h2 lang="{e(p['lang'])}">{e(p['title'])}</h2><p class="post-excerpt" lang="{e(p['lang'])}">{e(p['paragraphs'][0][:100])}…</p><span class="post-expand"><span class="read-label">Read note</span><span class="close-label">Close note</span> <span aria-hidden="true">+</span></span></summary><div class="post-body" lang="{e(p['lang'])}">{paragraphs}</div></details></article>'''
    return content + '</div>' + empty_state('notes') + '</div></section>'


def cellfree():
    p = DATA['projects'][0]
    content = intro('RESEARCH / DISTRIBUTED MIMO', 'Intelligence at<br><span class="accent">the physical layer.</span>', p['summary'])
    content += f'''<section class="container research-overview"><div class="research-context"><p class="eyebrow">RESEARCH DIRECTION / R.01</p><h2>A network that learns<br>from the real world.</h2><p>Cell-free massive MIMO brings distributed access points together to serve users. My work explores learning-based precoding, transfer learning, and validation with real channel measurements.</p><div class="interest-tags">{tags(['Cell-free MIMO', 'Transfer learning', 'Real-world CSI'])}</div></div><figure class="testbed-figure"><img src="{e(p.get('preview', p['image']))}" alt="Techtile distributed MIMO testbed" width="3219" height="1565" loading="lazy"><figcaption>Techtile / connecting algorithms to hardware.</figcaption></figure></section><section class="container section">{heading('01', 'Featured study', 'GNN-based precoding.')}<a class="study-link" href="cellfree-gnn.html"><div><p class="eyebrow">2025 / REAL-WORLD CSI</p><h3>GNN-based Precoder Design and Fine-tuning</h3><p>Training on synthetic channels. Adapting to real measurements. Explore the architecture, dataset, and results.</p></div><span aria-hidden="true">↗</span></a></section><section class="container section">{heading('02', 'Related publications', 'Evidence from the testbed.')}<div class="publication-list">{publication_rows(project_ids=['cellfree.html', 'cellfree-gnn.html'])}</div></section>'''
    return content


def figure(item):
    return f'<figure class="research-figure"><a href="{e(item["image"])}" data-enlarge aria-label="Expand figure: {e(item["alt"])}"><img src="{e(item.get("preview", item["image"]))}" alt="{e(item["alt"])}" loading="lazy"><span class="figure-expand" aria-hidden="true">⤢</span></a><figcaption>{e(item["caption"])}</figcaption></figure>'


def gnn():
    g = DATA['gnn']
    content = intro('RESEARCH / GNN-BASED PRECODING', 'Learning from<br><span class="accent">real-world signals.</span>', g['overview'])
    toc = ''.join(f'<a href="#{f["id"]}">{i:02} / {e(f["title"])}</a>' for i, f in enumerate(g['figures'], 1))
    content += f'<div class="container detail-layout"><aside class="detail-sidebar"><p class="eyebrow">IN THIS STUDY</p><nav aria-label="Study sections">{toc}<a href="#publication">05 / Publication</a></nav>{external(g["dataset_url"], "Download dataset", "button button-outline")}<p class="sidebar-note">Original measurements from the Techtile testbed.</p></aside><div class="detail-body"><div class="result-strip"><div><strong>33</strong><span>Access points</span></div><div><strong>500</strong><span>Spatial positions</span></div><div><strong>+8.2</strong><span>bits/channel use</span></div></div>'
    for f in g['figures']:
        content += f'<section class="study-section" id="{f["id"]}"><h2>{e(f["title"])}</h2>{figure(f)}</section>'
    content += '<section class="study-section" id="publication"><h2>The publication</h2><div class="publication-list">' + publication_rows(project_ids=['cellfree-gnn.html']) + '</div></section>'
    return content + '</div></div>'


def compress():
    content = intro('RESEARCH / FRONTHAUL COMPRESSION', 'Less to send.<br><span class="accent">More to connect.</span>', DATA['projects'][1]['summary'])
    questions = ''.join(f'<article class="question-row"><span>Q.{i:02}</span><h3>{e(q)}</h3></article>' for i, q in enumerate(DATA['compression_questions'], 1))
    return content + f'''<section class="container research-overview"><div class="research-context"><p class="eyebrow">RESEARCH DIRECTION / R.02</p><h2>Designing around<br>the communication cost.</h2><p>Distributed wireless systems connect many access points and processing units. Moving radio information between them puts communication capacity and computation in the same design picture.</p><p>This research direction explores efficient fronthaul compression. It complements my work on cell-free networking, where coordination, interference, and computational cost all matter.</p></div>{fronthaul_art()}</section><section class="container section">{heading('01', 'Open questions', 'What I’m exploring.')}<div class="questions">{questions}</div></section><section class="container related-section"><p class="eyebrow">KEEP EXPLORING</p><a class="study-link" href="cellfree.html"><div><h3>AI-driven signal processing in distributed MIMO</h3><p>A related research direction: learning to coordinate a distributed network.</p></div><span aria-hidden="true">↗</span></a><a class="text-link" href="publication.html">Browse publications ↗</a></section>'''


def validate_data():
    for group, key in [('projects', 'id'), ('publications', 'id'), ('posts', 'id')]:
        ids = [item[key] for item in DATA[group]]
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate IDs in {group}')
    for post in DATA['posts']:
        date.fromisoformat(post['date'])
    for image in [PROFILE['portrait'], *[p[k] for p in DATA['projects'] for k in ('image', 'preview') if p.get(k)], *[f[k] for f in DATA['gnn']['figures'] for k in ('image', 'preview') if f.get(k)]]:
        if not (ROOT / image).is_file():
            raise ValueError(f'Missing image: {image}')


def build():
    validate_data()
    pages = {
        'index.html': ('Wireless Systems & Machine Learning', 'home-page', 'about', home),
        'publication.html': ('Publications', 'archive-page', 'publications', publications),
        'services.html': ('Professional Service', 'service-page', 'service', services),
        'awards.html': ('Awards', 'awards-page', '', awards),
        'updates.html': ('Notes & Updates', 'notes-page', 'notes', updates),
        'cellfree.html': ('AI-Driven Distributed MIMO', 'research-page', 'research', cellfree),
        'cellfree-gnn.html': ('GNN-Based Precoding', 'research-page', 'research', gnn),
        'compress.html': ('Fronthaul Compression', 'research-page', 'research', compress),
    }
    nav_items = [('about', 'About', 'index.html#about'), ('research', 'Research', 'index.html#research'), ('publications', 'Publications', 'publication.html'), ('service', 'Service', 'services.html'), ('notes', 'Notes', 'updates.html')]
    for filename, (title, css, active, render) in pages.items():
        nav = ''.join(f'<a class="nav-link {"is-active" if key == active else ""}" href="{href if filename != "index.html" or key not in ["about", "research"] else "#" + key}"' + (' aria-current="page"' if active == key and filename != 'index.html' else '') + f'>{label}</a>' for key, label, href in nav_items)
        content = render()
        description = PROFILE['bio'] if filename == 'index.html' else {
            'publication.html': 'Publications by Tianzheng Miao on machine learning, distributed MIMO, and real-world wireless systems.',
            'services.html': 'Journal and conference peer review and technical program committee service by Tianzheng Miao.',
            'awards.html': 'Awards and academic milestones of Tianzheng Miao.',
            'updates.html': 'Research notes and personal reflections from Tianzheng Miao.',
            'cellfree.html': DATA['projects'][0]['summary'],
            'cellfree-gnn.html': DATA['gnn']['overview'],
            'compress.html': DATA['projects'][1]['summary'],
        }[filename]
        html = BASE.substitute(title=e(title + ' — ' + PROFILE['name']), description=e(description), body_class=css, navigation=nav, content=content, email=e(PROFILE['email']), name=e(PROFILE['name']), name_zh=e(PROFILE['name_zh']), location=e(PROFILE['location']))
        (ROOT / filename).write_text(html, encoding='utf-8', newline='\n')
        print(f'Built {filename}')
    (ROOT / 'citations').mkdir(exist_ok=True)
    for pub in DATA['publications']:
        (ROOT / 'citations' / f'{pub["id"]}.bib').write_text(bibtex(pub) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    build()
