#!/usr/bin/env python3
"""Render the academic site with Python's standard library; no runtime build needed."""

import html
import hashlib
import json
import re
import subprocess
from pathlib import Path

from about_page import about_intro

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "data/profile.json").read_text())
PAPERS = json.loads((ROOT / "data/publications.json").read_text())
PAGES = [("", "About"), ("publications", "Publications"), ("blog", "Blog"), ("teaching", "Teaching"), ("contact", "Contact")]
LAB_URL = "https://pairs-lab.github.io/"  # research, people, projects, datasets and positions live on the lab site
SEARCH = []


def asset_revision():
    """Give generated pages fresh CSS and scripts whenever their sources change."""
    sources = [ROOT / "stylesheet.css", ROOT / "assets/site.js", ROOT / "assets/blog.css", ROOT / "assets/blog.js"]
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


def media_url(path, prefix=""):
    """Local paths are relative to the site root; full URLs (media hosted on the PAIRS Lab site) are used as they are."""
    return path if path.startswith(("http://", "https://")) else prefix + path


def media(paper, prefix=""):
    if paper.get("image"):
        return f'<img src="{esc(media_url(paper["image"], prefix))}" alt="Research overview: {esc(paper["title"])}" loading="lazy" decoding="async">'
    if paper.get("video"):
        src = esc(media_url(paper["video"], prefix))
        poster = f' poster="{esc(media_url(paper["poster"], prefix))}"' if paper.get("poster") else ""
        return f'<video controls muted playsinline preload="none"{poster} aria-label="Research demonstration: {esc(paper["title"])}"><source src="{src}" type="video/mp4">Your browser does not support embedded video. <a href="{src}">Download the demonstration</a>.</video>'
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


def format_source(source, target):
    """Keep generated code readable when the local Prettier tool is installed."""
    formatter = ROOT / "node_modules/.bin/prettier"
    if not formatter.is_file():
        return source
    return subprocess.run(
        [str(formatter), "--stdin-filepath", str(target)],
        input=source,
        stdout=subprocess.PIPE,
        text=True,
        check=True,
        cwd=ROOT,
    ).stdout


SUPPORT_SHORT = [("JSPS", "JSPS"), ("KDDI", "KDDI"), ("UniGe", "UniGe"), ("JST SPRING", "JST SPRING"), ("JAIST", "JAIST DRF"),
                 ("Monbukagakusho", "MEXT Honors"), ("VINIF", "VinIF"), ("Vallet", "Vallet")]


def support_ring(items):
    """Scholarships and fellowships as a 3D ring (like the PAIRS Lab member rings); a plain grid without JavaScript."""
    def short(name):
        return next((s for k, s in SUPPORT_SHORT if k in name), name.split(",")[0])
    cards = "".join(
        f'<button class="ring-card support-card kind-{esc(p["kind"].lower())}" type="button" data-card aria-label="Show {esc(p["name"])}, {esc(p["period"])}">'
        f'<span class="ring-tile"><span class="section-kicker">{esc(p["kind"])}</span><strong>{esc(short(p["name"]))}</strong><span class="funding-label">{esc(p["period"])}</span>'
        f'<span class="ring-full">{esc(p["name"])}</span></span></button>' for p in items)
    dots = "".join(f'<button type="button" data-dot aria-label="Show {esc(p["name"])}, {esc(p["period"])}"></button>' for p in items)
    details = "".join(f'<p class="ring-detail" data-detail><span class="section-kicker">{esc(p["kind"])} · {esc(p["period"])}</span><strong>{esc(p["name"])}</strong></p>' for p in items)
    return (f'<div class="ring" data-ring tabindex="0" aria-roledescription="carousel" aria-label="Scholarships and fellowships"><div class="ring-stage">{cards}</div>'
            f'<button class="ring-arrow ring-prev" type="button" data-prev aria-label="Previous">&#9664;</button>'
            f'<button class="ring-arrow ring-next" type="button" data-next aria-label="Next">&#9654;</button>'
            f'<div class="ring-dots">{dots}</div></div><div class="ring-details" aria-live="polite">{details}</div>')


def social_meta(slug, title, intro, image=None, kind=None):
    """Canonical URL, link-preview tags and (home page) schema.org Person, so search engines and chat apps show the current photo.
    A page with its own 1200 x 630 picture (image, relative to the site root) shows that instead, as a large preview."""
    url = SITE + (slug + "/" if slug else "")
    photo = SITE + "images/profile/thanh-800.jpg"
    full = (title + " | " if slug else "") + PROFILE["name"]
    if image:
        picture = (f'<meta property="og:image" content="{esc(SITE + image)}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(title)}">'
                   f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{esc(SITE + image)}">')
    else:
        picture = (f'<meta property="og:image" content="{photo}"><meta property="og:image:width" content="800"><meta property="og:image:height" content="800"><meta property="og:image:alt" content="{esc(PROFILE["name"])}">'
                   f'<meta name="twitter:card" content="summary"><meta name="twitter:image" content="{photo}">')
    tags = (f'<link rel="canonical" href="{esc(url)}"><meta property="og:type" content="{kind or ("profile" if not slug else "website")}"><meta property="og:site_name" content="{esc(PROFILE["name"])}">'
            f'<meta property="og:title" content="{esc(full)}"><meta property="og:description" content="{esc(plain(intro))}"><meta property="og:url" content="{esc(url)}">' + picture)
    if not slug:
        person = {"@context": "https://schema.org", "@type": "Person", "name": PROFILE["name"], "url": SITE, "image": photo, "email": "mailto:" + PROFILE["email"],
                  "jobTitle": PROFILE["role"], "affiliation": [{"@type": "CollegeOrUniversity", "name": PROFILE["affiliation"]},
                                                              {"@type": "CollegeOrUniversity", "name": PROFILE["lecturer_institution"]}],
                  "worksFor": {"@type": "ResearchOrganization", "name": PROFILE["lab_short_name"], "url": LAB_URL},
                  "sameAs": ["https://scholar.google.com/citations?user=gnzxTKcAAAAJ", "https://orcid.org/0000-0001-6332-1002",
                             "https://github.com/thanhnguyencanh", "https://www.linkedin.com/in/nguyencanhthanh/", LAB_URL]}
        tags += '<script type="application/ld+json">' + json.dumps(person, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    return tags


def render_page(slug, title, intro, content, head="", image=None, kind=None, search_category="Page"):
    prefix = "../" * (slug.count("/") + 1) if slug else ""
    section = slug.split("/")[0]
    nav_links = []
    for path, label in PAGES:
        current = ' aria-current="page"' if path == section else ""
        nav_links.append(f'<a href="{route(path, prefix)}"{current}>{label}</a>')
    nav_links.append(f'<a href="{LAB_URL}">PAIRS Lab <span aria-hidden="true">↗</span></a>')
    nav = "\n".join(nav_links)
    search_icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>'
    theme_icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M20.5 14A8.5 8.5 0 0 1 10 3.5 8.5 8.5 0 1 0 20.5 14Z"/></svg>'
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title + ' | ' if slug else '')}{esc(PROFILE['name'])}</title><meta name="description" content="{esc(plain(intro))}"><meta name="author" content="{esc(PROFILE['name'])}">
<meta name="color-scheme" content="light dark"><script>document.documentElement.classList.add('js');try{{const t=localStorage.getItem('theme');if(t==='dark'||t==='light')document.documentElement.dataset.theme=t;else if(matchMedia('(prefers-color-scheme: dark)').matches)document.documentElement.dataset.theme='dark';}}catch(e){{}}</script>
<link rel="icon" href="{prefix}images/profile/thanh-icon-32.png" type="image/png" sizes="32x32"><link rel="apple-touch-icon" href="{prefix}images/profile/thanh-icon-180.png">{social_meta(slug, title, intro, image, kind)}<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&amp;display=swap"><link rel="stylesheet" href="{prefix}stylesheet.css?v={ASSET_REVISION}">
<script src="{prefix}assets/search-index.js?v={ASSET_REVISION}" defer></script><script src="{prefix}assets/site.js?v={ASSET_REVISION}" defer></script>{head}</head>
<body><a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header"><div class="header-inner"><a class="brand" href="{route('', prefix)}"><span class="brand-name">{esc(PROFILE['name'])}</span></a>
<button class="nav-toggle icon-button" type="button" aria-controls="site-nav" aria-expanded="false" aria-label="Open navigation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button>
<nav id="site-nav" class="site-nav" aria-label="Main navigation">{nav}</nav>
<div class="header-actions"><button id="open-search" class="icon-button" type="button" aria-label="Search this website" title="Search (Ctrl/⌘ K)" hidden>{search_icon}</button><button id="theme-toggle" class="icon-button" type="button" aria-label="Switch to dark theme" title="Change theme" hidden>{theme_icon}</button></div></div></header>
<main class="page-shell" id="main-content" tabindex="-1">{content}</main>
<footer class="site-footer"><div class="footer-inner"><p>© {esc(PROFILE['name'])} <span aria-hidden="true">·</span> {esc(PROFILE['lab_short_name'])}</p><div class="footer-links"><a href="{route('contact', prefix)}">Contact</a><a href="mailto:{esc(PROFILE['email'])}">Email</a><a href="{prefix}CV_Thanh%20Nguyen%20Canh.pdf">CV</a><a href="https://github.com/thanhnguyencanh">GitHub</a></div></div></footer>
<dialog id="site-search" class="search-dialog" aria-labelledby="search-title" data-root="{prefix}"><div class="dialog-topline"><h2 id="search-title">Search the website</h2><button id="close-search" class="icon-button" type="button" aria-label="Close search">×</button></div><form class="search-form" role="search"><label class="sr-only" for="site-query">Search publications, research, teaching and resources</label><input id="site-query" class="search-input" type="search" placeholder="Search publications, research, resources…" autocomplete="off"></form><p id="site-search-count" class="search-hint" role="status">Type a title, author, topic or keyword.</p><div id="site-search-results" class="search-results"></div><p class="search-hint">Ctrl/⌘ K to open <span aria-hidden="true">·</span> Esc to close</p></dialog>
</body></html>'''
    target = ROOT / slug / "index.html" if slug else ROOT / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_source(document, target), encoding="utf-8")
    if search_category:
        add_search(title, search_category, route(slug), intro)


def home():
    news = ""
    for i, item in enumerate(sorted(PROFILE["news"], key=lambda item: item["date"], reverse=True)):
        from datetime import datetime
        date = datetime.strptime(item["date"], "%Y-%m").strftime("%b %Y")
        news += f'<li class="news-item" id="news-{i}"><time class="news-date" datetime="{item["date"]}">{date}</time><div class="news-body">{item["html"]}</div></li>'
        add_search(plain(item["html"]), "News", f'index.html#news-{i}', date + " " + item["html"])
    papers_by_id = {paper["id"]: paper for paper in PAPERS}
    selected = [papers_by_id[paper_id] for paper_id in PROFILE["selected_publications"]]
    support_items = sorted(PROFILE["support"], key=lambda p: tuple(int(year) for year in re.findall(r"\d{4}", p["period"])), reverse=True)
    support = support_ring(support_items)
    content = about_intro(PROFILE) + f'''
<section class="content-section" id="news">{section_heading('Recent news')}<ul class="news-list">{news}</ul><button id="toggle-news" class="resource-link" type="button" aria-expanded="false" hidden>Show all news</button></section>
<section class="content-section">{section_heading('Selected publications', 'publications/', 'All publications')}{''.join(paper_card(p, compact=True) for p in selected)}</section>
<section class="content-section" id="awards">{section_heading('Awards & professional activities')}<ul class="service-list">{''.join('<li>' + x + '</li>' for x in PROFILE['awards'])}</ul><details class="abstract"><summary>Peer review & professional service</summary>{PROFILE['service_html']}</details></section>
<section class="content-section" id="scholarships">{section_heading("Scholarships & fellowships")}<p>Personal academic support and research fellowships.</p>{support}</section>
<section class="content-section contact-inline" id="contact">{section_heading('Contact', 'contact/', 'Contact details')}<p>For research collaboration, student inquiries and questions about my work, contact me at <a href="mailto:{esc(PROFILE['email'])}">{esc(PROFILE['email'])}</a>.</p><p>{esc(PROFILE['lab_name'])} (PAIRS)</p><div class="publication-links"><a class="resource-link" href="{LAB_URL}">PAIRS Lab ↗</a><a class="resource-link" href="mailto:{esc(PROFILE['email'])}?subject=Research%20collaboration">Email me ↗</a></div></section>'''
    render_page("", "About", "Thanh Nguyen Canh is a PhD candidate at JAIST working on semantic SLAM, robot learning and autonomous navigation.", content)
    add_search(PROFILE['lab_short_name'], "About", "index.html", PROFILE['lab_name'] + " " + PROFILE['name'])
    add_search("Peer review & professional service", "Service", "index.html#awards", PROFILE['service_html'] + " " + " ".join(PROFILE['awards']))


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
    content = heading("Teaching", "Teaching experience in robotics, programming and signal processing.", "Teaching experience") + f'<div class="timeline">{items}</div><section class="content-section notice-card"><h2>Student research</h2><p>Student Research Competition, VNU-University of Engineering and Technology:</p><ul><li>Second place, 2023</li><li>Third place, 2025</li><li>Second place, 2026</li></ul><a class="text-link" href="{LAB_URL}join/">Research inquiries ↗</a></section>'
    render_page("teaching", "Teaching", "Teaching experience at JAIST and VNU-University of Engineering and Technology.", content)


# ---------- blog ----------
# Posts are bilingual: each text exists as .t-en and .t-vi, and html[data-lang] shows one (assets/blog.css).
# A post is data/blog/<slug>.html (its body) plus, for data posts, blog/<slug>/data.js and covers written by its generator
# (e.g. scripts/make_blog_slam_tree.py).
BLOG = sorted(json.loads((ROOT / "data/blog.json").read_text(encoding="utf-8")), key=lambda p: p["date"], reverse=True)
BLOG_INTRO = {"en": "Interactive maps of research fields, tutorials and notes on SLAM and robot learning, in English and Vietnamese.",
              "vi": "Bản đồ tương tác về các lĩnh vực nghiên cứu, bài hướng dẫn và ghi chú về SLAM và học robot, bằng tiếng Anh và tiếng Việt."}
LANG_SWITCH = ('<div class="lang-switch" role="group" aria-label="Language / Ngôn ngữ">'
               '<button class="filter-chip" type="button" data-set-lang="en" aria-pressed="true">English</button>'
               '<button class="filter-chip" type="button" data-set-lang="vi" aria-pressed="false">Tiếng Việt</button></div>')


def bi(text, markup=False):
    """Both languages of a text; markup=True keeps the trusted HTML of data/blog.json."""
    show = (lambda value: value) if markup else esc
    return f'<span class="t-en">{show(text["en"])}</span><span class="t-vi">{show(text["vi"])}</span>'


def bi_date(value):
    import datetime
    d = datetime.date.fromisoformat(value)
    return bi({"en": f"{d.day} {d.strftime('%B %Y')}", "vi": f"{d.day} tháng {d.month}, {d.year}"})


def bi_tags(tags):
    return "".join(f'<div class="research-tags t-{lang}">' + "".join('<span class="tag">' + esc(t) + "</span>" for t in tags[lang]) + "</div>" for lang in ("en", "vi"))


def blog_head(prefix):
    """Blog stylesheet, and the reading language set before the first paint: ?lang= in the link, else the last choice, else English."""
    return (f'<link rel="stylesheet" href="{prefix}assets/blog.css?v={ASSET_REVISION}">'
            '<script>try{const q=new URLSearchParams(location.search).get("lang");let l=q==="vi"||q==="en"?q:localStorage.getItem("blog-lang");'
            'l=l==="vi"?"vi":"en";document.documentElement.dataset.lang=l;document.documentElement.lang=l}catch(e){document.documentElement.dataset.lang="en"}</script>')


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def blog():
    entries = ""
    for p in BLOG:
        folder = ROOT / "blog" / p["slug"]
        covers = "".join(f'<img class="cover-{theme}" src="{p["slug"]}/{name}?v={fingerprint(folder / name)}" alt="" width="1200" height="630" loading="lazy" decoding="async">'
                         for theme, name in (("light", "cover.svg"), ("dark", "cover-dark.svg")) if (folder / name).is_file())
        cover = f'<a class="blog-cover" href="{p["slug"]}/" tabindex="-1" aria-hidden="true">{covers}</a>' if covers else ""
        entries += (f'<article class="blog-entry{"" if cover else " text-only"}" id="{esc(p["slug"])}">{cover}<div>'
                    f'<div class="publication-venue"><span class="venue-badge">{bi(p["kind"])}</span><span class="publication-year">{bi_date(p["date"])}</span></div>'
                    f'<h2><a href="{p["slug"]}/">{bi(p["title"])}</a></h2><p>{bi(p["summary"])}</p>{bi_tags(p["tags"])}</div></article>')
    n = len(BLOG)
    count = bi({"en": f"{n} post" + ("" if n == 1 else "s"), "vi": f"{n} bài viết"})
    content = (f'<header class="page-heading"><p class="eyebrow">{bi({"en": "Notes and explainers", "vi": "Ghi chú và giải thích"})}</p><h1>Blog</h1>'
               f'<p class="page-intro">{bi(BLOG_INTRO)}</p></header><div class="blog-toolbar"><span>{count}</span>{LANG_SWITCH}</div>{entries}'
               f'<script src="../assets/blog.js?v={ASSET_REVISION}"></script>')
    render_page("blog", "Blog", BLOG_INTRO["en"], content, head=blog_head("../"))
    for p in BLOG:
        slug = "blog/" + p["slug"]
        folder = ROOT / slug
        url = SITE + slug + "/"
        image = slug + "/cover.png" if (folder / "cover.png").is_file() else None
        post = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"]["en"], "alternativeHeadline": p["title"]["vi"],
                "description": p["summary"]["en"], "datePublished": p["date"], "inLanguage": ["en", "vi"], "mainEntityOfPage": url,
                "author": {"@type": "Person", "name": PROFILE["name"], "url": SITE}}
        if image:
            post["image"] = SITE + image
        head = blog_head("../../") + '<script type="application/ld+json">' + json.dumps(post, ensure_ascii=False).replace("</", "<\\/") + "</script>"
        header = (f'<header class="page-heading post-heading"><p class="eyebrow"><a href="../">Blog</a> · {bi_date(p["date"])}</p>'
                  f'<h1>{bi(p["title"])}</h1><p class="page-intro">{bi(p["lead"], markup=True)}</p>'
                  f'<div class="post-byline"><span><a href="../../">{esc(PROFILE["name"])}</a> · <a href="{LAB_URL}">{esc(PROFILE["lab_short_name"])}</a></span>{LANG_SWITCH}</div></header>')
        scripts = f'<script src="data.js?v={fingerprint(folder / "data.js")}"></script>' if (folder / "data.js").is_file() else ""
        scripts += f'<script src="../../assets/blog.js?v={ASSET_REVISION}"></script>'
        body = (ROOT / "data/blog" / (p["slug"] + ".html")).read_text(encoding="utf-8")
        render_page(slug, p["title"]["en"], p["summary"]["en"], header + body + scripts, head=head, image=image, kind="article", search_category=None)
        add_search(p["title"]["en"], "Blog", slug + "/", " ".join([p["title"]["vi"], p["summary"]["en"], p["summary"]["vi"], *p["tags"]["en"], *p["tags"]["vi"]]))


def office_details(key, title):
    office = PROFILE["offices"][key]
    add_search(title + " office", "Contact", f"contact/#{key}",
               " ".join([title, "Room " + office["room"], office["building"], office["city"]]))
    return (
        f'<address class="office-address">Room {esc(office["room"])}, {esc(office["building"])}<br>{esc(office["city"])}</address>'
        '<div class="affiliation-links">'
        f'<a class="text-link" href="{esc(office["maps_url"])}">Open in Google Maps ↗</a>'
        f'<a class="text-link" href="{esc(office["university_url"])}">University website ↗</a>'
        '</div>'
        f'<iframe class="affiliation-map" title="Google Maps location for {esc(title)}" '
        f'src="{esc(office["embed_url"])}" width="480" height="280" loading="lazy" '
        'referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>'
    )


def contact():
    profiles = [
        ("Google Scholar", "https://scholar.google.com/citations?user=gnzxTKcAAAAJ&hl=en"),
        ("GitHub", "https://github.com/thanhnguyencanh"),
        ("LinkedIn", "https://www.linkedin.com/in/nguyencanhthanh/"),
        ("ORCID", "https://orcid.org/0000-0001-6332-1002"),
    ]
    links = "".join(f'<a class="resource-link" href="{esc(url)}">{label} ↗</a>' for label, url in profiles)
    content = heading("Contact", "Get in touch about research, collaboration and student inquiries.", PROFILE['lab_short_name']) + f'''<div class="contact-grid"><section class="contact-card" id="email"><p class="contact-label">Email</p><h2>{esc(PROFILE['name'])}</h2><p>{esc(PROFILE['lab_name'])} (PAIRS)</p><p><a href="mailto:{esc(PROFILE['email'])}">{esc(PROFILE['email'])}</a></p><a class="resource-link" href="mailto:{esc(PROFILE['email'])}?subject=Research%20collaboration">Send an email ↗</a></section><section class="contact-card"><p class="contact-label">Online</p><h2>Research profiles</h2><div class="contact-links">{links}<a class="resource-link" href="../CV_Thanh%20Nguyen%20Canh.pdf">Download CV ↗</a></div></section></div><section class="content-section">{section_heading('Affiliations')}<div class="two-column"><div class="affiliation" id="jaist"><h3>JAIST</h3><p>PhD candidate and research assistant<br>School of Information Science<br>Japan Advanced Institute of Science and Technology</p>{office_details("jaist", "JAIST")}</div><div class="affiliation" id="uet"><h3>{esc(PROFILE["lecturer_institution"])}</h3><p>Lecturer<br>{esc(PROFILE["lecturer_department"])}</p>{office_details("uet", "UET")}</div></div></section><section class="content-section notice-card"><h2>Research & student inquiries</h2><p>A brief introduction and your research interests will help start the conversation. You can explore our research topics, publications and people before getting in touch.</p><div class="publication-links"><a class="resource-link" href="{LAB_URL}research/">Lab research ↗</a><a class="resource-link" href="{LAB_URL}people/">Lab members ↗</a><a class="resource-link" href="{LAB_URL}join/">Join the lab ↗</a></div></section>'''
    render_page("contact", "Contact", "Contact Thanh Nguyen Canh at PAIRS Lab for research collaboration and student inquiries.", content)
    add_search(PROFILE['email'], "Contact", "contact/#email", PROFILE['name'] + " " + PROFILE['lab_name'] + " JAIST " + PROFILE['lecturer_department'] + " " + PROFILE['lecturer_institution'])


SITE = "https://thanhnguyencanh.github.io/"


def seo_files():
    """sitemap.xml and robots.txt for this site and the project pages served under it (thanhnguyencanh.github.io/<repo>/)."""
    import datetime
    today = datetime.date.today().isoformat()
    projects = sorted({u for p in PAPERS for u in [p["links"].get("website", "")] if u.startswith(SITE) and u != SITE})
    lab = json.loads((ROOT.parent / "pairslab.github.io/data/publications.json").read_text()) if (ROOT.parent / "pairslab.github.io/data/publications.json").is_file() else []
    projects = sorted(set(projects) | {u for p in lab for u in [p["links"].get("website", "")] if u.startswith(SITE) and u != SITE})
    urls = [SITE + (slug + "/" if slug else "") for slug, _ in PAGES] + [SITE + "blog/" + p["slug"] + "/" for p in BLOG] + projects
    body = "".join(f"<url><loc>{html.escape(u)}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + body + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8")
    return len(urls)


def main():
    home()
    publications()
    blog()
    teaching()
    contact()
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    search_index = assets / "search-index.js"
    search_source = (
        "// Generated by scripts/build_site.py\nwindow.siteSearch = "
        + json.dumps(SEARCH, ensure_ascii=False).replace("</", "<\\/")
        + ";\n"
    )
    search_index.write_text(format_source(search_source, search_index), encoding="utf-8")
    n = seo_files()
    print(f"Built {len(PAGES)} pages; indexed {len(SEARCH)} search entries; sitemap lists {n} URLs.")


if __name__ == "__main__":
    main()
