import requests, xmltodict, html, time, os
import pandas as pd

failed = []                                   # 실패한 날짜 기록
for year in range(2021, 2022):
    path = f'./limjunhee/Crawling_CSV/중앙일보_기사제목_{year}.csv'
    if os.path.exists(path):                  # 이미 저장된 연도는 건너뜀 (이어서 실행)
        print(year, '이미 있음, 건너뜀')
        continue

    rows = []
    for day in pd.date_range(f'{year}-01-01', f'{year}-12-31'):
        url = f"https://www.joongang.co.kr/sitemap/articles/{day.year}/{day:%Y%m%d}"
        try:
            response = requests.get(url, timeout=10)
            data = xmltodict.parse(response.text)
            urls = data['urlset'].get('url', [])
            if isinstance(urls, dict):
                urls = [urls]
            for u in urls:
                news = u['news:news']
                rows.append({
                    '날짜': news['news:publication_date'][:10],
                    '제목': html.unescape(news['news:title']),
                    '키워드': news.get('news:keywords'),
                    '주소': u['loc'],
                })
        except Exception as e:
            print(day.date(), '실패:', e)
            failed.append(str(day.date()))
        time.sleep(1)
        if day.day == 1:
            print(day.strftime('%Y-%m'), '진행 중...', len(rows), '건')

    pd.DataFrame(rows).to_csv(path, index=False, encoding='utf-8-sig')
    print(year, '저장 완료:', len(rows), '건')

print('실패한 날짜:', failed)



# 확인용 ========================================================================

# df = pd.read_csv('./limjunhee/CSV/중앙일보_기사제목_2023.csv')

# print(df['주소'].duplicated().sum())         # 같은 기사가 두 번 들어갔는지 (0이면 중복 없음)
# print(df['날짜'].str[:4].value_counts())      # 날짜가 전부 2023인지