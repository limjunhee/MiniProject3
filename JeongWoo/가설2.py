import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

# 가설 2: 전통시장 점포 감소율과 전체 상권 프랜차이즈 증가율 비교.
# 전통시장은 점포_수(비프랜차이즈), 프랜차이즈는 전체 상권에서 집계합니다.
# 관광특구는 다른 상권과 공간이 겹칠 수 있어 중복 제거된 고유 점포 합계는 아닙니다.
sns.set_theme(font='Malgun Gothic', style='whitegrid', rc={'axes.unicode_minus': False})
folder = Path(__file__).resolve().parent
output = folder / 'graphs'
output.mkdir(exist_ok=True)
columns = ['기준_년분기_코드', '상권_코드', '상권_구분_코드', '서비스_업종_코드',
           '점포_수', '프랜차이즈_점포_수', '자치구_코드', '자치구_코드_명']
store = pd.concat([
    pd.read_csv(folder / 'mapped_csv' / f'store_{year}_자치구매핑.csv',
                usecols=columns, dtype={'자치구_코드': str}, encoding='utf-8-sig')
    for year in range(2021, 2026)
], ignore_index=True)
key = ['기준_년분기_코드', '상권_코드', '서비스_업종_코드']
assert not store.duplicated(key).any(), '같은 분기·상권·업종 중복 확인 필요'
assert not store[['자치구_코드', '자치구_코드_명']].isna().any().any()
assert not store[['점포_수', '프랜차이즈_점포_수']].isna().any().any()

store = store[store['기준_년분기_코드'].between(20211, 20254)]
group = ['자치구_코드', '자치구_코드_명', '기준_년분기_코드']
# 시장_점포수 관련 파생 열은 모두 전통시장 내 비프랜차이즈 점포 기준입니다.
market = store[store['상권_구분_코드'] == 'R'].groupby(group)['점포_수'].sum(min_count=1).rename('시장_점포수')
franchise = store.groupby(group)['프랜차이즈_점포_수'].sum(min_count=1).rename('프랜차이즈_점포수')
data = pd.concat([market, franchise], axis=1).reset_index()
data['연도'] = data['기준_년분기_코드'] // 10
data['분기'] = data['기준_년분기_코드'] % 10
# 코드에 10을 더해 전년도 같은 분기를 정확히 연결합니다. 누락 분기를 건너뛰지 않습니다.
previous = data[['자치구_코드', '기준_년분기_코드', '시장_점포수', '프랜차이즈_점포수']].copy()
previous['기준_년분기_코드'] += 10
previous = previous.rename(columns={'시장_점포수': '전년_시장점포수', '프랜차이즈_점포수': '전년_프랜차이즈점포수'})
data = data.merge(previous, on=['자치구_코드', '기준_년분기_코드'], how='left', validate='one_to_one')
data['시장_증감률'] = (data['시장_점포수'] / data['전년_시장점포수'].where(data['전년_시장점포수'] > 0) - 1) * 100
data['시장_감소율'] = -data['시장_증감률']
data['프랜차이즈_증가율'] = (data['프랜차이즈_점포수'] / data['전년_프랜차이즈점포수'].where(data['전년_프랜차이즈점포수'] > 0) - 1) * 100
data = data.sort_values(['자치구_코드', '기준_년분기_코드'])
print('연도별 수록 행 수:', data.groupby('연도').size().to_dict())
print('2021년은 2020년 자료가 없어 전년 대비 증감률을 계산하지 않습니다.')
print('피어슨 r:', data['시장_감소율'].corr(data['프랜차이즈_증가율']))
print('스피어만 rho:', data['시장_감소율'].corr(data['프랜차이즈_증가율'], method='spearman'))
print('양(+)의 관계가 가설 예상 방향. 인과관계나 개별 시장 주변의 경쟁 효과를 뜻하지 않습니다.')
print('점포 합계는 수록 업종 범위이며, 조사대상·상권경계 변화의 영향도 포함될 수 있습니다.')
data.to_csv(output / '가설2_자치구별_분석.csv', index=False, encoding='utf-8-sig')

analysis = data.dropna(subset=['시장_감소율', '프랜차이즈_증가율'])
# 연도별로 분리하고 모든 패널의 축 범위를 동일하게 유지합니다.
# 점 하나는 자치구·분기 한 관측입니다. 관측값을 빼거나 이동하지 않습니다.
fig, axes = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=True)
colors = ['#26779B', '#D77839', '#439477', '#8B68A5']
xmin, xmax = analysis['시장_감소율'].min(), analysis['시장_감소율'].max()
ymin, ymax = analysis['프랜차이즈_증가율'].min(), analysis['프랜차이즈_증가율'].max()
xpad, ypad = max((xmax-xmin)*.1, 1), max((ymax-ymin)*.1, 1)
for ax, year, color in zip(axes.flat, sorted(analysis['연도'].unique()), colors):
    subset = analysis[analysis['연도'] == year]
    sns.scatterplot(data=subset, x='시장_감소율', y='프랜차이즈_증가율',
                    color=color, alpha=.55, s=48, edgecolor='white', linewidth=.4, ax=ax)
    sns.regplot(data=subset, x='시장_감소율', y='프랜차이즈_증가율',
                scatter=False, ci=None, color=color, line_kws={'linewidth': 2}, ax=ax)
    ax.axhline(0, color='#555555', linewidth=1, linestyle='--')
    ax.axvline(0, color='#555555', linewidth=1, linestyle='--')
    r = subset['시장_감소율'].corr(subset['프랜차이즈_증가율'])
    ax.set(title=f'{year}년 | 관측 {len(subset)}개 · r = {r:.2f}',
           xlabel='', ylabel='', xlim=(xmin-xpad, xmax+xpad), ylim=(ymin-ypad, ymax+ypad))
    ax.grid(alpha=.25)
    sns.despine(ax=ax)
fig.suptitle('가설 2 | 전통시장 비프랜차이즈 감소와 전체 프랜차이즈 변화', fontsize=18, y=.98)
fig.supxlabel('전통시장 내 비프랜차이즈 점포수 감소율 (%)   ← 증가  |  감소 →', y=.07, fontsize=12)
fig.supylabel('전체 상권 프랜차이즈 증가율 (%)', x=.015, fontsize=12)
fig.text(.5, .025, '점 = 자치구·분기 · 전년 같은 분기 대비 · 직선 = 연도별 탐색 회귀선\n2021년은 전년도 자료가 없어 증감률 표시 제외 · 축 범위 동일 · 모든 유효 관측 포함',
         ha='center', fontsize=10, color='#555555')
print('전체 상권 프랜차이즈 집계: 전통시장 내부 프랜차이즈 포함, 관광특구의 공간 중복 가능성 있음.')
plt.tight_layout(rect=[.035, .1, 1, .95])
plt.savefig(output / '가설2_감소율_프랜차이즈_산점도.png', dpi=180)
plt.show()
plt.close(fig)

# 전체 분기 원수준 추이: 재고인 점포수는 분기끼리 합산하지 않습니다.
trend = data.groupby('기준_년분기_코드')[['시장_점포수', '프랜차이즈_점포수']].sum(min_count=1)
trend.index = [f'{q // 10}Q{q % 10}' for q in trend.index]
fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
for ax, column in zip(axes, trend.columns):
    sns.lineplot(x=trend.index, y=trend[column], marker='o', ax=ax)
    label = '전통시장 내 비프랜차이즈 점포수' if column == '시장_점포수' else '전체 상권 프랜차이즈 점포수'
    ax.set(ylabel=f'{label} (개)', xlabel='분기')
axes[1].tick_params(axis='x', rotation=45)
fig.suptitle('서울 전체 점포수 추이 | 2021~2025년 20개 분기')
plt.tight_layout()
plt.savefig(output / '가설2_전체분기_점포수추이.png', dpi=180)
plt.show()
plt.close(fig)
