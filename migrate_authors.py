#!/usr/bin/env python3

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq
from pathlib import Path
import re


yaml = YAML()
yaml.preserve_quotes = True
yaml.explicit_start = True
yaml.default_flow_style = False
yaml.width = 1000
yaml.indent(mapping=2, sequence=3, offset=1)


SUP_AUTHOR_RE = re.compile(r"<b>(.*?)</b>(.*</sup>).*, ([^ ]+@[^\s,]+)")
SUP_RE = re.compile("<sup>(.*?)</sup>")
SUP_AFF_RE = re.compile(r"\n<sup>(\d+)</sup>\s*(.+)")


def parse_name(name: str) -> dict[str, str]:
    initials, last_name = name.rsplit(maxsplit=1)
    assert len(initials) in (2, 5), f"Cannot parse name: {name}"
    assert initials.endswith("."), f"Cannot parse name: {name}"
    return {"last_name": last_name, "initials": initials}


def migrate_item(item):
    if "item_authors_v2" in item:
        return

    raw_addr = item["item_authors_address"]

    affiliations = []
    if "<sup>" in raw_addr:
        authors_v2 = [
            {
                **parse_name(m.group(1).strip()),
                "email": m.group(3),
                "affiliations": [
                    int(n.strip())
                    for m2 in SUP_RE.finditer(m.group(2))
                    for n in m2.group(1).split(",")
                ],
            }
            for m in SUP_AUTHOR_RE.finditer(raw_addr)
        ]
        affiliations = []
        for ix, m in enumerate(SUP_AFF_RE.finditer(raw_addr), start=1):
            assert int(m.group(1)) == ix
            affiliations.append(m.group(2))
    else:
        authors_v2 = []
        for line in raw_addr.splitlines():
            if line.startswith("<b>"):
                line = line.removeprefix("<b>")
                authors_v2.append(
                    {
                        **parse_name(line[: line.find("</b>")]),
                        "email": line.rstrip(",").split()[-1],
                        "affiliations": [len(affiliations) + 1],
                    }
                )
            else:
                affiliations.append(line.rstrip(","))

    assert authors_v2, f"Cannot parse authors: {raw_addr = }"

    for author in authors_v2:
        email = author["email"]
        assert "@" in email, email
        assert " " not in email, email
        assert "\n" not in email, email

        seq = CommentedSeq(author["affiliations"])
        seq.fa.set_flow_style()
        author["affiliations"] = seq

    keys = list(item.keys())
    idx = keys.index("item_authors_address")
    item.insert(idx + 1, "item_authors_v2", authors_v2)
    item.insert(idx + 2, "item_affiliations", affiliations)


def migrate_file(path: Path):
    data = yaml.load(path.read_text(encoding="utf-8"))

    for item in data.get("content", []):
        migrate_item(item)

    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: migrate_authors.py issue.yaml")
        sys.exit(1)

    migrate_file(Path(sys.argv[1]))
