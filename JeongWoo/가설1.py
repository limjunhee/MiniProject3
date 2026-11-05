import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

print('seaborn 버전:', sns.__version__)

# 윈도우 한글 폰트 및 시본 테마 설정
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(font='Malgun Gothic', rc={'axes.unicode_minus': False}, style='whitegrid')

# 코드 파일과 같은 폴더의 CSV만 사용합니다.
folder = Path(__file__).resolve().parent
output = folder / 'graphs'
output.mkdir(exist_ok=True)

# 1] 가설 1: 서울 전통시장 영업점포 수·빈점포율 추이
# CSV의 헤더는 3줄이므로 header=None으로 읽고 열 번호로 선택합니다.
store = pd.read_csv(folder / '점포현황_점포수_분석.csv', header=None, encoding='utf-8-sig')
seoul = store[store[0] == '서울'].iloc[0]

# 2021년 전체/영업/빈점포 열은 1/4/13, 이후 연도는 24열 간격입니다.
h1 = pd.DataFrame({
    '연도': [2021, 2022, 2023, 2024],
    '전체점포': pd.to_numeric(seoul[[1, 25, 49, 73]]).to_numpy(),
    '영업점포': pd.to_numeric(seoul[[4, 28, 52, 76]]).to_numpy(),
    '빈점포': pd.to_numeric(seoul[[13, 37, 61, 85]]).to_numpy()
})
# 2024년 빈점포율 열이 없어 전 기간 같은 산식 사용. 전체에는 기타점포·노점도 포함.
h1['빈점포율'] = h1['빈점포'] / h1['전체점포'] * 100
print('\n가설 1 데이터\n', h1)
h1.to_csv(output / '가설1_서울_연도별.csv', index=False, encoding='utf-8-sig')

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.lineplot(data=h1, x='연도', y='영업점포', marker='o', ax=axes[0])
axes[0].set(title='서울 전통시장 영업점포 수', ylabel='영업점포 수 (개)')
sns.lineplot(data=h1, x='연도', y='빈점포율', marker='o', color='coral', ax=axes[1])
axes[1].set(title='서울 전통시장 빈점포율', ylabel='빈점포율 (%)')
for ax in axes:
    ax.set_xticks(h1['연도'])
fig.suptitle('가설 1 | 영업점포 수와 빈점포율 추이')
plt.tight_layout()
plt.savefig(output / '가설1_영업점포_빈점포율.png', dpi=180)
plt.show()
plt.close(fig)

# 2] 가설 2 참고: 자치구별 등록·인정시장 점포수 변화
# 영업점포 수인지 확인되지 않은 대리지표이며 상점가는 제외합니다.
market = pd.read_csv(folder / '시장현황.csv', header=None, skiprows=3, encoding='utf-8-sig')
market = market[[1, 2, 7, 10]].copy()
market.columns = ['자치구', '연도', '등록시장점포', '인정시장점포']
market['자치구'] = market['자치구'].ffill()  # 병합 셀 때문에 비어 있는 지역명만 채움
for column in ['연도', '등록시장점포', '인정시장점포']:
    market[column] = pd.to_numeric(market[column], errors='coerce')
# '-'는 의미가 불명확하므로 0으로 바꾸지 않습니다.
market['등록인정점포'] = market['등록시장점포'] + market['인정시장점포']
market = market[market['자치구'] != '소계']

# 프랜차이즈와 공통으로 비교 가능한 기간: 2021~2024년
district = market.pivot(index='자치구', columns='연도', values='등록인정점포')
valid = district[2021].gt(0) & district[2024].notna()
print('\n결측 또는 분모 0으로 제외한 자치구:', district.index[~valid].tolist())
district = district.loc[valid, [2021, 2024]].copy()
district['점포수 증감률'] = (district[2024] / district[2021] - 1) * 100
h2 = district.reset_index().sort_values('점포수 증감률')
h2['방향'] = np.where(h2['점포수 증감률'] < 0, '감소', '증가·유지')
h2.to_csv(output / '가설2_자치구별_대리지표.csv', index=False, encoding='utf-8-sig')

# 3] 가설 2 참고: 서울 상권 프랜차이즈 점포수 추이
# 파일명과 실제 연도가 다름: store_2022~2025에 실제 2021~2024년 수록.
# store_2021.csv는 유동인구 자료이므로 사용하지 않습니다.
columns = ['기준_년분기_코드', '상권_구분_코드', '상권_코드',
           '서비스_업종_코드', '프랜차이즈_점포_수']
franchise = pd.concat([
    pd.read_csv(folder / 'store_2022.csv', usecols=columns, encoding='utf-8-sig'),
    pd.read_csv(folder / 'store_2023.csv', usecols=columns, encoding='utf-8-sig'),
    pd.read_csv(folder / 'store_2024.csv', usecols=columns, encoding='utf-8-sig'),
    pd.read_csv(folder / 'store_2025.csv', usecols=columns, encoding='utf-8-sig')
], ignore_index=True).drop_duplicates()

# 점포수는 재고 지표이므로 분기 합계 대신 매년 4분기를 비교합니다.
franchise['연도'] = franchise['기준_년분기_코드'] // 10
franchise['분기'] = franchise['기준_년분기_코드'] % 10
# 공간 중복 가능성이 있는 관광특구(U) 제외: 골목(A), 발달(D), 전통시장(R)
franchise = franchise[(franchise['분기'] == 4) & franchise['상권_구분_코드'].isin(['A', 'D', 'R'])]
yearly = franchise.groupby('연도')['프랜차이즈_점포_수'].sum(min_count=1).reset_index()
yearly.to_csv(output / '가설2_서울_프랜차이즈_4분기.csv', index=False, encoding='utf-8-sig')
print('\n서울 프랜차이즈 점포수 (4분기)\n', yearly)

fig, axes = plt.subplots(1, 2, figsize=(14, 9))
sns.barplot(data=h2, x='점포수 증감률', y='자치구', hue='방향', dodge=False,
            palette={'감소': 'coral', '증가·유지': 'steelblue'}, ax=axes[0])
axes[0].axvline(0, color='gray', linewidth=1)
axes[0].set(title='등록·인정시장 점포수 변화 (2021~2024)', xlabel='점포수 증감률 (%)', ylabel='')
sns.lineplot(data=yearly, x='연도', y='프랜차이즈_점포_수', marker='o', ax=axes[1])
axes[1].set(title='서울 상권 프랜차이즈 점포수 (매년 4분기)', ylabel='점포수 (개)')
axes[1].set_xticks(yearly['연도'])
fig.suptitle('가설 2 참고 | 자치구별 시장 점포수 변화와 서울 프랜차이즈 추이')
fig.text(.05, .02, '자치구별 영업점포·상권코드–자치구 매핑이 없어 두 변수의 상관관계는 검증하지 않았습니다.', fontsize=10)
plt.tight_layout(rect=[0, .05, 1, .95])
plt.savefig(output / '가설2_참고용_자치구점포변화_프랜차이즈추이.png', dpi=180)
plt.show()
plt.close(fig)

print('\n그래프 저장 위치:', output)
