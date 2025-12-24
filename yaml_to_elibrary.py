#!/usr/bin/env python3

import yaml
import xml.etree.ElementTree as ET
import sys
import os
import re
from datetime import date


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

    for article, article_en in zip(data["content"], data_en["content"]):
        article_elem = ET.SubElement(articles_elem, "article")
        ET.SubElement(article_elem, "artType").text = "RAR"  # Research Article
        ET.SubElement(article_elem, "pages").text = article["item_pages"].replace("—", "-")

        codes_elem = ET.SubElement(article_elem, "codes")
        ET.SubElement(codes_elem, "doi").text = f"10.17587/prin.{article['doi']}"
        ET.SubElement(codes_elem, "edn").text = article["edn"]

        authors_elem = ET.SubElement(article_elem, "authors")
        for author in article["item_authors_v2"]:
            author_elem = ET.SubElement(authors_elem, "author")
            individ = ET.SubElement(author_elem, "individInfo", lang="ru")
            ET.SubElement(individ, "surname").text = author["last_name"]
            ET.SubElement(individ, "initials").text = author["initials"]

            # TODO: включать все аффилиации, а не только первую?
            aff_idx = author["affiliations"][0] - 1
            ET.SubElement(individ, "orgName").text = article["item_affiliations"][aff_idx]
            ET.SubElement(individ, "email").text = author["email"]

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
        ET.SubElement(dates_elem, "dateReceived").text = article["item_rec_on"].isoformat()
        ET.SubElement(dates_elem, "dateAccepted").text = article["item_acc_on"].isoformat()
        ET.SubElement(dates_elem, "datePublication").text = date(int(year), int(month), 1).isoformat()

    tree = ET.ElementTree(journal)
    ET.indent(tree)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python yaml_to_elibrary.py <input.yaml> <output.xml>")
        sys.exit(1)

    generate_elibrary_xml(sys.argv[1], sys.argv[2])
