#!/usr/bin/env python3

import yaml
import xml.etree.ElementTree as ET
import sys
import os
import re
from datetime import datetime


def generate_elibrary_xml(yaml_file, output_file):
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    yaml_en_file = yaml_file.replace("/rus/", "/eng/")
    with open(yaml_en_file, "r", encoding="utf-8") as f:
        data_en = yaml.safe_load(f)

    basename = os.path.basename(yaml_file)
    name_part = os.path.splitext(basename)[0]
    volume, month, year = name_part.split("_")

    journal = ET.Element("journal")
    ET.SubElement(journal, "issn").text = "2220-3397"

    journal_info = ET.SubElement(journal, "journalInfo", lang="ru")
    ET.SubElement(journal_info, "title").text = "Программная инженерия"
    ET.SubElement(journal_info, "Title").text = "Software Engineering"
    ET.SubElement(journal_info, "publ").text = "Новые технологии"

    issue = ET.SubElement(journal, "issue")
    ET.SubElement(issue, "volume").text = volume
    ET.SubElement(issue, "number").text = month
    ET.SubElement(issue, "dateUni").text = year

    first_page, _ = data["content"][0]["item_pages"].split("—")
    _, last_page = data["content"][-1]["item_pages"].split("—")
    ET.SubElement(issue, "pages").text = f"{first_page}-{last_page}"

    articles_elem = ET.SubElement(issue, "articles")

    assert len(data["content"]) == len(data_en["content"])
    for article, article_en in zip(data["content"], data_en["content"]):
        if "doi" not in article:
            assert article["item_name"].startswith("Указатель")
            continue

        article_elem = ET.SubElement(articles_elem, "article")
        ET.SubElement(article_elem, "artType").text = "RAR"  # Research Article
        ET.SubElement(article_elem, "pages").text = article["item_pages"].replace("—", "-")

        codes_elem = ET.SubElement(article_elem, "codes")
        ET.SubElement(codes_elem, "doi").text = f"10.17587/prin.{article['doi']}"
        ET.SubElement(codes_elem, "edn").text = article["edn"]

        authors_elem = ET.SubElement(article_elem, "authors")

        authors_ru = article["item_authors_v2"]
        authors_en = article_en["item_authors_v2"]
        if len(authors_ru) != len(authors_en):
            msg = f"Number of authors mismatch: {authors_ru} vs. {authors_en}"
            raise AssertionError(msg)
        for author, author_en in zip(authors_ru, authors_en):
            if author["email"] != author_en["email"]:
                raise AssertionError(f"Email mismatch: {author} vs. {author_en}")
            if len(author["affiliations"]) != len(author_en["affiliations"]):
                msg = f"Number of affiliations mismatch: {author} vs. {author_en}"
                raise AssertionError(msg)

            author_elem = ET.SubElement(authors_elem, "author")
            individ = ET.SubElement(author_elem, "individInfo", lang="ru")
            ET.SubElement(individ, "surname").text = author["last_name"]
            ET.SubElement(individ, "initials").text = author["initials"]

            # TODO: включать все аффилиации, а не только первую?
            aff_idx = author["affiliations"][0] - 1
            ET.SubElement(individ, "orgName").text = article["item_affiliations"][aff_idx]
            ET.SubElement(individ, "email").text = author["email"]

            individ_en = ET.SubElement(author_elem, "individInfo", lang="en")
            ET.SubElement(individ_en, "surname").text = author_en["last_name"]
            ET.SubElement(individ_en, "initials").text = author_en["initials"]

            aff_idx = author_en["affiliations"][0] - 1
            ET.SubElement(individ_en, "orgName").text = article_en["item_affiliations"][aff_idx]
            ET.SubElement(individ_en, "email").text = author_en["email"]

        art_titles = ET.SubElement(article_elem, "artTitles")
        ET.SubElement(art_titles, "artTitle", lang="ru").text = article["item_name"]
        ET.SubElement(art_titles, "artTitle", lang="en").text = article_en["item_name"]

        abstracts_elem = ET.SubElement(article_elem, "abstracts")
        abstract_elem = ET.SubElement(abstracts_elem, "abstract", lang="ru")
        clean_text = re.sub("<[^>]+>", "", article["item_annot"])
        abstract_elem.text = clean_text.strip()

        abstract_en_elem = ET.SubElement(abstracts_elem, "abstract", lang="en")
        clean_text = re.sub("<[^>]+>", "", article_en["item_annot"])
        abstract_en_elem.text = clean_text.strip()

        keywords_elem = ET.SubElement(article_elem, "keywords")
        kwd_group = ET.SubElement(keywords_elem, "kwdGroup", lang="ru")
        for kwd in article["item_keywords"].split(","):
            ET.SubElement(kwd_group, "keyword").text = kwd.strip()

        kwd_en_group = ET.SubElement(keywords_elem, "kwdGroup", lang="en")
        for kwd in article_en["item_keywords"].split(","):
            ET.SubElement(kwd_en_group, "keyword").text = kwd.strip()

        dates_elem = ET.SubElement(article_elem, "dates")
        item_rec_on = datetime.strptime(article_en["item_rec_on"], "%B %d, %Y").date()
        item_acc_on = datetime.strptime(article_en["item_acc_on"], "%B %d, %Y").date()
        ET.SubElement(dates_elem, "dateReceived").text = item_rec_on.isoformat()
        ET.SubElement(dates_elem, "dateAccepted").text = item_acc_on.isoformat()
        ET.SubElement(dates_elem, "datePublication").text = data["date"].isoformat()

    tree = ET.ElementTree(journal)
    ET.indent(tree)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python yaml_to_elibrary.py <input.yaml> <output.xml>")
        sys.exit(1)

    generate_elibrary_xml(sys.argv[1], sys.argv[2])
