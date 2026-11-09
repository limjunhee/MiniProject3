import pandas as pd
import matplotlib.pyplot as plt

plt.rc( 'font' , family = 'Malgun Gothic' )
plt.rcParams['axes.unicode_minus'] = False

s21 = pd.read_csv( "data/store_2021.csv" )
s22 = pd.read_csv( "data/store_2022.csv" )
s23 = pd.read_csv( "data/store_2023.csv" )
s24 = pd.read_csv( "data/store_2024.csv" )
s25 = pd.read_csv( "data/store_2025.csv" )

store = pd.concat( [ s21 , s22 , s23 , s24 , s25 ] , axis = 0 , ignore_index = True )

print( store.shape )
print( store.isnull().sum().sum() )
print( store.shape , store.drop_duplicates().shape )
print( ( store["점포_수"] == 0 ).sum() )

store["연도"] = ( store["기준_년분기_코드"] / 10 ).astype(int)

store["묶음"] = "중심"
store.loc[ store["상권_구분_코드_명"] == "골목상권" , "묶음" ] = "동네"
store.loc[ store["상권_구분_코드_명"] == "전통시장" , "묶음" ] = "동네"

g = store.groupby( [ "연도" , "상권_코드" , "상권_구분_코드_명" , "묶음" ] ).agg(
    폐업합계 = ( "폐업_점포_수" , "sum" ),
    개업합계 = ( "개업_점포_수" , "sum" ),
    유사업종합계 = ( "유사_업종_점포_수" , "sum" )
).reset_index()
g["폐업률"] = g["폐업합계"] / g["유사업종합계"] * 100
g["개업률"] = g["개업합계"] / g["유사업종합계"] * 100
print( "제외 전" , g.shape )

g = g[ g["유사업종합계"] >= 30 ]
print( "제외 후" , g.shape )

# 현황 : 동네 vs 중심
r = g.groupby( [ "연도" , "묶음" ] ).agg(
    폐업률 = ( "폐업률" , "mean" )
).reset_index()
r["연도"] = r["연도"].astype(str)

dongne = r[ r["묶음"] == "동네" ]
center = r[ r["묶음"] == "중심" ]
print( dongne )
print( center )

plt.figure( figsize = ( 8 , 5 ) )
plt.plot( dongne["연도"] , dongne["폐업률"] , label = "동네 상권(골목+전통시장)" , color = "red" , marker = "o" )
plt.plot( center["연도"] , center["폐업률"] , label = "중심 상권(발달+관광특구)" , color = "blue" , marker = "o" )
plt.title( "연도별 폐업률 : 동네 상권 vs 중심 상권" )
plt.xlabel( "연도" )
plt.ylabel( "폐업률(%)" )
plt.legend()
plt.grid()
plt.show()

# 현황 : 상권 4유형
r4 = g.groupby( [ "연도" , "상권_구분_코드_명" ] ).agg(
    폐업률 = ( "폐업률" , "mean" ),
    상권수 = ( "상권_코드" , "count" )
).reset_index()
r4["연도"] = r4["연도"].astype(str)

a = r4[ r4["상권_구분_코드_명"] == "골목상권" ]
b = r4[ r4["상권_구분_코드_명"] == "전통시장" ]
c = r4[ r4["상권_구분_코드_명"] == "발달상권" ]
d = r4[ r4["상권_구분_코드_명"] == "관광특구" ]
print( r4 )

plt.figure( figsize = ( 8 , 5 ) )
plt.plot( a["연도"] , a["폐업률"] , label = "골목상권" , color = "red" , marker = "o" )
plt.plot( b["연도"] , b["폐업률"] , label = "전통시장" , color = "orange" , marker = "o" )
plt.plot( c["연도"] , c["폐업률"] , label = "발달상권" , color = "blue" , marker = "o" )
plt.plot( d["연도"] , d["폐업률"] , label = "관광특구" , color = "green" , linestyle = "--" , marker = "o" )
plt.title( "연도별 폐업률 : 상권 4유형" )
plt.xlabel( "연도" )
plt.ylabel( "폐업률(%)" )
plt.legend()
plt.grid()
plt.show()