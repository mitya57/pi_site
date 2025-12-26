#!/usr/bin/env python3

from os.path import abspath
import re

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq


yaml = YAML()
yaml.preserve_quotes = True
yaml.explicit_start = True
yaml.default_flow_style = False
yaml.width = 1000
yaml.indent(mapping=2, sequence=3, offset=1)


SUP_AUTHOR_RE = re.compile(r"<b>(.*?)</b>(.*</sup>).*, ([^ ]+@[^\s,]+)")
SUP_RE = re.compile("<sup>(.*?)</sup>")
SUP_AFF_RE = re.compile(r"\n<sup>(\d+)</sup>\s*(.+)")
INITIALS_RE = re.compile(r"^([А-Я]\.( [А-Я].)?|[A-Z][a-z]?\.( [A-Z][a-z]?\.)?)$")


def parse_name(name: str) -> dict[str, str]:
    initials, last_name = name.rsplit(maxsplit=1)
    assert INITIALS_RE.match(initials), f"Cannot parse name: {name}"
    return {"last_name": last_name, "initials": initials}


def migrate_item(item):
    if "item_authors_v2" in item:
        return
    if "item_authors_address" not in item:
        assert item["item_name"].startswith(("Указатель", "Index"))
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
            affiliations.append(m.group(2).rstrip(","))
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


def migrate_file(path: str):
    with open(path) as fp:
        data = yaml.load(fp)

    for item in data["content"]:
        migrate_item(item)

    with open(path, "w") as f:
        yaml.dump(data, f)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: migrate_authors.py issue.yaml")
        sys.exit(1)

    migrate_file(abspath(sys.argv[1]))
