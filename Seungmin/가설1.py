import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression

plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)


#  가설 1. 자영업의 고정비용(금리·임대료·인건비)이 상승하면,
#          음식점 폐업률은 상승하고 개업률은 하락할 것이다.
#    1-1 (금리)
#    1-2 (임대료) 
#    1-3 (인건비) 
#    종합         

def 회귀(d, x, y):
    model = LinearRegression()
    model.fit(d[[x]], d[y])
    r2 = model.score(d[[x]], d[y])
    print(f'{x} → {y} : 기울기 {model.coef_[0]:+.3f}, R² {r2:.3f}, n={len(d)}')
    return model, r2

시도명 = {'서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구', '인천광역시': '인천',
         '광주광역시': '광주', '대전광역시': '대전', '울산광역시': '울산', '세종특별자치시': '세종',
         '경기도': '경기', '강원도': '강원', '강원특별자치도': '강원', '충청북도': '충북', '충청남도': '충남',
         '전라북도': '전북', '전북특별자치도': '전북', '전라남도': '전남', '경상북도': '경북',
         '경상남도': '경남', '제주특별자치도': '제주'}


가동 = {}                 # 전국 : 연월 → 가동 사업자 수
시도가동 = []             # 시도 : 12월말 가동 사업자 수
for 연도 in [2022, 2023, 2025]:
    for 월 in range(1, 13):
        d = pd.read_excel(f'./Data/월별/가동사업자_{연도}_{월:02d}.xlsx', sheet_name='성별', header=None)
        for c in [0, 1, 2, 3]:
            d[c] = d[c].astype(str).str.strip()
        행 = d[d[0] == '음식업'].iloc[0]                  # 음식업 블록의 첫 행 = 전국 합계
        가동[f'{연도}-{월:02d}'] = int(행[4])
        가동[f'{연도 - 1}-{월:02d}'] = int(행[7])
        if 월 == 1:
            가동[f'{연도 - 1}-12'] = int(행[5])
        if 월 == 12:                                       # 12월 파일 → 시도 합계 행 (시군구 칸에 '합계')
            for i in range(d.shape[0]):
                if d.iloc[i, 0] == '음식업' and d.iloc[i, 3] == '합계' and d.iloc[i, 1] in 시도명 and '합계' in d.iloc[i, 2]:
                    시도가동.append({'시도': 시도명[d.iloc[i, 1]], '연도': 연도, '가동': int(d.iloc[i, 4])})
                    시도가동.append({'시도': 시도명[d.iloc[i, 1]], '연도': 연도 - 1, '가동': int(d.iloc[i, 7])})

d = pd.read_excel('./Data/월별/가동사업자_2021_01.xlsx', sheet_name='성별', header=None)
for c in [1, 2, 3, 4]:
    d[c] = d[c].astype(str).str.strip()
행 = d[d[1] == '음식업'].iloc[0]
가동['2021-01'] = int(행[5])
가동['2020-12'] = int(행[6])
for i in range(d.shape[0]):                               # 2021년 1월 파일의 '전월' = 2020년 12월말 (시도별)
    if d.iloc[i, 1] == '음식업' and d.iloc[i, 4] == '합계' and d.iloc[i, 2] in 시도명 and d.iloc[i, 3] == '합계':
        시도가동.append({'시도': 시도명[d.iloc[i, 2]], '연도': 2020, '가동': int(d.iloc[i, 6])})

rows = []
for 연월, 값 in 가동.items():
    rows.append({'연월': 연월, '가동': 값})
stock = pd.DataFrame(rows).sort_values('연월').reset_index(drop=True)
stock['가동_전월'] = [None] + list(stock['가동'][:-1])


# 전국 월별 신규 사업자 수 (음식점업) → 월별 폐업 역산

rows = []
for 연도 in range(2021, 2026):
    for 시트, 시작월, 첫열 in [('(3)', 1, 4), ('(4)', 7, 3)]:
        d = pd.read_excel(f'./Data/신규사업자_{연도}.xlsx', sheet_name=시트, header=None)
        d[0] = d[0].astype(str).str.strip()
        행 = d[d[0] == '음식점업'].iloc[0]
        for k in range(6):
            rows.append({'연월': f'{연도}-{시작월 + k:02d}', '신규': int(행[첫열 + k])})
new = pd.DataFrame(rows)

m = stock.merge(new, on='연월').sort_values('연월').reset_index(drop=True)
m['폐업'] = m['신규'] - (m['가동'] - m['가동_전월'])
m['폐업률'] = m['폐업'] / m['가동'] * 100
m['개업률'] = m['신규'] / m['가동'] * 100
m['연도'] = m['연월'].str[:4]
# [파생] 작년 같은 달 대비 폐업률 변화(%p) : 12월 폐업 신고 몰림 등 계절 차이 제거
m['폐업률변화'] = [None] * 12 + list(m['폐업률'][12:].values - m['폐업률'][:-12].values)


# [C] 금리 : KOSIS 예금은행 대출금리(월별) 중 '중소기업대출' 행
#   - 월이 열로 되어 있음 → 열을 하나씩 돌면서 (연월, 금리) 행으로 바꿈

r = pd.read_csv('./Data/대출금리_월별.csv', encoding='utf-8-sig')
행 = r[r['계정항목별'] == '중소기업대출 (연리%)'].iloc[0]
rows = []
for c in r.columns[1:]:
    if str(행[c]) not in ['-', 'nan']:
        rows.append({'연월': c.replace('.', '-'), '금리': float(행[c])})
rate_m = pd.DataFrame(rows)
m = m.merge(rate_m, on='연월', how='left')

# 시도 패널용 : 연평균 금리를 '다음 해'에 붙임 (금리 효과가 나타나기까지 시차)
rate_m['연도'] = rate_m['연월'].str[:4].astype(int) + 1
rate_y = rate_m.groupby('연도')['금리'].mean().reset_index()
rate_y.columns = ['연도', '금리_전년']


# [D] 시도 × 연도 패널 : 음식점 폐업률 · 개업률 (17개 시도 × 2021~2025)
#   - 폐업 : 폐업자 현황(사업자별·업태별) 일반+간이+면세 '음식업' 행 ('-' 칸 제외)
#   - 개업 : 폐업 + (올해 12월 가동 − 작년 12월 가동)   (시도별 음식점 개업 자료가 없어 역산)

df = pd.read_csv('./Data/폐업자_시도업태.csv', encoding='utf-8-sig', header=None)
rows = []
for i in range(2, df.shape[0]):
    if df.iloc[i, 0] in ['일반사업자', '간이사업자', '면세사업자'] and df.iloc[i, 1] == '음식업':
        for c in range(2, df.shape[1]):
            if df.iloc[1, c] != '합계' and str(df.iloc[i, c]).isdigit():
                rows.append({'시도': df.iloc[1, c], '연도': int(df.iloc[0, c]), '폐업': int(df.iloc[i, c])})
closed = pd.DataFrame(rows).groupby(['시도', '연도'])['폐업'].sum().reset_index()

st = pd.DataFrame(시도가동).drop_duplicates(subset=['시도', '연도'])      # 같은 해가 두 파일에 있으면 하나만
st = st.sort_values(['시도', '연도']).reset_index(drop=True)
전년 = []
for k in range(len(st)):
    전년.append(st['가동'][k - 1] if k > 0 and st['시도'][k] == st['시도'][k - 1] else None)
st['가동_전년'] = 전년

p = st.merge(closed, on=['시도', '연도'])
p['폐업률'] = p['폐업'] / p['가동'] * 100
p['신규'] = p['폐업'] + (p['가동'] - p['가동_전년'])
p['개업률'] = p['신규'] / p['가동'] * 100


# 임대지수 : R-ONE 소규모 상가 임대가격지수 3개 파일 → 하나로 연결
#   - 파일마다 100인 분기가 다름 (2020Q4 / 2021Q4 / 2024Q2)
#   - 분기별 변화율을 차례로 곱해 연결 : 지수[i] = 지수[i-1] × (원값[i] ÷ 원값[i-1])

def 지수연결(행목록):
    분기 = list(행목록[0].index)
    지수 = list(행목록[0].values)
    for f in 행목록[1:]:
        for k in range(1, len(f)):
            분기.append(f.index[k])
            지수.append(지수[-1] * f.values[k] / f.values[k - 1])
    return 분기, 지수

파일 = []
for path in ['./Data/임대지수_2021.csv', './Data/임대지수_2022.csv', './Data/임대지수_2024.csv']:
    파일.append(pd.read_csv(path, encoding='cp949', skiprows=[1]))

시도목록 = 파일[0][(파일[0]['지역'] == 파일[0]['지역.1']) & (파일[0]['지역'] == 파일[0]['지역.2']) & (파일[0]['지역'] != '전국')]['지역']
rows = []
for 시도 in 시도목록:
    행목록 = [t[(t['지역'] == 시도) & (t['지역.1'] == 시도) & (t['지역.2'] == 시도)].iloc[0, 4:] for t in 파일]
    분기, 지수 = 지수연결(행목록)
    for q, v in zip(분기, 지수):
        rows.append({'시도': 시도, '연도': int(q[:4]), '임대지수': v})
rent = pd.DataFrame(rows).groupby(['시도', '연도'])['임대지수'].mean().reset_index()
rent = rent.sort_values(['시도', '연도']).reset_index(drop=True)
전년 = []
for k in range(len(rent)):
    전년.append(rent['임대지수'][k - 1] if k > 0 and rent['시도'][k] == rent['시도'][k - 1] else None)
rent['임대지수_전년'] = 전년
rent['임대료변화율'] = (rent['임대지수'] / rent['임대지수_전년'] - 1) * 100


#  시도별 임금 : KOSIS 「행정구역(시도)/산업/규모별 임금」 연간
#   - 도소매·음식숙박업 상용 월급여액 (시도별 음식점 단독 임금이 없어 대신 사용)

wd = pd.read_csv('./Data/임금_시도_연간.csv', encoding='utf-8-sig', header=None)
rows = []
for i in range(2, wd.shape[0]):
    for c in range(3, wd.shape[1]):
        if wd.iloc[1, c] == '상용월급여액 (원)':
            rows.append({'시도': wd.iloc[i, 0], '연도': int(wd.iloc[0, c]), '임금': int(wd.iloc[i, c])})
wage = pd.DataFrame(rows).sort_values(['시도', '연도']).reset_index(drop=True)
전년 = []
for k in range(len(wage)):
    전년.append(wage['임금'][k - 1] if k > 0 and wage['시도'][k] == wage['시도'][k - 1] else None)
wage['임금_전년'] = 전년
wage['임금상승률'] = (wage['임금'] / wage['임금_전년'] - 1) * 100


# [병합] 시도 × 연도 패널 (2021~2025, 17개 시도 = 85건)
P = p.merge(rent[['시도', '연도', '임대료변화율']], on=['시도', '연도'])
P = P.merge(wage[['시도', '연도', '임금상승률']], on=['시도', '연도'])
P = P.merge(rate_y, on='연도')
P = P[(P['연도'] >= 2021) & (P['연도'] <= 2025)].dropna().reset_index(drop=True)
print(P)
print('시도 패널 :', len(P), '건')



#  가설 1-1 : 연도별 개업률·폐업률(위) + 금리(아래)

y연 = m.groupby('연도').agg(폐업=('폐업', 'sum'), 신규=('신규', 'sum'), 가동=('가동', 'mean'), 금리=('금리', 'mean')).reset_index()
y연['폐업률'] = y연['폐업'] / y연['가동'] * 100
y연['개업률'] = y연['신규'] / y연['가동'] * 100
print(y연)
회귀(P, '금리_전년', '폐업률')
회귀(P, '금리_전년', '개업률')

fig, ax = plt.subplots(figsize=(10, 5.5))
x = range(len(y연))
막대1 = ax.bar([i - 0.2 for i in x], y연['개업률'], width=0.4, color='royalblue', label='개업률(%)')
막대2 = ax.bar([i + 0.2 for i in x], y연['폐업률'], width=0.4, color='crimson', label='폐업률(%)')
ax.bar_label(막대1, fmt='%.1f')
ax.bar_label(막대2, fmt='%.1f')
ax.set_xticks(x)
ax.set_xticklabels(y연['연도'])
ax.set_ylim(10, 23)
ax.set_ylabel('연간 개업률·폐업률 (%)')
ax2 = ax.twinx()                                  # 오른쪽 y축을 하나 더 만들어 금리 선을 같은 그림에
ax2.plot(x, y연['금리'], marker='o', color='navy', linewidth=2, label='중소기업대출 금리(연평균, %)')
ax2.set_ylim(2, 6)
ax2.set_ylabel('금리(%)')
ax.legend(loc='upper left')
ax2.legend(loc='upper right')
ax.set_title('금리가 오른 2023년부터 음식점 폐업률이 개업률을 따라잡음')
plt.tight_layout()
plt.show()



# 가설 1-2 : 전국 임대지수 추이(위) vs 음식점 분기 폐업률(아래)
행목록 = [t[t['지역.2'] == '전국'].iloc[0, 4:] for t in 파일]
분기, 지수 = 지수연결(행목록)
q = pd.DataFrame({'분기': 분기, '임대지수': 지수})
q['연'] = q['분기'].str[:4]
q['q'] = q['분기'].str[6]                                 # '2021년 1분기' → '1'
q = q[q['연'] <= '2025']

mq = m.copy()
mq['연'] = mq['연도']
mq['q'] = ((mq['연월'].str[5:7].astype(int) + 2) // 3).astype(str)
mq = mq.groupby(['연', 'q']).agg(폐업=('폐업', 'sum'), 가동=('가동', 'mean')).reset_index()
mq['폐업률'] = mq['폐업'] / mq['가동'] * 100
q = q.merge(mq, on=['연', 'q'], how='left')
print(q)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(q['분기'], q['임대지수'], marker='o', color='darkorange', label='소규모 상가 임대가격지수(전국, 2020년 4분기 = 100)')
ax.set_ylabel('임대지수')
ax.set_xticks(range(len(q)))
ax.set_xticklabels(q['분기'], rotation=45)
ax2 = ax.twinx()                                  # 오른쪽 y축 : 음식점 분기 폐업률 막대
ax2.bar(q['분기'], q['폐업률'], color='crimson', alpha=0.3, label='음식점 분기 폐업률(%)')
ax2.set_ylabel('폐업률(%)')
ax.legend(loc='upper left')
ax2.legend(loc='upper right')
ax.set_title('임대지수는 5년간 꾸준히 하락(100 → 96.6) — 같은 기간 음식점 폐업률은 2023년에 오히려 상승')
ax.grid(alpha=0.3)
plt.tight_layout()
plt.show()



# 가설 1-2 : 시도 패널 산점도 (색 = 연도 / 색 = 시도)

P['연도표시'] = P['연도'].astype(str)
for 색기준, 팔레트, 번호 in [('연도표시', 'viridis', 6), ('시도', 'tab20', 7)]:
    fig, ax = plt.subplots(1, 2, figsize=(15, 5.5))
    for a, y in zip(ax, ['폐업률', '개업률']):
        model, r2 = 회귀(P, '임대료변화율', y)
        sns.scatterplot(data=P, x='임대료변화율', y=y, hue=색기준, palette=팔레트, s=50, ax=a, legend=(y == '개업률'))
        x선 = pd.DataFrame({'임대료변화율': [P['임대료변화율'].min(), P['임대료변화율'].max()]})
        a.plot(x선['임대료변화율'], model.predict(x선), color='red')
        a.set_title(f'임대료 변화율 → 음식점 {y}  기울기 {model.coef_[0]:+.2f}, R² {r2:.2f} (n={len(P)})')
        a.set_xlabel('임대료 변화율(전년 대비, %)')
        a.set_ylabel(f'음식점 {y}(%)')
        a.grid(alpha=0.3)
    ax[1].legend(fontsize=8, loc='center left', bbox_to_anchor=(1.01, 0.5))
    fig.suptitle(f'[그림 {번호}] 가설 1-2. 임대료 변화율 → 음식점 폐업률·개업률 (시도 × 연도 2021~2025)')
    plt.tight_layout()
    plt.show()



# [그림 8] 가설 1-3 : 숙박·음식점 1~4인 임금 상승률 vs 음식점 폐업률 변화 (전국 월별)

w = pd.read_csv('./Data/임금_숙박음식_월별.csv', encoding='cp949', na_values=['-', '...'])
w['규모별'] = w['규모별'].str.strip()
행 = w[(w['산업분류'] == 'I.숙박 및 음식점업(55~56)') & (w['규모별'] == '1~4인') & (w['항목'] == '전체임금총액[원]')].iloc[0]
rows = []
for c in w.columns:
    if c[-1] == '월':                              # '2020.01 월' 같은 월 열만 (분기·연간 열 제외)
        rows.append({'연월': c[:7].replace('.', '-'), '임금': 행[c]})
wm = pd.DataFrame(rows).dropna().reset_index(drop=True)
wm['임금상승률'] = [None] * 12 + list((wm['임금'][12:].values / wm['임금'][:-12].values - 1) * 100)
mw = m.merge(wm, on='연월', how='left')
mw['월'] = mw['연월'].str[2:4] + '.' + mw['연월'].str[5:7]
d = mw.dropna(subset=['임금상승률', '폐업률변화']).reset_index(drop=True)
model, r2 = 회귀(d, '임금상승률', '폐업률변화')

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
ax[0].plot(mw['월'], mw['임금상승률'], color='seagreen', marker='.', label='임금 상승률(작년 같은 달 대비, %)')
ax[0].plot(mw['월'], mw['폐업률변화'] * 10, color='crimson', marker='.', label='폐업률 변화(작년 같은 달 대비, %p × 10)')
ax[0].set_xticks(range(0, len(mw), 6))
ax[0].set_xticklabels(mw['월'][::6])
ax[0].legend(fontsize=8)
ax[0].grid(alpha=0.3)
ax[0].set_title('숙박·음식점 1~4인 임금 상승률과 음식점 폐업률 변화 (월별)')

sns.scatterplot(data=d, x='임금상승률', y='폐업률변화', hue='연도', ax=ax[1], s=45)
x선 = pd.DataFrame({'임금상승률': [d['임금상승률'].min(), d['임금상승률'].max()]})
ax[1].plot(x선['임금상승률'], model.predict(x선), color='red')
ax[1].grid(alpha=0.3)
ax[1].set_title(f'임금 상승률 → 폐업률 변화  기울기 {model.coef_[0]:+.3f}, R² {r2:.2f}, n={len(d)}')
plt.tight_layout()
plt.show()

회귀(P, '임금상승률', '폐업률')              # 시도 패널 (보고서 요약 숫자)
회귀(P, '임금상승률', '개업률')



# 가설 1 종합 : 비용 3요소 × 폐업률·개업률 표준화 기울기 막대
#   - x, y 를 모두 표준화(평균 0, 표준편차 1) → 기울기 = 상관계수 r
#   - 단위가 다른 금리·임대료·임금을 같은 눈금에서 비교

def 표준화(s):
    return (s - s.mean()) / s.std()

결과 = []
for 열 in ['금리_전년', '임대료변화율', '임금상승률']:
    for y in ['폐업률', '개업률']:
        X = pd.DataFrame({열: 표준화(P[열])})
        Y = 표준화(P[y])
        model = LinearRegression()
        model.fit(X, Y)
        결과.append({'비용': 열, '종속변수': y, '기울기': model.coef_[0], 'R²': model.score(X, Y)})
결과 = pd.DataFrame(결과)
print(결과)

폐 = 결과[결과['종속변수'] == '폐업률'].reset_index(drop=True)
개 = 결과[결과['종속변수'] == '개업률'].reset_index(drop=True)
x = range(3)
plt.figure(figsize=(10, 5.5))
막대1 = plt.bar([i - 0.2 for i in x], 폐['기울기'], width=0.4, color='crimson', label='폐업률')
막대2 = plt.bar([i + 0.2 for i in x], 개['기울기'], width=0.4, color='royalblue', label='개업률')
plt.bar_label(막대1, labels=[f'R² {v:.2f}' for v in 폐['R²']], padding=3)
plt.bar_label(막대2, labels=[f'R² {v:.2f}' for v in 개['R²']], padding=3)
plt.xticks(x, ['금리\n(전년 평균)', '임대료\n(전년 대비 변화율)', '인건비\n(전년 대비 상승률)'])
plt.ylabel('표준화 기울기 (상관계수 r)')
plt.legend()
plt.grid(alpha=0.3, axis='y')
plt.title(f'금리만 음식점 폐업률·개업률과 가설 방향으로 연결, 임대료·인건비는 관계 거의 없음\n(시도 17개 × 2021~2025년, n={len(P)})')
plt.tight_layout()
plt.show()