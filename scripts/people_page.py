"""Render researcher and student cards from the owner's profile data."""

from html import escape
import re
import unicodedata


def _slug(value):
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "person"


def _initials(name):
    parts = str(name).split()
    if not parts:
        return ""
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


def _section_heading(title):
    return (
        '<div class="section-heading">'
        f'<h2 class="section-title">{escape(title)}</h2>'
        '</div>'
    )


def people_content(profile, add_search) -> str:
    """Return main content and register person anchors with the site search index.

    Student entries use the student records provided in the CV.
    They do not assign lab membership, positions, photos, or research projects.
    """
    name = str(profile["name"])
    email = str(profile["email"])
    lab = str(profile.get("lab_short_name", "PAIRS Lab"))
    owner_id = "person-" + _slug(name)
    used_ids = {owner_id}
    owner_role = "PhD candidate and Research Assistant; Lecturer"
    owner_affiliation = (
        "Japan Advanced Institute of Science and Technology; "
        + str(profile.get("lecturer_department", "Robotics Department")) + ", "
        + str(profile.get("lecturer_institution", "University of Engineering and Technology, Vietnam National University"))
    )
    add_search(name, "People", f"people/#{owner_id}", owner_role + " " + owner_affiliation)

    owner_links = [
        ("mailto:" + email, "Email"),
        ("https://scholar.google.com/citations?user=gnzxTKcAAAAJ&hl=en", "Google Scholar"),
        ("https://github.com/thanhnguyencanh", "GitHub"),
        ("https://www.linkedin.com/in/nguyencanhthanh/", "LinkedIn"),
        ("https://orcid.org/0000-0001-6332-1002", "ORCID"),
        ("../CV_Thanh%20Nguyen%20Canh.pdf", "CV"),
    ]
    links = "".join(
        f'<a class="resource-link" href="{escape(url, quote=True)}">{escape(label)}</a>'
        for url, label in owner_links
    )
    content = (
        '<header class="page-heading">'
        f'<p class="eyebrow">{escape(lab)}</p>'
        '<h1>People</h1>'
        '<p class="page-intro">Researcher profile, students, and alumni in perception, '
        'autonomy, and intelligent robotics.</p>'
        '</header>'
        '<section class="content-section">'
        + _section_heading("Research & teaching")
        + '<div class="people-grid">'
        f'<article class="person-card lead-person" id="{escape(owner_id, quote=True)}">'
        f'<img class="person-photo" src="../images/profile/thanh.jpg" alt="{escape(name, quote=True)}" '
        'width="320" height="320" decoding="async">'
        '<div class="person-info">'
        f'<h3>{escape(name)}</h3>'
        '<p class="person-role">PhD candidate &amp; Research Assistant</p>'
        '<p class="person-affiliation">Japan Advanced Institute of Science and Technology (JAIST)</p>'
        '<p class="person-role">Lecturer</p>'
        f'<p class="person-affiliation">{escape(str(profile.get("lecturer_department", "Robotics Department")))}, '
        f'{escape(str(profile.get("lecturer_institution", "University of Engineering and Technology, Vietnam National University")))}</p>'
        f'<div class="person-links">{links}</div>'
        '</div></article></div></section>'
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
            institution = student["institution"]
            person_id = student["id"]
            aliases = "".join(
                f'<span class="visually-hidden" id="{escape(alias, quote=True)}" aria-hidden="true"></span>'
                for alias in student["aliases"]
            )
            cards.append(
                f'<article class="person-card" id="{escape(person_id, quote=True)}">'
                + aliases
                + f'<div class="person-avatar" aria-hidden="true">{escape(_initials(student_name))}</div>'
                '<div class="person-info">'
                f'<h3>{escape(student_name)}</h3>'
                f'<p class="person-affiliation">{escape(institution)}</p>'
                '</div></article>'
            )
            add_search(
                student_name,
                "People",
                f"people/#{person_id}",
                " ".join([section_title, institution]),
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
