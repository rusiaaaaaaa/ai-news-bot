import os
import feedparser
import requests
from datetime import datetime
import pytz
from google import genai

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
KST = pytz.timezone('Asia/Seoul')
LAST_SENT_FILE = 'last_sent.txt'  # 마지막 전송 시간을 저장할 파일

def main():
    now = datetime.now(KST)
    hour = now.hour

    # 기존 시간대 체크 (오전 2~6시는 스킵)
    if not (7 <= hour or hour <= 1):
        print(f"시간 외 스킵 ({now.strftime('%H:%M KST')})")
        return

    print(f"브리핑 시작 ({now.strftime('%m/%d %H:%M KST')})")

    # 3시간 주기 체크
    if os.path.exists(LAST_SENT_FILE):
        with open(LAST_SENT_FILE, 'r') as f:
            last_str = f.read().strip()
            last_time = datetime.fromisoformat(last_str)
        
        elapsed = (now - last_time).total_seconds()
        if elapsed < 3 * 3600:  # 3시간 미만이면 스킵
            print(f"3시간 미만 경과, 스킵 ({now.strftime('%H:%M KST')})")
            return

    # 뉴스 수집 및 요약 (기존 로직 그대로)
    rss_urls = [
        "https://news.google.com/rss/search?q=인공지능+OR+AI+OR+LLM+OR+Gemini+OR+Claude+OR+Grok&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=artificial+intelligence+OR+AI+OR+LLM+OR+Gemini+OR+Claude+OR+Grok&hl=en-US&gl=US&ceid=US:en"
    ]
    all_news = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.title
            pub_date = entry.get('published', '날짜 없음')
            desc = (entry.get('summary') or entry.get('description') or '')[:180]
            all_news.append(f"{title}\n{pub_date}\n{desc}...")

    news_text = "\n\n".join(all_news[:8])

    prompt = f"""지금은 한국시간 {now.strftime('%m월 %d일 %H:%M')}입니다.
아래 최신 AI 관련 뉴스를 다음 형식으로 요약해주세요.
- 가장 중요한 4~6개 뉴스만 선별
- 각 뉴스를 자세히 설명
- 링크는 포함하지 말 것
- 불필요한 이모지나 장식은 사용하지 말 것
- 각 뉴스의 일자, 시간 표시 (원문에 있는 published 날짜/시간 사용)
뉴스 원문:
{news_text}"""

    try:
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        summary = response.text.strip()

        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': f"AI 뉴스 브리핑 ({now.strftime('%m/%d %H:%M KST')})\n\n{summary}",
            'parse_mode': 'Markdown'
        }
        r = requests.post(telegram_url, data=payload)
        print(f"Telegram 응답: {r.status_code} - {r.text[:150]}")

        # 전송 성공 시 마지막 전송 시간 업데이트
        with open(LAST_SENT_FILE, 'w') as f:
            f.write(now.isoformat())

    except Exception as e:
        print(f"오류: {str(e)}")

if __name__ == "__main__":
    main()
