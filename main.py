import os
import feedparser
import requests
from datetime import datetime
import pytz

# 최신 Google GenAI 패키지
from google import genai

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
KST = pytz.timezone('Asia/Seoul')

def main():
    now = datetime.now(KST)
    hour = now.hour

    # KST 07:00 ~ 01:00 사이에만 뉴스 생성 및 전송
    if not (7 <= hour or hour <= 1):
        print(f"시간 외 스킵 ({now.strftime('%H:%M KST')})")
        return

    print(f"브리핑 시작 ({now.strftime('%m/%d %H:%M KST')})")

    rss_urls = [
        "https://news.google.com/rss/search?q=인공지능+OR+AI+OR+LLM+OR+Gemini+OR+Claude+OR+Grok&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=artificial+intelligence+OR+AI+OR+LLM+OR+Gemini+OR+Claude+OR+Grok&hl=en-US&gl=US&ceid=US:en"
    ]

    all_news = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.title
            link = entry.link
            desc = (entry.get('summary') or entry.get('description') or '')[:180]
            pub_date = entry.get('published', '날짜 없음')
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
        # 최신 방식: 모델 생성 시 api_key 전달
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            generation_config={"api_key": os.getenv('GEMINI_API_KEY')}
        )

        response = model.generate_content(prompt)
        summary = response.text.strip()

        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': f"AI 뉴스 브리핑 ({now.strftime('%m/%d %H:%M KST')})\n\n{summary}",
            'parse_mode': 'Markdown'
        }
        r = requests.post(telegram_url, data=payload)
        if r.status_code == 200:
            print("Telegram 전송 성공")
        else:
            print(f"Telegram 전송 실패: {r.status_code} {r.text}")
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
