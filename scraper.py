import re
import os
import time
import json
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
from collections import deque, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz
import pandas as pd
import requests

from bs4 import BeautifulSoup
from rapidfuzz import fuzz


"""
Italian University Sustainability Intelligence Scraper
=====================================================

PURPOSE
-------
This script recursively explores sustainability-related university pages
and sustainability PDFs for Italian universities.

FEATURES
--------
- Recursive sustainability crawling
- Manual sustainability root URLs
- Sustainability PDF discovery
- PDF text extraction
- SDG thematic analysis
- Governance analysis
- Sustainability discourse extraction
- Word frequency / thematic profiling
- Transparency evidence modelling
- Parallel processing

IMPORTANT
---------
This is NOT a ranking engine.
It is an evidence discovery + sustainability intelligence system.

The script separates:
- evidence found
from:
- institutional quality

OUTPUTS
-------
- italian_university_sustainability.csv
- italian_university_sustainability.json

INSTALL
-------
pip install:
    pandas
    requests
    beautifulsoup4
    lxml
    rapidfuzz
    pymupdf
"""


# ============================================================
# CONFIG
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 20
SLEEP_TIME = 0.5

MAX_DEPTH = 2
MAX_PAGES = 40
MAX_CANDIDATES = 20
MAX_WORKERS = 8

CURRENT_YEAR = datetime.now().year


# ============================================================
# UTILITIES
# ============================================================

def pretty_print(message, level="INFO"):

    timestamp = datetime.now().strftime("%H:%M:%S")

    print(f"[{timestamp}] [{level}] {message}")


def safe_len(obj):

    try:
        return len(obj)
    except Exception:
        return 0


# ============================================================
# UNIVERSITY LIST
# ============================================================

UNIVERSITIES = [
    "Bari",
    "Basilicata",
    "Bergamo",
    "Bologna",
    "Cagliari",
    "Camerino",
    "Chieti e Pescara",
    "Ferrara",
    "Firenze",
    "Foggia",
    "Genova",
    "Insubria",
    "L'Aquila",
    "Macerata",
    "Marche Politecnica",
    "Milano",
    "Milano Bicocca",
    "Milano Politecnico",
    "Modena e Reggio Emilia",
    "Padova",
    "Parma",
    "Piemonte Orientale",
    "Roma Tre",
    "Salerno",
    "Torino",
    "Torino Politecnico",
    "Tuscia",
    "Urbino",
    "Venezia Iuav"
]


# ============================================================
# UNIVERSITY URLS
# ============================================================

UNIVERSITY_URLS = {
    "Bari": "https://www.uniba.it",
    "Basilicata": "https://www.unibas.it",
    "Bergamo": "https://www.unibg.it",
    "Bologna": "https://www.unibo.it",
    "Cagliari": "https://www.unica.it",
    "Camerino": "https://www.unicam.it",
    "Chieti e Pescara": "https://www.unich.it",
    "Ferrara": "https://www.unife.it",
    "Firenze": "https://www.unifi.it",
    "Foggia": "https://www.unifg.it",
    "Genova": "https://unige.it",
    "Insubria": "https://www.uninsubria.it",
    "L'Aquila": "https://www.univaq.it",
    "Macerata": "https://www.unimc.it",
    "Marche Politecnica": "https://www.univpm.it",
    "Milano": "https://www.unimi.it",
    "Milano Bicocca": "https://www.unimib.it",
    "Milano Politecnico": "https://www.polimi.it",
    "Modena e Reggio Emilia": "https://www.unimore.it",
    "Padova": "https://www.unipd.it",
    "Parma": "https://www.unipr.it",
    "Piemonte Orientale": "https://www.uniupo.it",
    "Roma Tre": "https://www.uniroma3.it",
    "Salerno": "https://www.unisa.it",
    "Torino": "https://www.unito.it",
    "Torino Politecnico": "https://www.polito.it",
    "Tuscia": "https://www.unitus.it",
    "Urbino": "https://www.uniurb.it",
    "Venezia Iuav": "https://www.iuav.it",
}


# ============================================================
# MANUAL ROOTS
# ============================================================

MANUAL_ROOTS = {

    "Bari": [
        "https://www.uniba.it/en/university/university-overview/university-in-figures/sustainability"
    ],

    "Basilicata": [
        "https://www.unibas.it"
    ],

    "Bergamo": [
        "https://en.unibg.it/university/about-us/sustainability-at-unibg"
    ],

    "Bologna": [
        "https://magazine.unibo.it/en/articles/the-2025-sustainability-report-of-the-university-of-bologna-is-now-online"
    ],

    "Cagliari": [
        "https://en.unica.it/en/university/sustainability"
    ],

    "Camerino": [
        "https://sbmv.unicam.it/en/research/environmental-sustainability"
    ],

    "Ferrara": [
        "https://www.unife.it/studenti/dottorato/it/corsi/riforma/environmental-sustainability-and-wellbeing"
    ],

    "Firenze": [
        "https://www.unifi.it/sites/default/files/2025-12/bilancio_sociale_sostenibilita_2024_eng.pdf"
    ],

    "Foggia": [
        "https://www.unifg.it/en/third-mission/partnerships-and-collaborations/environmental-sustainability"
    ],

    "Genova": [
        "https://unigesostenibile.unige.it/en/Bilancio"
    ],

    "Insubria": [
        "https://www.uninsubria.eu/third-mission/uninsubria-and-society/uninsubria-sustainability"
    ],

    "L'Aquila": [
        "https://www.univaq.it/section.php?id=2100"
    ],

    "Macerata": [
        "https://giurisprudenza.unimc.it/en/third-mission/sustainability"
    ],

    "Marche Politecnica": [
        "https://www.univpm.it/Entra/Engine/RAServeFile.php/f/univpm_sostenibile/univpm_it_factfile_2024_full.pdf"
    ],

    "Milano": [
        "https://www.unimi.it/en/university/la-statale/sustainability-university-milan"
    ],

    "Milano Bicocca": [
        "https://en.unimib.it/about-us/bicocca-sustainability-project"
    ],

    "Milano Politecnico": [
        "https://www.polimi.it/en/the-politecnico/about-polimi/strategic-documents/sustainability-plan"
    ],

    "Padova": [
        "https://www.sostenibile.unipd.it/en/commitment/sustainability-report/"
    ],

    "Parma": [
        "https://www.unipr.it/en/node/106422"
    ],

    "Piemonte Orientale": [
        "https://www.uniupo.it/en/third-mission/sustainable-upo"
    ],

    "Roma Tre": [
        "https://www.uniroma3.it/int/about-us/sustainable-roma-tre/governance-sustainability/sustainability-report/"
    ],

    "Torino": [
        "https://unifind.unito.it/resource/item/429752?language=en-US"
    ],

    "Torino Politecnico": [
        "https://www.polito.it/en/polito/sustainable-campus/reports-and-documents"
    ],

    "Tuscia": [
        "https://www.unitus.it/en/third-mission/social-inclusion-and-sustainability/"
    ],

    "Venezia Iuav": [
        "https://1future.feut.edu.al/wp-content/uploads/2023/11/1FUTURE-IUAV-Survey.pdf"
    ]
}


# ============================================================
# SEARCH TERMS
# ============================================================

SEARCH_TERMS = [
    "sustainability",
    "sostenibilità",
    "sostenibilita",
    "sdg",
    "agenda 2030",
    "esg",
    "climate",
    "decarbonisation",
    "carbon neutrality",
    "net zero",
    "green office",
    "environment",
    "environmental sustainability",
    "social responsibility",
    "responsabilità sociale",
    "governance",
    "third mission",
    "terza missione",
    "sustainable campus",
    "bilancio",
    "bilancio sociale",
    "bilancio di sostenibilità",
    "sustainability report",
    "impact report",
    "transition",
    "ecological transition",
    "transizione ecologica",
    "wellbeing",
    "diversity",
    "inclusion",
    "mobility",
    "energy",
    "emissions",
    "waste",
    "water",
    "biodiversity",
]


ALLOWED_PATH_HINTS = [
    "sustain",
    "sdg",
    "agenda",
    "bilancio",
    "green",
    "environment",
    "climate",
    "governance",
    "mission",
    "responsibility",
    "esg",
    "report",
    "sosten",
]


STOPWORDS = {
    "della",
    "delle",
    "degli",
    "dell",
    "dello",
    "sustainability",
    "sostenibilità",
    "sostenibilita",
    "university",
    "università",
    "universita",
    "research",
    "student",
    "students",
    "faculty",
    "department",
    "mission",
    "third",
    "terza",
    "agenda",
}


SDG_TERMS = {

    "SDG3_Health": [
        "health",
        "wellbeing",
    ],

    "SDG4_Education": [
        "education",
        "teaching",
        "curriculum",
    ],

    "SDG5_Gender": [
        "gender",
        "equality",
        "inclusion",
    ],

    "SDG7_Energy": [
        "energy",
        "renewable",
        "solar",
    ],

    "SDG11_Cities": [
        "mobility",
        "urban",
    ],

    "SDG12_Consumption": [
        "waste",
        "recycling",
    ],

    "SDG13_Climate": [
        "climate",
        "carbon",
        "emissions",
        "net zero",
    ],

    "SDG16_Governance": [
        "governance",
        "transparency",
        "committee",
    ]
}


# ============================================================
# SCRAPER
# ============================================================

class UniversityScraper:

    def __init__(self):

        pretty_print("UniversityScraper initialised")

    # ========================================================
    # FETCH
    # ========================================================

    def fetch_page(self, url):

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code != 200:
                return None

            return response.text

        except Exception:
            return None

    # ========================================================
    # PDF TEXT EXTRACTION
    # ========================================================

    def extract_pdf_text(self, pdf_url):

        pretty_print(f"PDF extraction: {pdf_url}")

        try:

            response = requests.get(
                pdf_url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )

            pdf_data = response.content

            doc = fitz.open(
                stream=pdf_data,
                filetype="pdf"
            )

            text = ""

            for page in doc:
                text += page.get_text()

            return text.lower()

        except Exception as e:

            pretty_print(
                f"PDF extraction failed: {e}",
                level="ERROR"
            )

            return ""

    # ========================================================
    # TEXT EXTRACTION
    # ========================================================

    def extract_text(self, html):

        try:

            soup = BeautifulSoup(html, "lxml")

            for script in soup([
                "script",
                "style",
                "noscript"
            ]):
                script.extract()

            text = soup.get_text(" ", strip=True)

            return text.lower()

        except Exception:
            return ""

    # ========================================================
    # WORD FREQUENCIES
    # ========================================================

    def extract_top_terms(self, text, top_n=30):

        words = re.findall(
            r"\b[a-zàèéìòù]+\b",
            text.lower()
        )

        filtered = [

            w for w in words

            if (
                len(w) > 4
                and w not in STOPWORDS
            )
        ]

        counter = Counter(filtered)

        return counter.most_common(top_n)

    # ========================================================
    # SDG DETECTION
    # ========================================================

    def detect_sdgs(self, text):

        sdg_hits = {}

        for sdg, terms in SDG_TERMS.items():

            count = 0

            for term in terms:

                count += text.count(term.lower())

            sdg_hits[sdg] = count

        return sdg_hits

    # ========================================================
    # YEARS
    # ========================================================

    def extract_years(self, text):

        years = re.findall(
            r"(20[1-2][0-9])",
            text
        )

        validated = []

        for y in years:

            y = int(y)

            if 2010 <= y <= CURRENT_YEAR:
                validated.append(y)

        return sorted(
            list(set(validated)),
            reverse=True
        )

    # ========================================================
    # PDFS
    # ========================================================

    def find_pdf_links(self, base_url, html):

        pdfs = []

        try:

            soup = BeautifulSoup(html, "lxml")

            links = soup.find_all("a", href=True)

            for link in links:

                href = link["href"]

                if ".pdf" not in href.lower():
                    continue

                full_url = urljoin(
                    base_url,
                    href
                )

                pdfs.append(full_url)

        except Exception:
            pass

        return list(set(pdfs))

    # ========================================================
    # CRAWL
    # ========================================================

    def recursive_crawl(
        self,
        start_urls,
        domain
    ):

        queue = deque()

        for u in start_urls:
            queue.append((u, 0))

        visited = set()

        candidate_pages = []

        total_pages = 0

        while queue:

            current_url, depth = queue.popleft()

            if current_url in visited:
                continue

            if depth > MAX_DEPTH:
                continue

            visited.add(current_url)

            total_pages += 1

            if total_pages > MAX_PAGES:
                break

            pretty_print(
                f"[Depth {depth}] {current_url}"
            )

            if current_url.lower().endswith(".pdf"):

                candidate_pages.append(current_url)
                continue

            html = self.fetch_page(current_url)

            time.sleep(SLEEP_TIME)

            if not html:
                continue

            candidate_pages.append(current_url)

            try:

                soup = BeautifulSoup(html, "lxml")

                links = soup.find_all("a", href=True)

                for link in links:

                    href = link["href"]

                    full_url = urljoin(
                        current_url,
                        href
                    )

                    parsed = urlparse(full_url)

                    if parsed.netloc != domain:
                        continue

                    lowered = full_url.lower()

                    if not any(
                        hint in lowered
                        for hint in ALLOWED_PATH_HINTS
                    ):
                        continue

                    if full_url in visited:
                        continue

                    queue.append(
                        (full_url, depth + 1)
                    )

            except Exception:
                continue

        return list(set(candidate_pages))

    # ========================================================
    # EVIDENCE LEVEL
    # ========================================================

    def determine_evidence_level(
        self,
        page_count,
        pdf_count,
        word_count
    ):

        score = (
            page_count +
            pdf_count * 2 +
            word_count / 10000
        )

        if score >= 25:
            return "extensive"

        elif score >= 15:
            return "strong"

        elif score >= 8:
            return "moderate"

        elif score >= 3:
            return "minimal"

        return "none"

    # ========================================================
    # SCRAPE UNIVERSITY
    # ========================================================

    def scrape_university(
        self,
        university,
        base_url
    ):

        pretty_print("=" * 70)
        pretty_print(f"STARTING: {university}")

        domain = urlparse(base_url).netloc

        manual_roots = MANUAL_ROOTS.get(
            university,
            [base_url]
        )

        pages = self.recursive_crawl(
            manual_roots,
            domain
        )

        combined_text = ""

        all_pdfs = []

        all_years = []

        for page in pages:

            pretty_print(f"Processing: {page}")

            if page.lower().endswith(".pdf"):

                pdf_text = self.extract_pdf_text(page)

                combined_text += " " + pdf_text

                all_pdfs.append(page)

                all_years.extend(
                    self.extract_years(pdf_text)
                )

                continue

            html = self.fetch_page(page)

            if not html:
                continue

            text = self.extract_text(html)

            combined_text += " " + text

            years = self.extract_years(text)

            all_years.extend(years)

            pdfs = self.find_pdf_links(
                page,
                html
            )

            for pdf in pdfs:

                if pdf not in all_pdfs:
                    all_pdfs.append(pdf)

                    pdf_text = self.extract_pdf_text(pdf)

                    combined_text += " " + pdf_text

                    all_years.extend(
                        self.extract_years(pdf_text)
                    )

        combined_text = combined_text.lower()

        top_terms = self.extract_top_terms(
            combined_text
        )

        sdg_hits = self.detect_sdgs(
            combined_text
        )

        all_years = sorted(
            list(set(all_years)),
            reverse=True
        )

        evidence_level = self.determine_evidence_level(
            page_count=len(pages),
            pdf_count=len(all_pdfs),
            word_count=len(combined_text.split())
        )

        result = {

            "university": university,

            "base_url": base_url,

            "manual_roots": manual_roots,

            "pages_scanned": len(pages),

            "pdf_count": len(all_pdfs),

            "pdf_urls": all_pdfs,

            "latest_year": (
                all_years[0]
                if all_years
                else None
            ),

            "all_years": all_years,

            "evidence_level": evidence_level,

            "top_terms": top_terms,

            "sdg_hits": sdg_hits,

            "text_length": len(combined_text),

            "word_count": len(
                combined_text.split()
            ),
        }

        pretty_print(
            f"FINISHED: {university}"
        )

        return result

    # ========================================================
    # RUN ALL
    # ========================================================

    def run_all(self):

        results = []

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            futures = {

                executor.submit(
                    self.scrape_university,
                    uni,
                    UNIVERSITY_URLS[uni]
                ): uni

                for uni in UNIVERSITIES
            }

            for future in as_completed(futures):

                uni = futures[future]

                try:

                    result = future.result()

                    results.append(result)

                    pretty_print(
                        f"Completed: {uni}"
                    )

                except Exception as e:

                    pretty_print(
                        f"FAILED: {uni} -> {e}",
                        level="ERROR"
                    )

        return results


# ============================================================
# FLATTEN RESULTS
# ============================================================

def flatten_results(results):

    rows = []

    for r in results:

        row = {

            "university": r["university"],

            "base_url": r["base_url"],

            "evidence_level": r["evidence_level"],

            "pages_scanned": r["pages_scanned"],

            "pdf_count": r["pdf_count"],

            "latest_year": r["latest_year"],

            "word_count": r["word_count"],

            "text_length": r["text_length"],

            "top_terms": json.dumps(
                r["top_terms"],
                ensure_ascii=False
            ),

            "pdf_urls": " | ".join(
                r["pdf_urls"]
            )
        }

        for sdg, count in r["sdg_hits"].items():

            row[sdg] = count

        rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# MAIN
# ============================================================

def main():

    pretty_print("=" * 70)
    pretty_print("PROGRAM STARTED")
    pretty_print("=" * 70)

    scraper = UniversityScraper()

    results = scraper.run_all()

    # ========================================================
    # SAVE JSON
    # ========================================================

    pretty_print("Saving JSON")

    with open(
        "italian_university_sustainability.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    # ========================================================
    # DATAFRAME
    # ========================================================

    df = flatten_results(results)

    # ========================================================
    # SORT
    # ========================================================

    evidence_order = {
        "extensive": 5,
        "strong": 4,
        "moderate": 3,
        "minimal": 2,
        "none": 1
    }

    df["evidence_rank"] = df[
        "evidence_level"
    ].map(evidence_order)

    df = df.sort_values(
        [
            "evidence_rank",
            "pdf_count",
            "word_count"
        ],
        ascending=False
    )

    # ========================================================
    # SAVE CSV
    # ========================================================

    pretty_print("Saving CSV")

    df.to_csv(
        "italian_university_sustainability.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # ========================================================
    # CONSOLE SUMMARY
    # ========================================================

    print("")
    print("=" * 70)
    print("SUSTAINABILITY EVIDENCE SUMMARY")
    print("=" * 70)

    print(df[[
        "university",
        "evidence_level",
        "pdf_count",
        "latest_year",
        "word_count"
    ]].head(25))

    print("")
    print("=" * 70)
    print("FILES EXPORTED")
    print("=" * 70)

    print("italian_university_sustainability.csv")
    print("italian_university_sustainability.json")

    print("=" * 70)


if __name__ == "__main__":
    main()