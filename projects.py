#!/usr/bin/env python3
"""Folder -> project metadata. Edit this file to change how tiles are labelled."""

# folder (as it appears under "Microfiche Photos") -> (Display name, Category, Kind)
PROJECTS = {
    "Apparel":                      ("Apparel",                    "Objects",  "garment"),
    "Apparel/AuraCadet":            ("Aura Cadet",                 "Objects",  "garment"),
    "Campsorted":                   ("CampSorted",                 "Web",      "deck"),
    "Card_Pngs":                    ("ELECTION",                   "Games",    "card"),
    "Election Files for Portfolio": ("ELECTION",                   "Games",    "campaign"),
    "DUMP":                         ("The Dump Show",              "Games",    "screen"),
    "Emiko and the Night House":    ("Emiko and the Night House",  "Books",    "page"),
    "Epsilon":                      ("Epsilon",                    "Web",      "screen"),
    "Feelabit":                     ("Feelabit",                   "Apps",     "screen"),
    "Halal 100":                    ("Halal 100",                  "Apps",     "mark"),
    "Home Page":                    ("youmightfindit.com",         "Web",      "screen"),
    "Hue Hunt":                     ("Hue Hunt",                   "Apps",     "screen"),
    "Misc.":                        ("Miscellany",                 "Objects",  "image"),
    "Nearside":                     ("Nearside",                   "Apps",     "screen"),
    "Politics":                     ("The Voting Report Card",     "Web",      "screen"),
    "Quickfire":                    ("Quickfire",                  "Web",      "screen"),
    "Rainbow Cobra":                ("Rainbow Cobra",              "Games",    "screen"),
    "rainbow cobra photos":         ("Rainbow Cobra",              "Games",    "screen"),
    "The Flush 50":                 ("The Flush 50",               "Apps",     "screen"),
    "Two Dots and a Line":          ("Two Dots and a Line",        "Games",    "screen"),
    "URL Sorted":                   ("URL Sorted",                 "Web",      "screen"),
    "Words":                        ("Words",                      "Writing",  "text"),
    "Yume Nikki":                   ("Yume Nikki",                 "Web",      "screen"),
}

# Where a work goes when you click it, once you're zoomed in. Keyed by the display name in
# PROJECTS above. A project with no entry here simply isn't clickable.
LINKS = {
    "CampSorted":               "https://youmightfindit.com/portfolio/campsorted",
    "Aura Cadet":               "https://youmightfindit.com/portfolio/auracadet",
    "Apparel":                  "https://youmightfindit.com/portfolio/auracadet",
    "ELECTION":                 "https://youmightfindit.com/portfolio/election",
    "Emiko and the Night House": "https://youmightfindit.com/portfolio/emiko",
    "Hue Hunt":                 "https://youmightfindit.com/portfolio/hue-hunt",
    "The Voting Report Card":   "https://youmightfindit.com/portfolio/voting",
    "Feelabit":                 "https://youmightfindit.com/portfolio/innerloop",   # earlier name
    "Old Writings":             "https://youmightfindit.com/portfolio/the-tasting-menu-writing-samples",
    "Words":                    "https://youmightfindit.com/portfolio/the-tasting-menu-writing-samples",
    "Halal 100":                "https://youmightfindit.com/apps",
    "Nearside":                 "https://youmightfindit.com/apps",
    "Rainbow Cobra":            "https://youmightfindit.com/apps",
    "The Flush 50":             "https://youmightfindit.com/apps",
}

# Source images to leave out of the archive entirely.
EXCLUDE = [
    "Quickfire/01-app-icon-512.png",     # the green Q — off-brand
    "Quickfire/02-app-icon-192.png",     # same artwork, exported twice
]

# Hero images: get a larger block in the mosaic. Matched on the source path suffix.
HEROES = [
    "Emiko and the Night House/emiko_page_01.png",
    "DUMP/02-title-menu-dmg.png",
    "Two Dots and a Line/01-title-screen.png",
    "Rainbow Cobra/01-key-art-splash.png",
    "The Flush 50/01-app-icon-master-4797px.png",
    "Feelabit/01-app-icon-rabbit-1024.png",
    "Halal 100/Halal_100-02_forbiggerimages.png",
    "Hue Hunt/03-app-icon-source.png",
    "Home Page/01-sunset-hero.png",
    "Home Page/03-playlist-open.png",
    "URL Sorted/01-extension-icon-128-4x.png",
    "Nearside/01-logo-256-4x.png",
    "Yume Nikki/01-nexus-hub.png",
    "Election Files for Portfolio/election_kickstarter_hero2.jpg",
    "Misc./nouselesstech-11.png",
    "Words/Screen Shot 2020-11-20 at 11.25.11 AM.jpeg",
    "Apparel/AuraCadet/AC_ShortSleeve_Black_03.jpg",  # the broken-heart X mark
]

# Filename fragment -> nicer title fragment
RENAME = [
    ("emiko_page_",              "Page "),
    ("AC_K_Hoodie_",             "Kids Hoodie · "),
    ("AC_W_Hoodie_",             "Womens Hoodie · "),
    ("AC_Hoodie_",               "Hoodie · "),
    ("AC_ShortSleeve_",          "Tee · "),
    ("Election_poker-size_MAY_for-jpegs1-", "Card "),
    ("Election_poker-size_MAY_for-pngs2-",  "Card "),
    ("Slide",                    "Slide "),
]
