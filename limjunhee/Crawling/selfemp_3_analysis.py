# [B-3단계: 자영업 기사 분석]
#  (1) 연도별로 '폐업'이 언급된 기사 비율 -> 선 그래프
#  (2) '폐업'이 언급된 기사들의 연도별 상위 키워드 (kiwi) -> 가로 막대그래프
#  (3) 주요 키워드가 연도별로 얼마나 등장했는지 흐름 -> 선 그래프
# 입력: ./limjunhee/Crawling_CSV/자영업기사_본문_2021~2025.csv (selfemp_2_body.py 결과)
# 설치: pip install kiwipiepy
import pandas as pd
import matplotlib.pyplot as plt
from kiwipiepy import Kiwi
from collections import Counter

plt.rc('font', family='Malgun Gothic')        # 윈도우 맑은고딕으로 변경
plt.rcParams['axes.unicode_minus'] = False    # 음수 기호 깨짐 방지

df = pd.concat([pd.read_csv(f'./limjunhee/Crawling_CSV/자영업기사_본문_{y}.csv', encoding='utf-8-sig')
                for y in range(2021, 2026)])
df['본문'] = df['본문'].fillna('')
df = df[df['본문'].str.len() > 0]                    # 본문을 못 가져온 기사는 제외
df['글'] = df['제목'] + ' ' + df['본문']              # 제목 + 본문을 합쳐서 분석


# ===== (1) 연도별 '폐업' 언급 기사 비율 =====
df['폐업언급'] = df['글'].str.contains('폐업')
ratio = df.groupby('연도').agg(기사수=('폐업언급', 'size'), 폐업언급기사수=('폐업언급', 'sum'))
ratio['비율(%)'] = (ratio['폐업언급기사수'] / ratio['기사수'] * 100).round(1)
print(ratio)
ratio.to_csv('./limjunhee/Crawling_CSV/연도별_폐업언급비율.csv', encoding='utf-8-sig')

plt.figure(figsize=(8, 5))
plt.plot(ratio.index.astype(str), ratio['비율(%)'], marker='o', color='firebrick')
for x, y, n in zip(ratio.index.astype(str), ratio['비율(%)'], ratio['기사수']):
    plt.text(x, y + 1, f'{y}%\n(기사 {n}건)', ha='center', fontsize=9)
plt.title("중앙일보 자영업·소상공인·외식업 기사 중 '폐업'이 언급된 기사 비율")
plt.xlabel('연도')
plt.ylabel('폐업 언급 기사 비율 (%)')
plt.ylim(0, ratio['비율(%)'].max() + 15)
plt.grid(axis='y', alpha=0.3)
plt.show()


# ===== (2) '폐업' 언급 기사의 연도별 상위 키워드 =====
closing = df[df['폐업언급']]

# kiwi 준비: 한 단어로 묶어야 하는 말은 사전에 추가 (안 하면 '소상공인' -> '소' + '상공인'으로 쪼개짐)
kiwi = Kiwi()
for word in ['소상공인', '자영업자', '최저임금', '노란우산', '소진공', '손실보상', '배달앱', '고금리', '고물가',
             '거리두기', '인건비', '중소벤처기업부', '코로나19']:
    kiwi.add_user_word(word, 'NNP', 5)            # 5: 쪼개진 것보다 한 단어로 묶는 쪽을 우선하는 점수

# 같은 뜻인데 다르게 쓰인 단어는 하나로 합치기
same = {'코로나19': '코로나', '신종 코로나바이러스 감염증': '코로나'}

# 불용어: 세어도 의미 없는 단어
stop = {
    # 기사를 고를 때 쓴 단어 -> 모든 기사에 들어 있어 순위만 차지함
    '폐업', '폐점', '자영업', '자영업자', '소상공인', '외식업', '음식점', '식당', '가게', '점포', '매장', '업종', '업체',
    '사업자', '사업', '사장', '대표', '손님', '장사', '영업',
    # 기사 형식 단어
    '기자', '사진', '이미지', '크게', '보기', '뉴스', '중앙일보', '무단', '전재', '재배포', '연합뉴스', '뉴시스', '뉴스1', '그래픽',
    # 어느 기사에나 나오는 일반 단어 (시간·장소·설명)
    '지난해', '올해', '이번', '최근', '지난달', '처음', '기간', '당시', '이후', '이날', '오전', '오후', '시간',
    '서울', '한국', '지역', '경우', '정도', '관계자', '가운데', '상황', '때문', '운영', '기준', '이상', '문제', '결과',
    '설명', '대상', '이유', '규모', '사람', '생각', '관련', '진행', '예정', '전년', '동기', '대비', '전체', '수준',
    '기록', '발표', '조사', '이용', '사용', '제공', '확인', '필요', '가능', '계획', '다양',
}

def get_nouns(text):
    """글에서 두 글자 이상 명사(NNG: 일반명사, NNP: 고유명사)만 뽑기"""
    nouns = []
    for t in kiwi.tokenize(text):
        if t.tag in ('NNG', 'NNP') and len(t.form) >= 2:
            word = same.get(t.form, t.form)
            if word not in stop:
                nouns.append(word)
    return nouns

# 연도별로 세기
#  - 한 기사 안에서 같은 단어가 여러 번 나와도 1번으로 센다 (set 사용) -> 한 기사가 순위를 독차지하는 것을 막음
#  - 연도마다 기사 수가 달라서, '그 단어가 나온 기사 수 ÷ 그해 기사 수 × 100' (%)로 비교
closing = closing.copy()
closing['명사'] = [set(get_nouns(text)) for text in closing['글']]     # 기사마다 명사 목록 (중복 제거) - (3)에서도 사용

counts = {}
for year, group in closing.groupby('연도'):
    counter = Counter()
    for nouns in group['명사']:
        counter.update(nouns)
    counts[year] = {word: n / len(group) * 100 for word, n in counter.most_common(20)}
    print(year, '폐업 언급 기사', len(group), '건 / 상위 10개:',
          [(w, f'{p:.0f}%') for w, p in list(counts[year].items())[:10]])

rows = []
for year, top in counts.items():
    for rank, (word, pct) in enumerate(top.items(), start=1):
        rows.append({'연도': year, '순위': rank, '키워드': word, '등장 기사 비율(%)': round(pct, 1)})
pd.DataFrame(rows).to_csv('./limjunhee/Crawling_CSV/연도별_폐업키워드빈도.csv', index=False, encoding='utf-8-sig')

years = list(counts.keys())
plt.figure(figsize=(20, 6))
for i, year in enumerate(years, start=1):
    top = list(counts[year].items())[:10][::-1]             # 많은 단어가 위로 오도록 뒤집기
    plt.subplot(1, len(years), i)
    plt.barh([w for w, p in top], [p for w, p in top], color='steelblue')
    n_articles = (closing['연도'] == year).sum()
    plt.title(f'{year}년 (폐업 언급 기사 {n_articles}건)')
    plt.xlabel('등장 기사 비율 (%)')
    plt.xlim(0, 100)
plt.suptitle("중앙일보 자영업 기사 중 '폐업' 언급 기사의 연도별 상위 키워드 (기사 1건당 1번)")
plt.tight_layout()
plt.show()


# ===== (3) 주요 키워드 흐름 =====
# 폐업 언급 기사 중 각 키워드가 나온 기사 비율(%)을 연도별로 계산 (키워드는 이 목록만 고치면 바꿀 수 있음)
key_words = ['방역', '거리두기', '고금리', '인건비', '내수']

flow = pd.DataFrame(index=sorted(closing['연도'].unique()))
for word in key_words:
    flow[word] = [group['명사'].apply(lambda nouns: word in nouns).mean() * 100
                  for year, group in closing.groupby('연도')]
flow = flow.round(1)
print(flow)
flow.to_csv('./limjunhee/Crawling_CSV/연도별_주요키워드흐름.csv', encoding='utf-8-sig')

plt.figure(figsize=(9, 5))
for word in key_words:
    plt.plot(flow.index.astype(str), flow[word], marker='o', label=word)
plt.title("'폐업' 언급 기사 속 주요 키워드 등장 비율 (중앙일보 자영업 기사, 2021~2025)")
plt.xlabel('연도')
plt.ylabel('등장 기사 비율 (%)')
plt.ylim(0, 100)
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.show()
