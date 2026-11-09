import pandas as pd
from pathlib import Path

# 이 코드를 MiniProject3/JeongWoo 폴더에서 실행합니다.
folder = Path(__file__).resolve().parent.parent
output = Path(__file__).resolve().parent / 'mapped_csv'
output.mkdir(exist_ok=True)

# 제공된 매핑 파일은 CP949 인코딩이며 상권코드 열 이름이 다릅니다.
mapping = pd.read_csv(folder / '자치구_상권코드.csv', encoding='cp949', dtype=str)
mapping = mapping[['상권배후지_구분_코드', '자치구_코드', '자치구_코드_명']]
mapping = mapping.rename(columns={'상권배후지_구분_코드': '상권_코드'}).drop_duplicates()
if mapping['상권_코드'].isna().any() or mapping['상권_코드'].duplicated().any():
    raise ValueError('매핑표의 상권코드 누락 또는 중복을 확인하세요.')

for year in range(2021, 2026):
    store = pd.read_csv(folder / f'store_{year}.csv', encoding='utf-8-sig',
                        dtype={'상권_코드': str})
    result = store.merge(mapping, on='상권_코드', how='left',
                         validate='many_to_one', sort=False)
    assert len(result) == len(store), '병합 후 행 수가 달라졌습니다.'
    assert result.shape[1] == store.shape[1] + 2, '추가 열 수를 확인하세요.'
    # 제공된 매핑표에 없는 상권은 자치구를 추측하지 않고 빈칸으로 보존합니다.
    result.to_csv(output / f'store_{year}_자치구매핑.csv', index=False, encoding='utf-8-sig')
    print(f'\n{year}: 원본 {len(store):,}행 → 결과 {len(result):,}행')
    print('자치구 매핑 여부별 상권 유형 (행 수)')
    print(pd.crosstab(result['상권_구분_코드_명'],
                      result['자치구_코드'].notna().map({True: '매핑됨', False: '미매핑'})))
    print('미매핑 상권 수:', result.loc[result['자치구_코드'].isna(), '상권_코드'].nunique())

print('\n저장 위치:', output)
