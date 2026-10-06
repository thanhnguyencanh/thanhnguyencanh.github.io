"""Render researcher and student mentee cards from the owner's profile data."""

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

    Student entries describe the mentoring relationships recorded in the CV.
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
        '<p class="page-intro">Researcher profile and student mentees in perception, '
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

    for group in profile.get("supervision", []):
        level = str(group["level"])
        if "master" in level.lower():
            section_title = "Master's student mentees"
            person_role = "Master's student mentee"
        elif "undergraduate" in level.lower():
            section_title = "Undergraduate student mentees"
            person_role = "Undergraduate student mentee"
        else:
            section_title = level + " · student mentees"
            person_role = "Student mentee"
        cards = []
        for student in group.get("students", []):
            student_name = str(student["name"])
            institution = str(student["institution"])
            period = str(student["period"])
            base_id = "person-" + _slug(level + " " + student_name + " " + institution)
            person_id = base_id
            suffix = 2
            while person_id in used_ids:
                person_id = f"{base_id}-{suffix}"
                suffix += 1
            used_ids.add(person_id)
            cards.append(
                f'<article class="person-card" id="{escape(person_id, quote=True)}">'
                f'<div class="person-avatar" aria-hidden="true">{escape(_initials(student_name))}</div>'
                '<div class="person-info">'
                f'<h3>{escape(student_name)}</h3>'
                f'<p class="person-role">{escape(person_role)}</p>'
                f'<p class="person-affiliation">{escape(institution)}</p>'
                f'<p class="person-period">Mentoring · {escape(period)}</p>'
                '</div></article>'
            )
            add_search(
                student_name,
                "People",
                f"people/#{person_id}",
                " ".join([person_role, institution, period]),
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
