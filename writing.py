#!/usr/bin/env python3
"""The writing, as works in their own right.

Screenshots of prose never read as prose at mosaic scale — they read as grey noise. These
are set as actual type instead, so a passage is legible at the same zoom that makes an
image legible, and the archive contains the writing rather than a picture of it.

One source: the 21 .docx pieces in "Old Writings".

Each piece contributes its title plus its opening passage, pulled automatically; the longer
ones also contribute a second passage from further in, chosen by hand in SECOND_PASSAGE.

Exposes PASSAGES: a list of dicts {project, title, body, attrib, kind, nth, src}.
"""
import os, re, glob, zipfile, html

SRC = "/Users/sundeepbasi/Workbench/TIME CAPSULE/Microfiche Photos"


def docx_paragraphs(path):
    """Plain paragraphs out of a .docx without any third-party library."""
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf8", "ignore")
    xml = re.sub(r"</w:p\s*>", "\n", xml)
    xml = re.sub(r"<w:tab[^>]*/>", " ", xml)
    text = html.unescape(re.sub(r"<[^>]+>", "", xml))
    return [re.sub(r"\s+", " ", p).strip() for p in text.split("\n") if p.strip()]


SENTENCE = re.compile(r"[^.!?]+[.!?]+[”\"'’)\]]*|\S[^.!?]*$")


def opening(paras, want=36, cap=50):
    """Title plus enough of the opening to stand on its own."""
    title = paras[0]
    body = paras[1:]
    if not body:
        return title, ""
    if sum(len(p.split()) for p in body) <= 46:       # a short poem: show the whole thing
        return title, "\n".join(body)
    # skip greetings and email headers — "Hey," is not an opening passage
    start = next((i for i, p in enumerate(body) if len(p.split()) >= 9), 0)
    out, n = [], 0
    for sent in SENTENCE.findall(body[start]):
        sent = sent.strip()
        if not sent:
            continue
        out.append(sent)
        n += len(sent.split())
        if n >= want:
            break
    words = " ".join(out).split()
    if len(words) > cap:
        return title, " ".join(words[:cap]).rstrip(",;:—-") + "…"
    return title, " ".join(words)


def trim(para, want=32, cap=48):
    """As much of a paragraph as stands on its own, cut at a sentence boundary."""
    out, n = [], 0
    for sent in SENTENCE.findall(para):
        sent = sent.strip()
        if not sent:
            continue
        out.append(sent)
        n += len(sent.split())
        if n >= want:
            break
    words = " ".join(out).split()
    return (" ".join(words[:cap]).rstrip(",;:—-") + "…") if len(words) > cap else " ".join(words)


# A second passage from further into each piece, chosen by hand. Identified by the opening
# words of the paragraph rather than by index, so it survives edits to the document and you
# can see at a glance which passage is meant. Anything here that no longer matches is
# reported by __main__ rather than silently dropped.
SECOND_PASSAGE = {
    "544.1km cigarette":            "As I lit the first cigarette",
    "cocos nucifera":               "Or did they scoff",
    "everyone has had a boss who is an idiot": "After a long pause",
    "float":                        "When I got home",
    "free drowning lessons":        "I hated you until",
    "how many sleeping pills would it take to get to saturn?": "He suggested we try therapy",
    "it took a multiverse":         "You see, there was a time",
    "kintsugi soul":                "And if you are the impatient type",
    "not the yeast bit interested": "In year five",
    "old cardigans":                "“I just want it to stop",
    "psychic queen":                "I want to read those dismissive hands",
    "rubber plants and silicon tits": "Or is it that we can’t appreciate",
    "sounds of sonder":             "False comfort is the reason",
    "squish":                       "He then picked the gypsy moth caterpillar",
    "the catfish paradox":          "At that point, I should have just shrugged",
    "the manchurian candidate":     "Three of the five test subjects",
    "the one with fiona apple and the dead naked guy": "“You see, he never wanted to date me",
    "the ultimate selfie":          "In my approximately thirty-four years",
    "tree carving":                 "Or maybe it just serves",
}


def old_writings():
    works = []
    for f in sorted(glob.glob(os.path.join(SRC, "Old Writings", "*.docx"))):
        if os.path.basename(f).startswith("~$"):
            continue
        paras = docx_paragraphs(f)
        if not paras:
            continue
        title, body = opening(paras)
        words = sum(len(p.split()) for p in paras[1:])
        rel = os.path.relpath(f, SRC)
        common = dict(project="Old Writings", attrib=f"{words:,} words", kind="prose")
        works.append(dict(common, title=title, body=body, nth=1, src=rel))

        cue = SECOND_PASSAGE.get(title)
        if cue:
            hit = next((p for p in paras[1:] if p.startswith(cue)), None)
            if hit:
                works.append(dict(common, title=title, body=trim(hit), nth=2,
                                  src=f"{rel}#2"))
    return works


PASSAGES = old_writings()
MISSING = [t for t in SECOND_PASSAGE
           if not any(w["title"] == t and w["nth"] == 2 for w in PASSAGES)]


if __name__ == "__main__":
    for w in PASSAGES:
        print(f"\n[{w['nth']}] {w['title']}   ({len(w['body'].split())} words)")
        print("   ", w["body"][:200])
    print(f"\n{len(PASSAGES)} passages from {len(set(w['src'].split('#')[0] for w in PASSAGES))} pieces")
    if MISSING:
        print("SECOND_PASSAGE keys that matched nothing:", MISSING)
