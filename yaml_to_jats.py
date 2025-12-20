#!/usr/bin/env python3

import html
import os
import re
import sys
import xml.etree.ElementTree as ET
import yaml


def create_article_xml(article_data, idx, issue_info):
    article_root = ET.Element(
        "article",
        {
            "xmlns": "http://jats.nlm.nih.gov",
            "xmlns:xlink": "http://www.w3.org/1999/xlink",
            "dtd-version": "1.4",
            "article-type": "research-article",
            "xml:lang": "ru",
            "id": f"art{idx}",
        },
    )

    front = ET.SubElement(article_root, "front")

    journal_meta = ET.SubElement(front, "journal-meta")
    journal_id = ET.SubElement(
        journal_meta, "journal-id", {"journal-id-type": "publisher"}
    )
    journal_id.text = "Программная инженерия"

    journal_title_group = ET.SubElement(journal_meta, "journal-title-group")
    ET.SubElement(journal_title_group, "journal-title").text = "Программная инженерия"

    trans_title_group = ET.SubElement(journal_title_group, "trans-title-group")
    ET.SubElement(trans_title_group, "trans-title", {"xml:lang": "en"}).text = (
        "Software Engineering"
    )

    ET.SubElement(journal_meta, "issn", {"pub-type": "ppub"}).text = "2220-3397"

    publisher = ET.SubElement(journal_meta, "publisher")
    ET.SubElement(publisher, "publisher-name").text = "Новые технологии"

    issue_meta = ET.SubElement(front, "issue-meta")
    ET.SubElement(issue_meta, "volume").text = issue_info["volume"]
    ET.SubElement(issue_meta, "issue").text = issue_info["issue"]

    pub_date = ET.SubElement(issue_meta, "pub-date", {"pub-type": "pub"})
    ET.SubElement(pub_date, "year").text = issue_info["year"]
    ET.SubElement(pub_date, "month").text = issue_info["issue"]

    article_meta = ET.SubElement(front, "article-meta")

    ET.SubElement(article_meta, "article-id", {"pub-id-type": "doi"}).text = (
        f"10.17587/prin.{article_data['doi']}"
    )

    if edn := article_data.get("edn"):
        ET.SubElement(
            article_meta, "article-id", {"pub-id-type": "other", "specific-use": "edn"}
        ).text = edn

    title_group = ET.SubElement(article_meta, "title-group")
    ET.SubElement(title_group, "article-title").text = article_data["item_name"]

    contrib_group = ET.SubElement(article_meta, "contrib-group")

    for author_data in article_data["item_authors_v2"]:
        contrib = ET.SubElement(contrib_group, "contrib", {"contrib-type": "author"})
        name = ET.SubElement(contrib, "name")
        ET.SubElement(name, "surname").text = author_data["last_name"]
        ET.SubElement(name, "given-names").text = author_data["initials"]
        ET.SubElement(contrib, "email").text = author_data["email"]

        for aff_index in author_data["affiliations"]:
            ET.SubElement(
                contrib, "xref", {"ref-type": "aff", "rid": f"aff{idx}_{aff_index}"}
            )

    for aff_idx, affiliation in enumerate(article_data["item_affiliations"], 1):
        aff = ET.SubElement(article_meta, "aff", {"id": f"aff{idx}_{aff_idx}"})
        ET.SubElement(aff, "label").text = str(aff_idx)
        ET.SubElement(aff, "institution").text = affiliation

    pub_history = ET.SubElement(article_meta, "history")

    date_rec = ET.SubElement(pub_history, "date", {"date-type": "received"})
    item_rec_on = article_data["item_rec_on"]
    ET.SubElement(date_rec, "year").text = str(item_rec_on.year)
    ET.SubElement(date_rec, "month").text = str(item_rec_on.month)
    ET.SubElement(date_rec, "day").text = str(item_rec_on.day)

    date_acc = ET.SubElement(pub_history, "date", {"date-type": "accepted"})
    item_acc_on = article_data["item_acc_on"]
    ET.SubElement(date_acc, "year").text = str(item_acc_on.year)
    ET.SubElement(date_acc, "month").text = str(item_acc_on.month)
    ET.SubElement(date_acc, "day").text = str(item_acc_on.day)

    date_pub = ET.SubElement(pub_history, "date", {"date-type": "published"})
    ET.SubElement(date_pub, "year").text = issue_info["year"]
    ET.SubElement(date_pub, "month").text = issue_info["issue"]

    permissions = ET.SubElement(article_meta, "permissions")
    ET.SubElement(permissions, "copyright-statement").text = (
        f"© {issue_info['year']} Новые технологии"
    )
    ET.SubElement(permissions, "copyright-year").text = issue_info["year"]
    ET.SubElement(permissions, "copyright-holder").text = "Новые технологии"

    abstract = ET.SubElement(article_meta, "abstract")
    annot_text = article_data["item_annot"]

    for match in re.findall(r"<p>(.*?)</p>", annot_text, re.DOTALL):
        para_text = html.unescape(match.strip())
        para_text = re.sub(r"<[^>]+>", "", para_text)
        ET.SubElement(abstract, "p").text = para_text.strip()

    kwd_group = ET.SubElement(article_meta, "kwd-group", {"kwd-group-type": "author"})
    for kwd in article_data["item_keywords"].split(","):
        ET.SubElement(kwd_group, "kwd").text = kwd.strip()

    counts = ET.SubElement(article_meta, "counts")
    fpage, lpage = article_data["item_pages"].split("—")
    ET.SubElement(counts, "page-count", {"count": str(int(lpage) - int(fpage) + 1)})
    ET.SubElement(article_meta, "fpage").text = fpage
    ET.SubElement(article_meta, "lpage").text = lpage

    custom_meta_group = ET.SubElement(article_meta, "custom-meta-group")
    custom_meta = ET.SubElement(custom_meta_group, "custom-meta")
    ET.SubElement(custom_meta, "meta-name").text = "UDK"
    ET.SubElement(custom_meta, "meta-value").text = article_data["udk"]

    body = ET.SubElement(article_root, "body")
    sec = ET.SubElement(body, "sec", {"id": f"s{idx}"})
    ET.SubElement(sec, "title").text = article_data["item_name"]
    ET.SubElement(sec, "p").text = (
        "Полный текст статьи доступен в печатной версии журнала."
    )

    back = ET.SubElement(article_root, "back")
    ref_list = ET.SubElement(back, "ref-list")
    ref = ET.SubElement(ref_list, "ref", {"id": "ref-self"})
    citation = ET.SubElement(ref, "element-citation", {"publication-type": "journal"})

    authors_list = []
    for author in article_data["item_authors_v2"]:
        authors_list.append(f"{author['last_name']} {author['initials']}")
    authors_str = ", ".join(authors_list)

    ET.SubElement(citation, "person-group", {"person-group-type": "author"}).text = (
        authors_str
    )
    ET.SubElement(citation, "article-title").text = article_data["item_name"]
    ET.SubElement(citation, "source").text = "Программная инженерия"
    ET.SubElement(citation, "year").text = issue_info["year"]
    ET.SubElement(citation, "volume").text = issue_info["volume"]
    ET.SubElement(citation, "issue").text = issue_info["issue"]

    fpage, lpage = article_data["item_pages"].split("—")
    ET.SubElement(citation, "fpage").text = fpage
    ET.SubElement(citation, "lpage").text = lpage

    ET.SubElement(citation, "pub-id", {"pub-id-type": "doi"}).text = (
        f"10.17587/prin.{article_data['doi']}"
    )
    return article_root


def generate_issue_manifest(article_files, issue_info, output_file_path):
    root = ET.Element(
        "issue-collection",
        {
            "xmlns": "http://jats.nlm.nih.gov",
            "xmlns:xlink": "http://www.w3.org/1999/xlink",
            "dtd-version": "1.4",
            "xml:lang": "ru",
        },
    )

    issue_meta = ET.SubElement(root, "issue-meta")
    journal_id = ET.SubElement(
        issue_meta, "journal-id", {"journal-id-type": "publisher"}
    )
    journal_id.text = "Программная инженерия"
    ET.SubElement(issue_meta, "journal-title").text = "Программная инженерия"
    ET.SubElement(issue_meta, "volume").text = issue_info["volume"]
    ET.SubElement(issue_meta, "issue").text = issue_info["issue"]

    pub_date = ET.SubElement(issue_meta, "pub-date")
    ET.SubElement(pub_date, "year").text = issue_info["year"]
    ET.SubElement(pub_date, "month").text = issue_info["issue"]

    article_list = ET.SubElement(root, "article-list")

    for idx, article_file in enumerate(article_files, 1):
        article_ref = ET.SubElement(article_list, "article-ref", {"id": f"art{idx}"})
        ET.SubElement(
            article_ref,
            "file-ref",
            {"xlink:href": article_file, "xlink:title": f"Article {idx}"},
        )

    tree = ET.ElementTree(root)
    ET.indent(tree)
    with open(output_file_path, "wb") as fp:
        tree.write(fp, encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("Usage: python yaml_to_jats.py <input_yaml_file>")
        sys.exit(1)

    input_yaml = sys.argv[1]

    basename = os.path.basename(input_yaml)
    name_part = os.path.splitext(basename)[0]
    volume, issue, year = name_part.split("_")

    issue_info = {
        "volume": volume,
        "issue": issue,
        "year": year,
    }
    print(f"Processing: Volume {volume}, Issue {issue}, Year {year}")

    with open(input_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    base_name = os.path.splitext(input_yaml)[0]

    article_files = []
    for idx, article_data in enumerate(data["content"], 1):
        article_xml = create_article_xml(article_data, idx, issue_info)
        article_filename = f"{base_name}_article_{idx:02d}.xml"

        tree = ET.ElementTree(article_xml)
        ET.indent(tree)
        with open(article_filename, "wb") as fp:
            tree.write(fp, encoding="utf-8")
        article_files.append(article_filename)

    manifest_file = f"{base_name}_jats14_manifest.xml"
    generate_issue_manifest(article_files, issue_info, manifest_file)

    print(f"\nCreated {len(article_files)} article files:")
    for file in article_files:
        print(f"  - {file}")
    print(f"And manifest file: {manifest_file}")


if __name__ == "__main__":
    main()
