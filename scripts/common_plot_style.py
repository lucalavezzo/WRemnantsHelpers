CMS_DEFAULT_COLORS_SHORT = [
    "#5790fc",
    "#f89c20",
    "#e42536",
    "#964a8b",
    "#9c9ca1",
    "#7a21dd",
]

CMS_DEFAULT_COLORS = [
    "#3f90da",
    "#ffa90e",
    "#bd1f01",
    "#94a4a2",
    "#832db6",
    "#a96b59",
    "#e76300",
    "#b9ac70",
    "#717581",
    "#92dadd",
]


def build_cms_color_cycle(n):
    palette = CMS_DEFAULT_COLORS_SHORT if n <= 6 else CMS_DEFAULT_COLORS
    return [palette[i % len(palette)] for i in range(n)]
