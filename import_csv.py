#!/usr/bin/env python3

import json
import csv
import re
import sys
from collections.abc import Iterator
from datetime import date
from difflib import SequenceMatcher
from typing import Any

import yaml

(
    AUTHORS,
    TITLE,
    DATE_RECEIVED,
    DOI,
    LINK,
    REVIEWER,
    CONCLUSION,
    STATUS,
    JOURNAL_NUMBER,
    FILE_NAME,
) = range(10)

dash_re = re.compile(r"[\u2013\u2014-]")  # en dash or em dash

REVIEW_MARKERS = {
    "в представленном варианте не может быть": -1,
    "в таком виде нельзя": -1,
    "вряд ли может быть опубликована": -1,
    "не могу рекомендовать": -1,
    "не может быть опубликована": -1,
    "не может быть принята": -1,
    "не может быть рекомендована": -1,
    "не рекомендуется к публикации": -1,
    "не рекомендуется публиковать": -1,
    "не рекомендую к публикации": -1,
    "нуждается в существенно": -1,
    "статья не может быть": -1,
    "требует переработки": -1,
    "требует серьезной доработки": -1,
    "требуется кардинальная": -1,
    "перед публикацией рекомендуется учесть": 0,
    "после исправления": 0,
    "после их устранения": 0,
    "после переработки": 0,
    "после устранения": 0,
    "рекомендуется доработать": 0,
    "требует доработки": 0,
    "требует небольшой доработки": 0,
    "может быть опубликована": 1,
    "может быть рекомендована": 1,
    "полностью соответствует": 1,
    "рекомендуется к публикации": 1,
    "рекомендую к публикации": 1,
    "статью можно опубликовать": 1,
}


def is_initial(token: str) -> bool:
    return len(token) == 1 or token in ("Ya", "Yu")


def parse_authors(authors: str) -> Iterator[tuple[str, str | None, str]]:
    authors = authors.strip("., ")
    fname = mname = lname = None
    for token in re.split(r"[., ]+", authors):
        if is_initial(token):
            if fname is None:
                fname = token
            else:
                mname = token
                if lname is not None:
                    yield (fname, mname, lname)
                    fname = mname = lname = None
        else:
            if lname is not None:
                yield (fname, mname, lname)
                fname = mname = lname = None
            lname = token
            if fname is not None and lname is not None:
                yield (fname, mname, lname)
                fname = mname = lname = None
    if lname:
        yield (fname, mname, lname)


def run_tests() -> None:
    test_cases = {
        "В.А.Васенин": [
            ("В", "А", "Васенин"),
        ],
        "А.П.Прокопьев А.А.Большаков": [
            ("А", "П", "Прокопьев"),
            ("А", "А", "Большаков"),
        ],
        "Е.А.Басыня Н.Карапетьянц М.Карапетьянц": [
            ("Е", "А", "Басыня"),
            ("Н", None, "Карапетьянц"),
            ("М", None, "Карапетьянц"),
        ],
        "В.С. Корепанова А.А. Меркулов    А. Е. Трубин      А.В. Батищев А.И.Зайцев": [
            ("В", "С", "Корепанова"),
            ("А", "А", "Меркулов"),
            ("А", "Е", "Трубин"),
            ("А", "В", "Батищев"),
            ("А", "И", "Зайцев"),
        ],
        "Kol'chugina E. A.": [
            ("E", "A", "Kol'chugina"),
        ],
        "Abdullin A. M., Itsykson V. M.": [
            ("A", "M", "Abdullin"),
            ("V", "M", "Itsykson"),
        ],
        "I.Kovalchuk L.Zhukova A.Kochnev V.Chugunov": [
            ("I", None, "Kovalchuk"),
            ("L", None, "Zhukova"),
            ("A", None, "Kochnev"),
            ("V", None, "Chugunov"),
        ],
        "Vorobyev A Makeev S": [
            ("A", None, "Vorobyev"),
            ("S", None, "Makeev"),
        ],
        "O. A. Malafeyev, S. A. ALManai,": [
            ("O", "A", "Malafeyev"),
            ("S", "A", "ALManai"),
        ],
        "Voyakovskaya Ya.S": [
            ("Ya", "S", "Voyakovskaya"),
        ],
    }
    for source, expected in test_cases.items():
        result = list(parse_authors(source))
        assert result == expected, f"{result} != {expected}"


def find_article(title: str, number: int, year: int) -> dict[str, Any] | None:
    volume = year - 2009
    with open(f"content/rus/issues/{volume}_{number}_{year}.yaml") as fp:
        content = yaml.safe_load(fp)["content"]
        for item in content:
            matcher = SequenceMatcher(None, item["item_name"].lower(), title.lower())
            if matcher.ratio() >= 0.8:
                first_page, last_page = dash_re.split(item["item_pages"])
                return {
                    "DOI": f"10.17587/prin.{item['doi']}",
                    "EDN": item.get("edn"),
                    "Volume": str(volume),
                    "Issue": str(number),
                    "Year": year,
                    "FirstPage": first_page,
                    "LastPage": last_page,
                    "ReceivedDate": item["item_rec_on"],
                    "AcceptedDate": item["item_acc_on"],
                }


def process_file(filename: str) -> None:
    entries = []
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if not any(row):
                continue
            if row[AUTHORS] == "Авторы":
                continue
            if any(row[:4]):
                title = row[TITLE].strip().replace("\n", " ")
                if not title:
                    continue
                number = row[JOURNAL_NUMBER].lstrip("№.").replace(" ", "")
                number_parts = number.split(",")
                article = None
                if len(number_parts) == 2:
                    number = int(number_parts[0])
                    year = int(number_parts[1])
                    article = find_article(title, number, year)
                if article:
                    date_received = article.pop("ReceivedDate") if article else None
                    date_accepted = article.pop("AcceptedDate") if article else None
                else:
                    try:
                        date_received = date.strptime(row[DATE_RECEIVED], "%m/%d/%Y")
                    except ValueError:
                        date_received = None
                    date_accepted = None
                entry = {
                    "Title": title,
                    "ReceivedDate": (
                        date_received.isoformat() if date_received else None
                    ),
                    "AcceptedDate": (
                        date_accepted.isoformat() if date_accepted else None
                    ),
                    "Authors": [
                        {
                            "LastName": lname,
                            "FirstName": fname,
                            "MiddleName": mname,
                        }
                        for fname, mname, lname in parse_authors(row[AUTHORS])
                    ],
                    "Article": article,
                    "Reviews": [],
                }
                entries.append(entry)
            else:
                entry = entries[-1]
            if not (reviewers := list(parse_authors(row[REVIEWER]))):
                continue
            reviewer = reviewers[0]
            normalized_text = (
                row[CONCLUSION].strip().lower().replace("\n", " ").replace("ё", "е")
            )
            conclusion = 0
            for substring, substring_conclusion in REVIEW_MARKERS.items():
                if substring in normalized_text:
                    conclusion = substring_conclusion
                    break
            entry["Reviews"].append(
                {
                    "Reviewer": {
                        "LastName": reviewer[2],
                        "FirstName": reviewer[0],
                        "MiddleName": reviewer[1],
                    },
                    "Text": row[CONCLUSION].strip(),
                    "Conclusion": conclusion,
                    "NeedsChanges": conclusion <= 0,
                }
            )

    data = {
        "JournalName": "Программная инженерия",
        "JournalISSN": ["2220-3397"],
        "RequestedArticles": entries,
    }
    with open("requested_articles.json", "w") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    run_tests()
    process_file(sys.argv[1])
