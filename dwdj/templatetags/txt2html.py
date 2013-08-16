import re

from markupsafe import Markup
from django import template

register = template.Library()

BR = Markup("<br />")
AHREF = Markup("<a href='%s' rel='nofollow'>%s</a>")

LINK_RE = re.compile(r"(http(s?)\://\S+)")
def link_re_sub(match):
    link = match.group(0)
    return AHREF %(link, link)

EMAIL_RE = re.compile(r"(\S{2,}@\S{2,}\.[a-zA-Z]{2,3})\.?")
def email_re_sub(match):
    email = match.group(0)
    return AHREF %("mailto:" + email, email)


@register.filter
def txt2html(text):
    text = text.strip()
    text = LINK_RE.sub(link_re_sub, text)
    text = EMAIL_RE.sub(email_re_sub, text)
    text = text.replace("\n", BR)
    return text
