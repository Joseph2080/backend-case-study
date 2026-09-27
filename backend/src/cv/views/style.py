from typing import Literal, cast, get_args

CVDatePosition = Literal["leading", "trailing"]
CVTextAlignment = Literal["leading", "justify"]
CVFontFamily = Literal[
    "inter",
    "source-sans-3",
    "ibm-plex-sans",
    "noto-sans",
    "georgia",
    "lato",
    "merriweather",
    "libre-franklin",
]

ALL_CV_DATE_POSITIONS = cast(list[CVDatePosition], list(get_args(CVDatePosition)))
ALL_CV_TEXT_ALIGNMENTS = cast(list[CVTextAlignment], list(get_args(CVTextAlignment)))
ALL_CV_FONT_FAMILIES = cast(list[CVFontFamily], list(get_args(CVFontFamily)))
