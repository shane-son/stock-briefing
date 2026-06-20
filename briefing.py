import os
import smtplib
import ssl
import sys
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from openai import OpenAI

KST = ZoneInfo("Asia/Seoul")

NEWS_QUERIES = [
    "global stock market today OR Wall Street OR Nasdaq OR S&P 500",
    "KOSPI KOSDAQ Korean stock market today",
    "AI stocks Nvidia Microsoft OpenAI data center market",
    "semiconductor stocks Nvidia AMD TSMC Samsung SK Hynix ASML",
    "quantum computing stocks IonQ Rigetti D-Wave",
    "space stocks Rocket Lab AST SpaceMobile SpaceX",
    "emerging stock market theme investors",
]


def env_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def fetch_google_news(query: str, limit: int = 5) -> list[dict]:
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        data = response.read()

    root = ET.fromstring(data)
    items = []
    for item in root.findall("./channel/item")[:limit]:
        source_node = item.find("source")
        items.append(
            {
                "query": query,
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "published": (item.findtext("pubDate") or "").strip(),
                "source": (source_node.text if source_node is not None else "").strip(),
            }
        )
    return items


def collect_news() -> list[dict]:
    seen = set()
    articles = []
    for query in NEWS_QUERIES:
        try:
            for article in fetch_google_news(query):
                key = article["title"] or article["link"]
                if key and key not in seen:
                    seen.add(key)
                    articles.append(article)
        except Exception as exc:
            print(f"Warning: failed to fetch query '{query}': {exc}", file=sys.stderr)
    return articles[:40]


def article_block(articles: list[dict]) -> str:
    if not articles:
        return "뉴스 RSS 수집 결과가 없습니다."
    lines = []
    for idx, article in enumerate(articles, 1):
        lines.append(
            f"{idx}. [{article['source']}] {article['title']}\n"
            f"   Published: {article['published']}\n"
            f"   Link: {article['link']}\n"
            f"   Query: {article['query']}"
        )
    return "\n".join(lines)


def build_briefing(articles: list[dict]) -> str:
    today = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=env_required("OPENAI_API_KEY"))

    prompt = f"""
    현재 시각: {today}

    아래 수집 뉴스 목록을 바탕으로 국내 및 해외 주식 관련 주요 뉴스를 한국어로 간결하게 요약해줘.

    요구 형식:
    # 평일 주식 뉴스 브리핑 - YYYY-MM-DD

    ## 전체 증시 상황
    - 핵심 이슈:
    - 관련 기업/지수/섹터:
    - 투자자가 볼 만한 의미:

    ## AI
    ## 반도체
    ## 양자컴퓨터
    ## 우주
    ## 새롭게 주목할 산업/테마
    ## 확인 출처

    지침:
    - 각 항목은 핵심 이슈, 관련 기업/지수/섹터, 투자자가 볼 만한 의미 중심으로 정리해.
    - 최신 정보는 아래 출처 목록 안에서만 사실로 다뤄.
    - 중요한 뉴스가 적으면 과장하지 말고 '특이사항 적음'이라고 적어.
    - 확인 출처에는 기사 제목과 매체명을 짧게 적고 링크도 포함해.
    - 투자 조언처럼 단정하지 말고 관찰 포인트로 표현해.

    수집 뉴스:
    {article_block(articles)}
    """

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": "You are a careful Korean financial news briefing writer. Be concise, factual, and avoid hype.",
            },
            {"role": "user", "content": textwrap.dedent(prompt)},
        ],
    )
    return response.output_text.strip()


def send_email(subject: str, body: str) -> None:
    smtp_user = env_required("SMTP_USER")
    smtp_password = env_required("SMTP_APP_PASSWORD")
    mail_to = env_required("MAIL_TO")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = mail_to
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)


def main() -> None:
    now = datetime.now(KST)
    articles = collect_news()
    briefing = build_briefing(articles)
    subject = f"평일 주식 뉴스 브리핑 - {now:%Y-%m-%d}"
    send_email(subject, briefing)
    print("Email sent")


if __name__ == "__main__":
    main()
