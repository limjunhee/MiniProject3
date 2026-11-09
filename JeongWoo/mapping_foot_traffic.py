import pandas as pd
from pathlib import Path

folder = Path(__file__).resolve().parent / 'mapped_csv'

# 점포 CSV에 이미 매핑된 상권코드–자치구 관계를 재사용합니다.
columns = ['상권_코드', '자치구_코드', '자치구_코드_명']
mapping = pd.concat([
    pd.read_csv(folder / f'store_{year}_자치구매핑.csv',
                usecols=columns, dtype=str, encoding='utf-8-sig')
    for year in range(2021, 2026)
], ignore_index=True)
mapping = mapping.dropna(subset=columns).drop_duplicates()
if mapping['상권_코드'].duplicated().any():
    raise ValueError('같은 상권코드에 서로 다른 자치구가 있습니다. 매핑 확인이 필요합니다.')

traffic = pd.read_csv(folder / 'Foot_Traffic.csv',
                      dtype={'상권_코드': str}, encoding='utf-8-sig')
result = traffic.merge(mapping, on='상권_코드', how='left',
                       validate='many_to_one', sort=False)
assert len(result) == len(traffic)
assert result.shape[1] == traffic.shape[1] + 2
result.to_csv(folder / 'Foot_Traffic_자치구매핑.csv', index=False, encoding='utf-8-sig')

print('원본/결과 행 수:', len(traffic), len(result))
print(pd.crosstab(result['상권_구분_코드_명'],
                  result['자치구_코드'].notna().map({True: '매핑됨', False: '미매핑'})))
print('주의: 기존 점포 자료에서 매핑되지 않은 상권은 유동인구에서도 빈칸으로 남습니다.')
