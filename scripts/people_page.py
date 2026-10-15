"""Render researcher and student portraits from the owner's profile data."""

from html import escape
import re
import unicodedata


def _slug(value):
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "person"


def _section_heading(title):
    return (
        '<div class="section-heading">'
        f'<h2 class="section-title">{escape(title)}</h2>'
        '</div>'
    )


def _person_card(name, person_id, image="", url="", aliases=()):
    """Use repository-relative image paths and optional profile URLs."""
    image = str(image or "").strip()
    if image and not image.startswith(("https://", "http://", "/", "./", "../")):
        image = "../" + image
    portrait = (
        f'<img class="person-photo" src="{escape(image or "../images/profile/default.svg", quote=True)}" '
        f'alt="{escape(name, quote=True) if image else ""}" width="144" height="144" '
        'loading="lazy" decoding="async">'
    )
    name_markup = escape(name)
    if url:
        name_markup = f'<a href="{escape(str(url), quote=True)}">{name_markup}</a>'
    alias_markup = "".join(
        f'<span class="visually-hidden" id="{escape(alias, quote=True)}" aria-hidden="true"></span>'
        for alias in aliases
    )
    return (
        f'<article class="person-card" id="{escape(person_id, quote=True)}">'
        + alias_markup + portrait
        + f'<h3 class="person-name">{name_markup}</h3></article>'
    )


def people_content(profile, add_search) -> str:
    """Return main content and register person anchors with the site search index.

    Student entries retain their groups and anchors from the CV records.
    Optional image and url fields add a portrait and a linked name.
    """
    name = str(profile["name"])
    lab = str(profile.get("lab_short_name", "PAIRS Lab"))
    owner_id = "person-" + _slug(name)
    used_ids = {owner_id}
    add_search(name, "People", f"people/#{owner_id}", "Research & teaching")
    content = (
        '<header class="page-heading">'
        f'<p class="eyebrow">{escape(lab)}</p>'
        '<h1>People</h1>'
        '<p class="page-intro">Researcher profile, students, and alumni in perception, '
        'autonomy, and intelligent robotics lab.</p>'
        '</header>'
        '<section class="content-section">'
        + _section_heading("Research & teaching")
        + '<div class="people-grid">'
        + _person_card(name, owner_id, "images/profile/thanh.jpg", "../index.html")
        + '</div></section>'
    )

    records_by_name = {}
    for group in profile.get("supervision", []):
        level = str(group["level"])
        for student in group.get("students", []):
            student_name = str(student["name"])
            institution = str(student["institution"])
            base_id = "person-" + _slug(level + " " + student_name + " " + institution)
            person_id = base_id
            suffix = 2
            while person_id in used_ids:
                person_id = f"{base_id}-{suffix}"
                suffix += 1
            used_ids.add(person_id)
            records_by_name.setdefault(student_name, []).append({
                "name": student_name,
                "institution": institution,
                "period": str(student["period"]),
                "level": level,
                "id": person_id,
                "image": student.get("image", ""),
                "url": student.get("url", ""),
            })

    def record_priority(record):
        years = [int(year) for year in re.findall(r"\b\d{4}\b", record["period"])]
        return (
            "present" in record["period"].lower(),
            max(years, default=0),
            min(years, default=0),
        )

    sections = {"Master students": [], "Undergraduate students": [], "Alumni": []}
    for records in records_by_name.values():
        selected = max(records, key=record_priority)
        if "present" not in selected["period"].lower():
            section_title = "Alumni"
        elif "master" in selected["level"].lower():
            section_title = "Master students"
        else:
            section_title = "Undergraduate students"
        selected["aliases"] = [record["id"] for record in records if record is not selected]
        sections[section_title].append(selected)

    for section_title, students in sections.items():
        cards = []
        for student in students:
            student_name = student["name"]
            person_id = student["id"]
            cards.append(
                _person_card(student_name, person_id, student["image"], student["url"], student["aliases"])
            )
            add_search(
                student_name,
                "People",
                f"people/#{person_id}",
                section_title,
            )
        if cards:
            content += (
                '<section class="content-section">'
                + _section_heading(section_title)
                + '<div class="people-grid">'
                + "".join(cards)
                + '</div></section>'
            )

    content += (
        '<section class="content-section">'
        + _section_heading("Research inquiries")
        + '<p>For student research and collaboration inquiries, get in touch to discuss your interests.</p>'
        '<div class="person-links">'
        '<a class="resource-link" href="../open-positions/">Research opportunities ↗</a>'
        '<a class="resource-link" href="../contact/">Contact ↗</a>'
        '</div></section>'
    )
    return content
