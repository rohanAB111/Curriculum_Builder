import re
from typing import Any


def sanitize_latex(text: Any) -> str:
    if text is None:
        return ""
    
    s = str(text)

    s = re.sub(r"^```(?:latex|tex)?\s*", "", s, flags=re.MULTILINE)
    s = re.sub(r"\s*```$", "", s, flags=re.MULTILINE)

    s = s.replace("\t", " ")

    s = s.replace("\\", r"\textbackslash{}")

    special_chars = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for char, replacement in special_chars.items():
        s = s.replace(char, replacement)

    s = s.replace(r"\textbackslash\{\}", r"\textbackslash{}")

    return s.strip()


def sanitize_table_cell(text: Any, max_len: int = 120) -> str:
    clean = sanitize_latex(text)
    if len(clean) > max_len:
        return clean[: max_len - 3] + "..."
    return clean
