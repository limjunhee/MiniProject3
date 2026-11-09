import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)


#  보조 분석. 지역별 음식점 폐업률·증감률 

# 시도별 음식점 폐업자 수 : 폐업자 현황(사업자별·업태별) 일반+간이+면세 '음식업' 행
df = pd.read_csv('./Data/폐업자_시도업태.csv', encoding='utf-8-sig', header=None)
rows = []
for i in range(2, df.shape[0]):
    if df.iloc[i, 0] in ['일반사업자', '간이사업자', '면세사업자'] and df.iloc[i, 1] == '음식업':
        for c in range(2, df.shape[1]):
            if df.iloc[1, c] != '합계' and str(df.iloc[i, c]).isdigit():      # '-' 칸 제외
                rows.append({'시도': df.iloc[1, c], '연도': int(df.iloc[0, c]), '폐업': int(df.iloc[i, c])})
closed = pd.DataFrame(rows).groupby(['시도', '연도'])['폐업'].sum().reset_index()

#시도별 12월말 음식점 가동 사업자 수 : 12월 파일의 시도 합계 행
#   - 특별자치도 전환으로 바뀐 시도명을 약칭으로 통일
시도명 = {'서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구', '인천광역시': '인천',
         '광주광역시': '광주', '대전광역시': '대전', '울산광역시': '울산', '세종특별자치시': '세종',
         '경기도': '경기', '강원도': '강원', '강원특별자치도': '강원', '충청북도': '충북', '충청남도': '충남',
         '전라북도': '전북', '전북특별자치도': '전북', '전라남도': '전남', '경상북도': '경북',
         '경상남도': '경남', '제주특별자치도': '제주'}
rows = []
for 연도 in [2022, 2023, 2025]:
    d = pd.read_excel(f'./Data/월별/가동사업자_{연도}_12.xlsx', sheet_name='성별', header=None)
    for c in [0, 1, 2, 3]:
        d[c] = d[c].astype(str).str.strip()
    for i in range(d.shape[0]):
        if d.iloc[i, 0] == '음식업' and d.iloc[i, 3] == '합계' and d.iloc[i, 1] in 시도명 and '합계' in d.iloc[i, 2]:
            시도 = 시도명[d.iloc[i, 1]]
            rows.append({'시도': 시도, '연도': 연도, '가동': int(d.iloc[i, 4])})
            rows.append({'시도': 시도, '연도': 연도 - 1, '가동': int(d.iloc[i, 7])})
st = pd.DataFrame(rows).drop_duplicates(subset=['시도', '연도'])
st = st.sort_values(['시도', '연도']).reset_index(drop=True)
전년 = []
for k in range(len(st)):
    전년.append(st['가동'][k - 1] if k > 0 and st['시도'][k] == st['시도'][k - 1] else None)
st['가동_전년'] = 전년
st['증감률'] = (st['가동'] / st['가동_전년'] - 1) * 100

p = st.merge(closed, on=['시도', '연도'])
p['폐업률'] = p['폐업'] / p['가동'] * 100
print(p)
print(p.groupby('연도')['폐업률'].mean())          # 17개 시도 평균 폐업률


# [그림 10] 시도 × 연도 음식점 폐업률 히트맵

시도목록 = sorted(p['시도'].unique())
표 = pd.DataFrame(index=시도목록)
for 연도 in range(2021, 2026):
    값 = []
    for 시도 in 시도목록:
        값.append(p[(p['시도'] == 시도) & (p['연도'] == 연도)]['폐업률'].iloc[0])
    표[연도] = 값

plt.figure(figsize=(8, 7))
sns.heatmap(표, annot=True, fmt='.1f', cmap='Reds')
plt.yticks(rotation=0)
plt.title('시도별 · 연도별 음식점 폐업률(%)')
plt.xlabel('연도')
plt.ylabel('시도')
plt.tight_layout()
plt.show()

# 2025년 시도별 음식점 가동 사업자 증감률 (전년 12월 대비)
순 = p[p['연도'] == 2025].sort_values('증감률').reset_index(drop=True)
print(순[['시도', '증감률']])

plt.figure(figsize=(11, 5))
색 = ['crimson' if v < 0 else 'seagreen' for v in 순['증감률']]
막대 = plt.bar(순['시도'], 순['증감률'], color=색)
plt.bar_label(막대, fmt='%.1f')
plt.title('2025년 시도별 음식점 가동 사업자 증감률(%)')
plt.ylabel('전년 12월 대비 증감률(%)')
plt.grid(alpha=0.3, axis='y')
plt.tight_layout()
plt.show()