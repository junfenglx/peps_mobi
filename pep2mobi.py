# coding: utf-8

import uuid
import datetime
import os.path
import subprocess
import traceback


import bs4
from tornado import template

PEP_DIR = "peps"
def get_peps_index():
    a_set = set()
    pep_index = os.path.join(PEP_DIR, "pep-0000.html")
    with open(pep_index, "r") as f:
        soup = bs4.BeautifulSoup(f.read(), "lxml")
    for a in soup.find_all("a"):
        href = a.get("href")
        if href.startswith("pep-") and href.endswith(".html"):
            a_set.add(href)
    return a_set

def parse_pep_html(index):
    filename = os.path.join(PEP_DIR, index)
    print("parsing %s" % filename)
    content = ""
    with open(filename, "r") as f:
        content = f.read()
    soup = bs4.BeautifulSoup(content, "lxml")
    nav = soup.find("table", class_="navigation")
    if nav:
        nav.decompose()
    # try find title
    title = {}
    title["id"] = index.split(".", 1)[0]
    title["text"] = index.split(".", 1)[0]
    try:
        title_th = soup.find("th", text=["Title:", "Title:\xc2\xa0"])
        title_td = title_th.next_sibling
        title["text"] = title["text"] + " " + title_td.text
    except Exception as e:
        traceback.print_exc()
    # handle anchor reference
    tag_as = soup.find_all("a")
    for a in tag_as:
        href = a.get("href")
        if href.startswith("#"):
            # correct id and href
            old_id = href[1:]
            new_id = title["id"] + "-" + old_id
            a["href"] = "#" + new_id
            tag = soup.find(id=old_id)
            if tag:
                tag["id"] = new_id
    print(title["text"])
    content = u"".join([unicode(t) for t in soup.body.contents])
    return (title, content)
def get_contents(indexs):
    titles = []
    chapters = []
    for index in indexs:
        title, content = parse_pep_html(index)
        titles.append(title)
        chapter = dict(title=title, content=content)
        chapters.append(chapter)
    return titles, chapters


def build(titles, chapters):
    book_dir = "."
    book_name = "Python Enhancement Proposals"
    print("building %s ..." % book_name)
    book_author="junfeng"
    uid=uuid.uuid1()

    content_path = os.path.join(book_dir, "content.html")
    toc_path = os.path.join(book_dir, "toc.html")
    toc_ncx_path = os.path.join(book_dir, "toc.ncx")
    book_opf_path = os.path.join(book_dir, "book.opf")

    loader=template.Loader("template/")
    with open(content_path, "wb") as f:
        f.write(loader.load("content.html").generate(
            book_name=book_name, chapters=chapters))
    with open(toc_path, "wb") as f:
        f.write(loader.load("toc.html").generate(titles=titles))
    with open(toc_ncx_path, "wb") as f:
        f.write(loader.load("toc.ncx").generate(
            book_name=book_name, book_author=book_author,
            uid=uid, titles=titles))
    with open(book_opf_path, "wb") as f:
        f.write(loader.load("book.opf").generate(
            book_name=book_name, book_author=book_author,
            uid=uid, titles=titles))

    # output mobi file
    output_mobi = book_name + ".mobi"
    print("generating mobi file, please wait...")
    cmd = ["kindlegen", book_opf_path, "-c2", "-o", output_mobi]
    print(" ".join(cmd))
    subprocess.call(cmd)
    print("done")

def main():
    indexs = list(get_peps_index())
    indexs = sorted(indexs)
    titles, chapters = get_contents(indexs)
    build(titles, chapters)

if __name__ == "__main__":
    main()
