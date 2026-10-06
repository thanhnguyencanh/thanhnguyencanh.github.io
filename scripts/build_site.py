#!/usr/bin/env python3
"""Render the academic site with Python's standard library; no runtime build needed."""

import html
import hashlib
import json
import re
from pathlib import Path

from people_page import people_content
from about_page import about_intro

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "data/profile.json").read_text())
PAPERS = json.loads((ROOT / "data/publications.json").read_text())
PAGES = [
    ("", "About"), ("research", "Research"), ("publications", "Publications"),
    ("teaching", "Teaching"), ("funded-projects", "Funded Projects"),
    ("datasets-code", "Dataset & Code"), ("open-positions", "Open Positions"),
    ("people", "People"), ("contact", "Contact"),
]
SEARCH = []


def asset_revision():
    """Give generated pages fresh CSS and scripts whenever their sources change."""
    sources = [ROOT / "stylesheet.css", ROOT / "assets/site.js"]
    sources += sorted((ROOT / "data").glob("*.json"))
    sources += sorted((ROOT / "scripts").glob("*.py"))
    digest = hashlib.sha256()
    for path in sources:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:12]


ASSET_REVISION = asset_revision()


def esc(value):
    return html.escape(str(value), quote=True)


def plain(value):
    return html.unescape(re.sub(r"<[^>]+>", " ", value)).strip()


def route(slug, prefix=""):
    return prefix + (slug + "/" if slug else "index.html")


def add_search(title, category, url, text):
    SEARCH.append({"title": title, "category": category, "url": url,
                   "text": re.sub(r"\s+", " ", plain(text))})


def heading(title, intro, eyebrow=""):
    return f'<header class="page-heading"><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(title)}</h1><p class="page-intro">{intro}</p></header>'


def section_heading(title, link="", label="View all"):
    action = f'<a class="section-link" href="{esc(link)}">{esc(label)} <span aria-hidden="true">↗</span></a>' if link else ""
    return f'<div class="section-heading"><h2 class="section-title">{esc(title)}</h2>{action}</div>'


def resource_links(paper):
    labels = {"paper": "Paper", "website": "Project", "code": "Code"}
    return "".join(f'<a class="resource-link" href="{esc(url)}">{labels.get(key, esc(key.title()))} <span aria-hidden="true">↗</span></a>' for key, url in paper["links"].items() if url)


def media(paper, prefix=""):
    if paper.get("image"):
        return f'<img src="{esc(prefix + paper["image"])}" alt="Research overview: {esc(paper["title"])}" loading="lazy" decoding="async">'
    if paper.get("video"):
        return f'<video controls muted playsinline preload="none" aria-label="Research demonstration: {esc(paper["title"])}"><source src="{esc(prefix + paper["video"])}" type="video/mp4">Your browser does not support embedded video. <a href="{esc(prefix + paper["video"])}">Download the demonstration</a>.</video>'
    return '<div class="resource-symbol" aria-hidden="true">◈</div>'


def citation(paper):
    kind, field = {"journal": ("article", "journal"), "conference": ("inproceedings", "booktitle"), "preprint": ("unpublished", "note")}[paper["type"]]
    authors = " and ".join(paper["authors"])
    return f'@{kind}{{{paper["id"]},\n  title = {{{paper["title"]}}},\n  author = {{{authors}}},\n  {field} = {{{paper["venue"]}}},\n  year = {{{paper["year"]}}}\n}}'


def paper_card(paper, prefix="", compact=False):
    title = esc(paper["title"])
    if paper["links"].get("website"):
        title = f'<a href="{esc(paper["links"]["website"])}">{title}</a>'
    authors = ", ".join(f'<strong>{esc(author)}</strong>' if author == PROFILE["name"] else esc(author) for author in paper["authors"])
    metadata = " · ".join(esc(x) for x in [paper["venue"], str(paper["year"]), paper.get("status", "")] if x)
    details = ""
    if not compact:
        if paper["abstract"]:
            details += f'<details class="abstract"><summary>Abstract</summary><p>{esc(paper["abstract"])}</p></details>'
        details += f'<details class="abstract citation"><summary>BibTeX</summary><pre><code>{esc(citation(paper))}</code></pre><button class="resource-link copy-citation" type="button" hidden>Copy citation</button></details>'
    has_media = bool(paper.get("image") or paper.get("video"))
    media_html = f'<div class="publication-media">{media(paper, prefix)}</div>' if has_media else ""
    card_class = "publication-card" + ("" if has_media else " text-only")
    search_text = " ".join([paper["title"], *paper["authors"], metadata, *paper["topics"], paper["abstract"]])
    return f'''<article class="{card_class}" id="{esc(paper['id'])}" data-year="{paper['year']}" data-type="{paper['type']}" data-topics="{esc('|'.join(paper['topics']))}" data-search="{esc(search_text)}">
{media_html}
<div class="publication-content"><div class="publication-venue"><span class="venue-badge">{esc(paper['type'].title())}</span><span class="publication-year">{paper['year']}</span></div>
<h4 class="publication-title">{title}</h4><p class="publication-authors">{authors}</p><p class="publication-meta">{metadata}</p><div class="publication-links">{resource_links(paper)}</div>{details}</div></article>'''


def render_page(slug, title, intro, content):
    prefix = "../" if slug else ""
    nav_links = []
    labels = dict(PAGES)
    for path in ["", "research", "publications", "teaching", "people", "funded-projects", "datasets-code", "open-positions", "contact"]:
        current = ' aria-current="page"' if path == slug else ""
        nav_links.append(f'<a href="{route(path, prefix)}"{current}>{labels[path]}</a>')
    nav = "".join(nav_links)
    search_icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>'
    theme_icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M20.5 14A8.5 8.5 0 0 1 10 3.5 8.5 8.5 0 1 0 20.5 14Z"/></svg>'
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title + ' | ' if slug else '')}{esc(PROFILE['name'])}</title><meta name="description" content="{esc(plain(intro))}"><meta name="author" content="{esc(PROFILE['name'])}">
<meta name="color-scheme" content="light dark"><script>document.documentElement.classList.add('js');try{{const t=localStorage.getItem('theme');if(t==='dark'||t==='light')document.documentElement.dataset.theme=t;else if(matchMedia('(prefers-color-scheme: dark)').matches)document.documentElement.dataset.theme='dark';}}catch(e){{}}</script>
<link rel="icon" href="{prefix}images/profile/thanh_circle.png"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&amp;display=swap"><link rel="stylesheet" href="{prefix}stylesheet.css?v={ASSET_REVISION}">
<script src="{prefix}assets/search-index.js?v={ASSET_REVISION}" defer></script><script src="{prefix}assets/site.js?v={ASSET_REVISION}" defer></script></head>
<body><a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header"><div class="header-inner"><a class="brand" href="{route('', prefix)}"><span class="brand-name">{esc(PROFILE['name'])}</span></a>
<button class="nav-toggle icon-button" type="button" aria-controls="site-nav" aria-expanded="false" aria-label="Open navigation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button>
<nav id="site-nav" class="site-nav" aria-label="Main navigation">{nav}</nav>
<div class="header-actions"><button id="open-search" class="icon-button" type="button" aria-label="Search this website" title="Search (Ctrl/⌘ K)" hidden>{search_icon}</button><button id="theme-toggle" class="icon-button" type="button" aria-label="Switch to dark theme" title="Change theme" hidden>{theme_icon}</button></div></div></header>
<main class="page-shell" id="main-content" tabindex="-1">{content}</main>
<footer class="site-footer"><div class="footer-inner"><p>© {esc(PROFILE['name'])} <span aria-hidden="true">·</span> {esc(PROFILE['lab_short_name'])}</p><div class="footer-links"><a href="{route('contact', prefix)}">Contact</a><a href="mailto:{esc(PROFILE['email'])}">Email</a><a href="{prefix}CV_Thanh%20Nguyen%20Canh.pdf">CV</a><a href="https://github.com/thanhnguyencanh">GitHub</a></div><p class="footer-credit">Original template credits: <a href="https://jonbarron.info/">Jon Barron</a> and <a href="https://thaipduong.github.io/">Thai Duong</a>.</p></div></footer>
<dialog id="site-search" class="search-dialog" aria-labelledby="search-title" data-root="{prefix}"><div class="dialog-topline"><h2 id="search-title">Search the website</h2><button id="close-search" class="icon-button" type="button" aria-label="Close search">×</button></div><form class="search-form" role="search"><label class="sr-only" for="site-query">Search publications, research, teaching and resources</label><input id="site-query" class="search-input" type="search" placeholder="Search publications, research, resources…" autocomplete="off"></form><p id="site-search-count" class="search-hint" role="status">Type a title, author, topic or keyword.</p><div id="site-search-results" class="search-results"></div><p class="search-hint">Ctrl/⌘ K to open <span aria-hidden="true">·</span> Esc to close</p></dialog>
</body></html>'''
    target = ROOT / slug / "index.html" if slug else ROOT / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(document, encoding="utf-8")
    add_search(title, "Page", route(slug), intro)


def home():
    news = ""
    for i, item in enumerate(sorted(PROFILE["news"], key=lambda item: item["date"], reverse=True)):
        from datetime import datetime
        date = datetime.strptime(item["date"], "%Y-%m").strftime("%b %Y")
        news += f'<li class="news-item" id="news-{i}"><time class="news-date" datetime="{item["date"]}">{date}</time><div class="news-body">{item["html"]}</div></li>'
        add_search(plain(item["html"]), "News", f'index.html#news-{i}', date + " " + item["html"])
    papers_by_id = {paper["id"]: paper for paper in PAPERS}
    selected = [papers_by_id[paper_id] for paper_id in PROFILE["selected_publications"]]
    content = about_intro(PROFILE) + f'''
<section class="content-section" id="news">{section_heading('Recent news')}<ul class="news-list">{news}</ul><button id="toggle-news" class="resource-link" type="button" aria-expanded="false" hidden>Show all news</button></section>
<section class="content-section">{section_heading('Selected publications', 'publications/', 'All publications')}{''.join(paper_card(p, compact=True) for p in selected)}</section>
<section class="content-section" id="awards">{section_heading('Awards & professional activities')}<ul class="service-list">{''.join('<li>' + x + '</li>' for x in PROFILE['awards'])}</ul><details class="abstract"><summary>Peer review & professional service</summary>{PROFILE['service_html']}</details></section>
<section class="content-section contact-inline" id="contact">{section_heading('Contact', 'contact/', 'Contact details')}<p>For research collaboration, student inquiries and questions about my work, contact me at <a href="mailto:{esc(PROFILE['email'])}">{esc(PROFILE['email'])}</a>.</p><p>{esc(PROFILE['lab_name'])} (PAIRS)</p><div class="publication-links"><a class="resource-link" href="people/">People ↗</a><a class="resource-link" href="mailto:{esc(PROFILE['email'])}?subject=Research%20collaboration">Email me ↗</a></div></section>'''
    render_page("", "About", "Thanh Nguyen Canh is a PhD candidate at JAIST working on semantic SLAM, robot learning and autonomous navigation.", content)
    add_search(PROFILE['lab_short_name'], "About", "index.html", PROFILE['lab_name'] + " " + PROFILE['name'])
    add_search("Peer review & professional service", "Service", "index.html#awards", PROFILE['service_html'] + " " + " ".join(PROFILE['awards']))


TOPICS = [
    ("semantic-slam", "01", "Active & semantic SLAM", "Building meaningful representations of the world for autonomous robots. My research spans probabilistic semantic mapping, visual SLAM under challenging conditions, and active exploration with UAVs.", ["SLAM", "Semantic mapping"]),
    ("robot-learning", "02", "Robot learning & interaction", "Learning robot behavior from observations, demonstrations and interaction. I investigate imitation learning, reinforcement learning and the use of vision-language models for robotic manipulation and human–robot interaction.", ["Robot learning", "Human–robot interaction", "Reinforcement learning"]),
    ("navigation", "03", "Reliable localization & navigation", "Connecting perception with safe decisions. I work on semantic-aware path planning, multisensor fusion, and motion prediction for navigation around people and in challenging environments.", ["Navigation", "Sensor fusion"]),
    ("robot-vision", "04", "Robot vision & industrial perception", "Turning visual observations into useful information for robotics and inspection. Applications include monocular 3D object localization and super-resolution methods for detecting tiny defects on printed circuit boards.", ["Computer vision", "Calibration", "Defect detection"]),
]


def research():
    cards = ""
    for slug, number, title, description, tags in TOPICS:
        tag_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)
        cards += f'<article class="topic-card" id="{slug}"><span class="topic-number">{number}</span><h2>{title}</h2><p>{description}</p><div class="research-tags">{tag_html}</div><a class="text-link" href="../publications/?q={esc(tags[0])}">Related publications <span aria-hidden="true">↗</span></a></article>'
        add_search(title, "Research", f"research/#{slug}", description + " " + " ".join(tags))
    project_cards = ""
    for p in PROFILE.get("research_projects", []):
        project_cards += f'<article class="timeline-item" id="{esc(p["id"])}"><div class="timeline-date">{esc(p["period"])}</div><div class="timeline-content"><h3>{esc(p["title"])}</h3><p>{esc(p["description"])}</p><p class="results-summary">{esc(p["tools"])}</p></div></article>'
        add_search(p["title"], "Research project", f'research/#{p["id"]}', " ".join(p.values()))
    projects_html = f'<section class="content-section">{section_heading("Research projects")}<div class="timeline">{project_cards}</div></section>' if project_cards else ""
    content = heading("Research", "Perception, representation and learning for robots that operate in the real world.", "Research directions") + f'<div class="topic-grid">{cards}</div>{projects_html}<section class="content-section"><h2>Connected research interests</h2><p>I am also interested in lifelong SLAM, robot dynamics learning, model-based reinforcement learning and learning from demonstration. Modeling uncertainty in map representations and robot dynamics is central to my interests in safe, active planning and control.</p></section><section class="content-section notice-card"><h2>Research resources</h2><p>Explore the papers, implementations and demonstrations behind these research directions.</p><div class="publication-links"><a class="resource-link" href="../publications/">Publications ↗</a><a class="resource-link" href="../datasets-code/">Dataset & Code ↗</a></div></section>'
    render_page("research", "Research", "Research on active semantic SLAM, robot learning, reliable navigation and industrial robot vision.", content)


def publications():
    years = sorted({p["year"] for p in PAPERS}, reverse=True)
    controls = f'''<div class="publication-toolbar" hidden><form id="publication-filters" role="search"><div class="search-field"><label class="sr-only" for="publication-query">Filter publications</label><svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/></svg><input id="publication-query" type="search" placeholder="Search title, author, venue or topic…" autocomplete="off"></div><label class="sr-only" for="publication-year">Publication year</label><select id="publication-year" class="filter-select"><option value="all">All years</option>{''.join(f'<option value="{y}">{y}</option>' for y in years)}</select><label class="sr-only" for="publication-type">Publication type</label><select id="publication-type" class="filter-select"><option value="all">All types</option><option value="journal">Journal articles</option><option value="conference">Conference papers</option><option value="preprint">Preprints</option></select></form><div class="filter-row" aria-label="Filter by research topic"><button class="filter-chip" data-topic="all" type="button" aria-pressed="true">All topics</button>{''.join(f'<button class="filter-chip" data-topic="{tag}" type="button" aria-pressed="false">{tag}</button>' for tag in ['SLAM', 'Navigation', 'Robot learning', 'Computer vision'])}</div></div><p id="publication-count" class="results-summary" role="status">{len(PAPERS)} publications · grouped by type and year</p>'''
    groups = ""
    for kind, label in [("journal", "Journal articles"), ("conference", "Conference papers"), ("preprint", "Preprints & submitted work")]:
        subset = [p for p in PAPERS if p["type"] == kind]
        if not subset:
            continue
        groups += f'<section class="publication-group"><h2>{label}</h2>'
        for year in sorted({p["year"] for p in subset}, reverse=True):
            groups += f'<div class="year-group"><h3 class="year-label">{year}</h3>' + "".join(paper_card(p, "../") for p in subset if p["year"] == year) + "</div>"
        groups += "</section>"
    content = heading("Publications", "Articles and conference papers, organized by category and year. Search by title, author, venue or research topic.", "Research output") + controls + groups + '<div id="publication-empty" class="empty-state" hidden><h2>No matching publications</h2><p>Try another keyword or reset the filters.</p><button id="reset-publications" class="resource-link" type="button">Reset filters</button></div>'
    render_page("publications", "Publications", "Search Thanh Nguyen Canh's publications by title, author, venue, year and research topic.", content)
    for p in PAPERS:
        add_search(p["title"], "Publication", f'publications/#{p["id"]}', " ".join([*p["authors"], p["venue"], str(p["year"]), *p["topics"], p["abstract"]]))


def teaching():
    items = ""
    for i, item in enumerate(PROFILE["teaching"]):
        title = esc(item["title"])
        if item.get("url"):
            title = f'<a href="{esc(item["url"])}">{title}</a>'
        courses = [course for course in item.get("courses", []) if course.casefold() not in item["title"].casefold()]
        course_summary = '<p class="course-summary">' + ' · '.join(esc(course) for course in courses) + '</p>' if courses else ""
        institution = f'<p>{esc(item["institution"])}</p>' if item["institution"] else ""
        items += f'<article class="timeline-item" id="teaching-{i}"><div class="timeline-date">{esc(item["date"])}</div><div class="timeline-content"><p class="section-kicker">{esc(item["role"])}</p><h2>{title}</h2>{institution}{course_summary}</div></article>'
        add_search(item["title"], "Teaching", f"teaching/#teaching-{i}", " ".join([item["institution"], item["role"], *item.get("courses", [])]))
    content = heading("Teaching", "Teaching experience in robotics, programming and signal processing.", "Teaching experience") + f'<div class="timeline">{items}</div><section class="content-section notice-card"><h2>Student research</h2><p>I have helped students with robotics research, including a team awarded second place in the 2023 Student Research Competition at VNU-University of Engineering and Technology.</p><a class="text-link" href="../open-positions/">Research inquiries ↗</a></section>'
    render_page("teaching", "Teaching", "Teaching experience at JAIST and VNU-University of Engineering and Technology.", content)


def funding():
    projects = ""
    for i, p in enumerate(PROFILE["funded_projects"]):
        projects += f'<article class="funding-card" id="project-{i}"><p class="funding-label">{esc(p["program"])}</p><h2>{esc(p["title"])}</h2><p>{esc(p["description"])}</p><dl class="funding-meta"><dt>Programme / call</dt><dd>{esc(p["grant"])}</dd><dt>Participation</dt><dd>{esc(p["role"])}</dd><dt>Appointment</dt><dd>{esc(p["period"])}</dd></dl><a class="resource-link" href="../CV_Thanh%20Nguyen%20Canh.pdf">Details in CV ↗</a></article>'
        add_search(p["title"], "Funded project", f"funded-projects/#project-{i}", " ".join(p.values()))
    support_items = sorted(PROFILE["support"], key=lambda p: tuple(int(year) for year in re.findall(r"\d{4}", p["period"])), reverse=True)
    support = "".join(f'<article class="support-card"><p class="section-kicker">{esc(p["kind"])}</p><h3>{esc(p["name"])}</h3><p class="funding-label">{esc(p["period"])}</p></article>' for p in support_items)
    content = heading("Funded Projects", "Research project participation, fellowships and academic support.", "Projects & research support") + f'<section class="content-section">{section_heading("Research projects")}{projects}</section><section class="content-section">{section_heading("Scholarships & fellowships")}<p>Personal academic support and research fellowships.</p><div class="support-grid">{support}</div></section>'
    render_page("funded-projects", "Funded Projects", "Research project participation, including SOLARIS, and academic scholarships and fellowships.", content)
    for p in PROFILE["support"]:
        add_search(p["name"], "Research support", "funded-projects/", " ".join(p.values()))


def resources():
    cards = ""
    available = [p for p in PAPERS if p["links"].get("code")]
    for p in sorted(available, key=lambda x: x["year"], reverse=True):
        cards += f'<article class="resource-card" id="code-{esc(p["id"])}"><div class="publication-media">{media(p, "../")}</div><div class="resource-body"><p class="resource-type">Code · {esc(p["topics"][0])}</p><h3>{esc(p["title"])}</h3><p>{esc(p["venue"])} · {p["year"]}</p><div class="publication-links">{resource_links(p)}<a class="resource-link" href="../publications/#{esc(p["id"])}">Publication ↗</a></div></div></article>'
        add_search(p["title"], "Code", f'datasets-code/#code-{p["id"]}', " ".join(p["topics"]) + " " + p["abstract"])
    content = heading("Dataset & Code", "Implementations and research resources for semantic mapping, robot learning, navigation and computer vision.", "Open research resources") + f'<section class="content-section">{section_heading("Code & implementations", "https://github.com/thanhnguyencanh", "GitHub profile")}<div class="resource-grid">{cards}</div></section><section class="content-section" id="datasets">{section_heading("Datasets")}<div class="notice-card"><h3>Dataset releases</h3><p>Dataset download links will be listed here when available. For resources associated with an existing paper, see its project page and repository.</p><a class="text-link" href="mailto:{esc(PROFILE["email"])}?subject=Research%20dataset%20inquiry">Ask about research data ↗</a></div></section><section class="content-section"><p class="results-summary">Please consult each repository for its license, usage instructions and citation information.</p></section>'
    render_page("datasets-code", "Dataset & Code", "Explore code and research resources for Thanh Nguyen Canh's robotics and computer vision projects.", content)
    add_search("Dataset availability", "Dataset", "datasets-code/#datasets", "Research datasets and data inquiries")


def positions():
    content = heading("Open Positions", "Information for prospective students, research visitors and collaborators.", "Work together") + f'''<section class="notice-card"><p class="section-kicker">Position announcements</p><h2>Future opportunities</h2><p>Specific positions, funding details and application deadlines will be posted here when announced.</p></section><section class="content-section">{section_heading('Research collaboration & student inquiries')}<p>If you are interested in semantic SLAM, robot learning or autonomous navigation, you can contact me to discuss research interests and possible collaboration.</p><div class="two-column"><div><h3>Research topics</h3><ul class="course-list"><li>Active, semantic and lifelong SLAM</li><li>Robot perception and environment representation</li><li>Imitation learning and human–robot interaction</li><li>Safe navigation and multisensor fusion</li></ul></div><div><h3>In your inquiry</h3><p>A brief introduction, your research interests, and links to relevant projects or publications will help start the discussion.</p><a class="resource-link" href="mailto:{esc(PROFILE['email'])}?subject=Research%20collaboration%20inquiry">Contact me ↗</a></div></div></section><section class="content-section"><p class="results-summary">For degree admission information, please consult <a href="https://www.jaist.ac.jp/english/admissions/">JAIST admissions</a>.</p></section>'''
    render_page("open-positions", "Open Positions", "Research collaboration and prospective student inquiries in SLAM, robotics and autonomous navigation.", content)


def people():
    content = people_content(PROFILE, add_search)
    render_page("people", "People", "Researchers and students associated with Thanh Nguyen Canh's research and teaching.", content)


def contact():
    profiles = [
        ("Google Scholar", "https://scholar.google.com/citations?user=gnzxTKcAAAAJ&hl=en"),
        ("GitHub", "https://github.com/thanhnguyencanh"),
        ("LinkedIn", "https://www.linkedin.com/in/nguyencanhthanh/"),
        ("ORCID", "https://orcid.org/0000-0001-6332-1002"),
    ]
    links = "".join(f'<a class="resource-link" href="{esc(url)}">{label} ↗</a>' for label, url in profiles)
    content = heading("Contact", "Get in touch about research, collaboration and student inquiries.", PROFILE['lab_short_name']) + f'''<div class="contact-grid"><section class="contact-card" id="email"><p class="contact-label">Email</p><h2>{esc(PROFILE['name'])}</h2><p>{esc(PROFILE['lab_name'])} (PAIRS)</p><p><a href="mailto:{esc(PROFILE['email'])}">{esc(PROFILE['email'])}</a></p><a class="resource-link" href="mailto:{esc(PROFILE['email'])}?subject=Research%20collaboration">Send an email ↗</a></section><section class="contact-card"><p class="contact-label">Online</p><h2>Research profiles</h2><div class="contact-links">{links}<a class="resource-link" href="../CV_Thanh%20Nguyen%20Canh.pdf">Download CV ↗</a></div></section></div><section class="content-section">{section_heading('Affiliations')}<div class="two-column"><div><h3>JAIST</h3><p>PhD candidate and research assistant<br>School of Information Science<br>Japan Advanced Institute of Science and Technology</p><p>Ishikawa, Japan</p><a class="text-link" href="https://www.jaist.ac.jp/english/">University website ↗</a></div><div><h3>{esc(PROFILE["lecturer_institution"])}</h3><p>Lecturer<br>{esc(PROFILE["lecturer_department"])}</p><p>Hanoi, Vietnam</p><a class="text-link" href="https://uet.vnu.edu.vn/en/">University website ↗</a></div></div></section><section class="content-section notice-card"><h2>Research & student inquiries</h2><p>A brief introduction and your research interests will help start the conversation. You can explore our research topics, publications and people before getting in touch.</p><div class="publication-links"><a class="resource-link" href="../research/">Research ↗</a><a class="resource-link" href="../people/">People ↗</a><a class="resource-link" href="../open-positions/">Open Positions ↗</a></div></section>'''
    render_page("contact", "Contact", "Contact Thanh Nguyen Canh at PAIRS Lab for research collaboration and student inquiries.", content)
    add_search(PROFILE['email'], "Contact", "contact/#email", PROFILE['name'] + " " + PROFILE['lab_name'] + " JAIST " + PROFILE['lecturer_department'] + " " + PROFILE['lecturer_institution'])


def main():
    home()
    research()
    publications()
    teaching()
    funding()
    resources()
    positions()
    people()
    contact()
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "search-index.js").write_text("// Generated by scripts/build_site.py\nwindow.siteSearch = " + json.dumps(SEARCH, ensure_ascii=False).replace("</", "<\\/") + ";\n", encoding="utf-8")
    print(f"Built {len(PAGES)} pages; indexed {len(SEARCH)} search entries.")


if __name__ == "__main__":
    main()
