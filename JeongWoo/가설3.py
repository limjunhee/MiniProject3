import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# 먼저 가설2.py 실행. 2021~2025 전체 분기 수준값과 전년 동분기 증감률 사용.
sns.set_theme(font='Malgun Gothic', style='whitegrid', rc={'axes.unicode_minus': False})
folder = Path(__file__).resolve().parent
output = folder / 'graphs'
output.mkdir(exist_ok=True)
data = pd.read_csv(output / '가설2_자치구별_분석.csv', dtype={'자치구_코드': str}, encoding='utf-8-sig')
traffic = pd.read_csv(folder / 'mapped_csv' / 'Foot_Traffic_자치구매핑.csv',
                      dtype={'자치구_코드': str}, encoding='utf-8-sig')
# 관광특구(U) 포함. 공간 중복을 제거한 고유 방문자 수가 아닙니다.
traffic = traffic[traffic['기준_년분기_코드'].between(20211, 20254) & traffic['상권_구분_코드'].isin(['A', 'D', 'R', 'U'])]
assert not traffic.duplicated(['기준_년분기_코드', '상권_코드']).any()
assert not traffic[['자치구_코드', '총_유동인구_수']].isna().any().any()
keys = ['자치구_코드', '기준_년분기_코드']
population = traffic.groupby(keys)['총_유동인구_수'].sum(min_count=1).rename('유동인구').reset_index()
data = data.merge(population, on=keys, how='left', validate='one_to_one')
# 매 분기 중앙값으로 집단 구분. 상권별 합계는 고유 방문자 수가 아닙니다.
median = data.groupby('기준_년분기_코드')['유동인구'].transform('median')
data['유동인구집단'] = np.where(data['유동인구'] >= median, '높음', '낮음')
data.loc[data['유동인구'].isna(), '유동인구집단'] = pd.NA
data.to_csv(output / '가설3_자치구별_분석.csv', index=False, encoding='utf-8-sig')
analysis = data.dropna(subset=['시장_증감률', '프랜차이즈_증가율', '유동인구']).copy()
print('전체 표 연도별 행 수:', data.groupby('연도').size().to_dict())
print('분석 표 연도별 행 수:', analysis.groupby('연도').size().to_dict())
for label, subset in analysis.groupby('유동인구집단'):
    print(label, '관측 수:', len(subset), '탐색적 상관계수:', subset['시장_증감률'].corr(subset['프랜차이즈_증가율']))

# 같은 자치구의 반복 관측을 고려: 자치구·분기 고정효과 + 자치구 군집 표준오차.
# 시장 증감률/로그 유동인구를 표준화하고 상호작용 계수가 음수인지 확인합니다.
x = analysis['시장_증감률'].to_numpy(dtype=float)
z = np.log1p(analysis['유동인구'].to_numpy(dtype=float))
x = (x - x.mean()) / x.std(ddof=0)
z = (z - z.mean()) / z.std(ddof=0)
y = analysis['프랜차이즈_증가율'].to_numpy(dtype=float)
district = pd.get_dummies(analysis['자치구_코드'], drop_first=True, dtype=float)
quarter = pd.get_dummies(analysis['기준_년분기_코드'].astype(str), drop_first=True, dtype=float)
X = np.column_stack([np.ones(len(analysis)), x, z, x*z, district.to_numpy(), quarter.to_numpy()])
assert np.linalg.matrix_rank(X) == X.shape[1]
beta = np.linalg.lstsq(X, y, rcond=None)[0]
residual = y - X @ beta
inv = np.linalg.inv(X.T @ X)
meat = np.zeros((X.shape[1], X.shape[1]))
clusters = analysis['자치구_코드'].to_numpy()
for code in np.unique(clusters):
    mask = clusters == code
    score = X[mask].T @ residual[mask]
    meat += np.outer(score, score)
G = len(np.unique(clusters))
N, K = X.shape
cov = inv @ meat @ inv * (G/(G-1)) * ((N-1)/(N-K))
se = np.sqrt(np.maximum(np.diag(cov), 0))
pvalue = 2 * stats.t.sf(np.abs(beta / se), df=G-1)
regression = pd.DataFrame({'항목': ['절편', '시장증감률_z', '로그유동인구_z', '상호작용'],
    '계수': beta[:4], '자치구군집표준오차': se[:4], '근사양측p값': pvalue[:4],
    '관측수': N, '자치구수': G, '고정효과': '자치구+분기'})
print(regression.to_string(index=False))
print('상호작용 음수가 가설 예상 방향. 같은 기간의 관련성이며 인과관계가 아닙니다.')
print('군집 25개로 근사 검정이며, 공간 중복·매핑 추정·조사대상 변화도 고려해야 합니다.')
regression.to_csv(output / '가설3_상호작용회귀.csv', index=False, encoding='utf-8-sig')

# 연도별 집단 관계를 분리해 표시. 회귀선은 고정효과 모형과 다른 탐색용 그림.
plot = sns.lmplot(data=analysis, x='시장_증감률', y='프랜차이즈_증가율', hue='유동인구집단',
    col='연도', col_wrap=2, palette={'높음': 'coral', '낮음': 'steelblue'},
    ci=None, height=4, aspect=1.3, scatter_kws={'alpha': .6})
plot.set_axis_labels('', '')
plot.set_titles('{col_name}년')
# 각 패널 대신 그림 전체에 공통 축 제목을 한 번만 표시합니다.
plot.fig.subplots_adjust(left=.12, bottom=.12, top=.86, right=.85, hspace=.22, wspace=.12)
plot.fig.supxlabel('전통시장 내 비프랜차이즈 점포수 전년 동분기 증감률 (%)', y=.035, fontsize=12)
plot.fig.supylabel('전체 상권 프랜차이즈 전년 동분기 증가율 (%)', x=.025, fontsize=12)
plot.fig.suptitle('가설 3 | 연도별 유동인구 집단 관계 (2021~2025년 자료)\n2021년은 전년도 자료가 없어 변화율 분석 제외', y=.98, fontsize=15)
plot.fig.savefig(output / '가설3_유동인구별_관계.png', dpi=180, bbox_inches='tight')
plt.show()
plt.close(plot.fig)
