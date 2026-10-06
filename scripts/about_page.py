"""Render the homepage introduction with a portrait and local Font Awesome SVGs."""

from functools import lru_cache
from html import escape
from pathlib import Path
import re
import xml.etree.ElementTree as ET


@lru_cache(maxsize=6)
def _icon(name):
    """Validate and inline a local SVG, retaining its original license comment."""
    filenames = {
        "envelope": "envelope.svg",
        "building": "building.svg",
        "github": "github.svg",
        "linkedin": "linkedin.svg",
        "orcid": "orcid.svg",
        "scholar": "google-scholar.svg",
    }
    source = (Path(__file__).resolve().parents[1] / "assets" / "icons" / filenames[name]).read_text()
    if "<!DOCTYPE" in source.upper() or "<!ENTITY" in source.upper():
        raise ValueError("Icon SVG cannot contain document types or entities")
    root = ET.fromstring(source)
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError("Icon must have an SVG root")
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] not in {"svg", "path"}:
            raise ValueError("Icon SVG may contain only SVG and path elements")
        for key, value in element.attrib.items():
            attribute = key.rsplit("}", 1)[-1].lower()
            if attribute.startswith("on") or attribute in {"href", "src"} or "url(" in value.lower():
                raise ValueError("Icon SVG cannot contain scripts or external resources")
    return re.sub(
        r"<svg\b",
        '<svg width="32" height="32" aria-hidden="true" focusable="false"',
        source,
        count=1,
    )


def about_intro(profile) -> str:
    """Return the introduction section; its float layout is styled by about-intro."""
    name = str(profile["name"])
    email = str(profile["email"])
    lab_name = str(profile.get("lab_name", "Perception, Autonomy, and Intelligent Robotics Systems Lab"))
    lab_short_name = str(profile.get("lab_short_name", "PAIRS Lab"))
    social_links = [
        ("mailto:" + email, "Email", "envelope"),
        ("https://github.com/thanhnguyencanh", "GitHub", "github"),
        ("https://www.linkedin.com/in/nguyencanhthanh/", "LinkedIn", "linkedin"),
        ("https://orcid.org/0000-0001-6332-1002", "ORCID", "orcid"),
        ("https://scholar.google.com/citations?user=gnzxTKcAAAAJ&hl=en", "Google Scholar", "scholar"),
    ]
    social_html = "".join(
        f'<a class="social-icon" href="{escape(url, quote=True)}" '
        f'aria-label="{escape(label, quote=True)}" title="{escape(label, quote=True)}">'
        + _icon(icon)
        + '</a>'
        for url, label, icon in social_links
    )
    return (
        '<section class="about-intro">'
        '<header class="about-heading">'
        f'<h1>{escape(name)}</h1>'
        '<p class="about-contact">'
        f'<a class="about-lab" href="people/" title="{escape(lab_name, quote=True)}">'
        + _icon("building")
        + f'<span>{escape(lab_short_name)}</span></a>'
        '<span class="about-contact-separator" aria-hidden="true"> | </span>'
        f'<a href="mailto:{escape(email, quote=True)}">'
        + _icon("envelope")
        + f'<span>{escape(email)}</span></a></p>'
        '</header>'
        '<aside class="about-profile" aria-label="Portrait and profile links">'
        f'<img class="profile-photo" src="images/profile/thanh.jpg" alt="{escape(name, quote=True)}" '
        'width="320" height="320" decoding="async">'
        f'<div class="social-icons">{social_html}</div>'
        '</aside>'
        '<div class="about-bio">'
        + str(profile["bio_html"])
        + '<p class="about-cv"><a href="CV_Thanh%20Nguyen%20Canh.pdf">Curriculum vitae</a></p>'
        '<h2 class="about-research-title">Research Interests</h2>'
        '<p>My research focuses on semantic, active, and lifelong simultaneous localization and mapping '
        'for autonomous robots. I study probabilistic and continual learning, robot perception, and '
        'environment representation to support reliable navigation and motion planning. I am also '
        'interested in human–robot interaction, humanoid robotics, multisensor fusion, and control, '
        'with applications to unmanned aerial vehicles and other robotic platforms.</p>'
        '</div></section>'
    )
