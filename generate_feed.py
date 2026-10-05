from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
SOURCE_URL = "https://sevillasecreta.co/escapadas/"
OUTPUT = Path("docs/escapadas.xml")
def main():
    request = Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0 (compatible; SevillaEscapadasRSS/1.0)"})
    with urlopen(request, timeout=30) as response:
        html = response.read()
    soup = BeautifulSoup(html, "html.parser")
    old_dates = {}
    if OUTPUT.exists():
        try:
            previous = ET.parse(OUTPUT).getroot()
            for item in previous.findall("./channel/item"):
                guid = item.findtext("guid")
                pub_date = item.findtext("pubDate")
                if guid and pub_date:
                    old_dates[guid] = pub_date
        except ET.ParseError:
            pass
    channel = ET.Element("rss", {"version": "2.0"})
    body = ET.SubElement(channel, "channel")
    ET.SubElement(body, "title").text = "Sevilla Secreta - Escapadas"
    ET.SubElement(body, "link").text = SOURCE_URL
    ET.SubElement(body, "description").text = "Noticias de la sección Escapadas de Sevilla Secreta"
    ET.SubElement(body, "language").text = "es-ES"
    now = datetime.now(timezone.utc)
    ET.SubElement(body, "lastBuildDate").text = format_datetime(now)
    count = 0
    for article in soup.select("article"):
        category = article.select_one("a.bottom-post-wrapper__category-link[href]")
        title_link = article.select_one("h2 a[href]")
        if not category or "/escapadas/" not in category["href"] or not title_link:
            continue
        title = title_link.get_text(" ", strip=True)
        link = title_link["href"]
        if not title or not link.startswith("https://sevillasecreta.co/"):
            continue
        item = ET.SubElement(body, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = link
        excerpt = article.select_one(".archive__post_description")
        if excerpt:
            ET.SubElement(item, "description").text = excerpt.get_text(" ", strip=True)
        ET.SubElement(item, "category").text = "Escapadas"
        ET.SubElement(item, "pubDate").text = old_dates.get(link, format_datetime(now))
        count += 1
        if count == 10:
            break
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(channel).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(f"Feed actualizado: {count} artículos")
if __name__ == "__main__":
    main()
