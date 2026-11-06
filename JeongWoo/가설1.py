import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

# 가설 1: 전통시장 영업점포 수는 감소하고 빈점포율은 증가할 것이다.
sns.set_theme(font='Malgun Gothic', style='whitegrid', rc={'axes.unicode_minus': False})
folder = Path(__file__).resolve().parent
output = folder / 'graphs'
output.mkdir(exist_ok=True)

raw = pd.read_csv(folder / 'mapped_csv' / '점포현황_점포수_분석.csv', header=None, encoding='utf-8-sig')
seoul = raw[raw[0] == '서울'].iloc[0]
data = pd.DataFrame({
    '연도': [2021, 2022, 2023, 2024],
    '전체점포': pd.to_numeric(seoul[[1, 25, 49, 73]]).to_numpy(),
    '영업점포': pd.to_numeric(seoul[[4, 28, 52, 76]]).to_numpy(),
    '빈점포': pd.to_numeric(seoul[[13, 37, 61, 85]]).to_numpy()
})
# 원자료의 전체점포를 분모로 사용. 기타점포·노점도 포함된 분모임.
data['빈점포율'] = data['빈점포'] / data['전체점포'] * 100
print(data.to_string(index=False))
print('기간 영업점포 증감률(%):', (data['영업점포'].iloc[-1] / data['영업점포'].iloc[0] - 1) * 100)
print('기간 빈점포율 변화(%p):', data['빈점포율'].iloc[-1] - data['빈점포율'].iloc[0])
print('끝점 비교와 매년 일관된 추세는 구분해서 해석하세요.')
data.to_csv(output / '가설1_서울_연도별.csv', index=False, encoding='utf-8-sig')

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.lineplot(data=data, x='연도', y='영업점포', marker='o', ax=axes[0])
axes[0].set(title='서울 전통시장 영업점포 수', ylabel='영업점포 수 (개)')
sns.lineplot(data=data, x='연도', y='빈점포율', marker='o', color='coral', ax=axes[1])
axes[1].set(title='서울 전통시장 빈점포율', ylabel='빈점포율 (%)')
for ax in axes:
    ax.set_xticks(data['연도'])
fig.suptitle('가설 1 | 2021~2024년 영업점포·빈점포율')
plt.tight_layout()
plt.savefig(output / '가설1_영업점포_빈점포율.png', dpi=180)
plt.show()
plt.close(fig)
