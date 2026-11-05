import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.rc( 'font' , family = 'Malgun Gothic' )
plt.rcParams['axes.unicode_minus'] = False

s21 = pd.read_csv( "data/store_2021.csv" )
s22 = pd.read_csv( "data/store_2022.csv" )
s23 = pd.read_csv( "data/store_2023.csv" )
s24 = pd.read_csv( "data/store_2024.csv" )
s25 = pd.read_csv( "data/store_2025.csv" )
flow = pd.read_csv( "data/Foot_Traffic.csv" )

store = pd.concat( [ s21 , s22 , s23 , s24 , s25 ] , axis = 0 , ignore_index = True )

print( store.shape , flow.shape )
print( store.isnull().sum().sum() )
print( flow.isnull().sum().sum() )
print( store.shape , store.drop_duplicates().shape )
print( flow.shape , flow.drop_duplicates().shape )
print( ( store["점포_수"] == 0 ).sum() )

store["연도"] = ( store["기준_년분기_코드"] / 10 ).astype(int)
flow["연도"] = ( flow["기준_년분기_코드"] / 10 ).astype(int)
flow = flow[ flow["연도"] <= 2025 ]

store["묶음"] = "중심"
store.loc[ store["상권_구분_코드_명"] == "골목상권" , "묶음" ] = "동네"
store.loc[ store["상권_구분_코드_명"] == "전통시장" , "묶음" ] = "동네"

g = store.groupby( [ "연도" , "상권_코드" , "상권_구분_코드_명" , "묶음" ] ).agg(
    폐업합계 = ( "폐업_점포_수" , "sum" ),
    유사업종합계 = ( "유사_업종_점포_수" , "sum" )
).reset_index()
g["폐업률"] = g["폐업합계"] / g["유사업종합계"] * 100
print( "제외 전" , g.shape )

g = g[ g["유사업종합계"] >= 30 ]

flow["낮비중"] = ( flow["시간대_06_11_유동인구_수"] + flow["시간대_11_14_유동인구_수"] + flow["시간대_14_17_유동인구_수"] ) / flow["총_유동인구_수"] * 100

f = flow.groupby( [ "연도" , "상권_코드" ] ).agg(
    총유동인구 = ( "총_유동인구_수" , "mean" ),
    낮비중 = ( "낮비중" , "mean" )
).reset_index()

m = pd.merge( g , f , on = [ "연도" , "상권_코드" ] , how = "inner" )
print( "합친 후" , m.shape )
print( m.head() )

# 동네 vs 중심
r = m.groupby( [ "연도" , "묶음" ] ).agg(
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

# 4유형 현황
r4 = m.groupby( [ "연도" , "상권_구분_코드_명" ] ).agg(
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

# 연도별 상관계수
years = [ 2021 , 2022 , 2023 , 2024 , 2025 ]
year_str = [ "2021" , "2022" , "2023" , "2024" , "2025" ]
r1_list = []
r2_list = []

for y in years:
    dy = m[ m["연도"] == y ]
    r1_list.append( dy[ [ "총유동인구" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )
    r2_list.append( dy[ [ "낮비중" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )

print( "총유동인구-폐업률 r :" , r1_list )
print( "낮비중-폐업률 r :" , r2_list )

d25 = m[ m["연도"] == 2025 ]

# 가설1 유동인구
plt.figure( figsize = ( 14 , 5 ) )

plt.subplot( 1 , 2 , 1 )
plt.scatter( d25["총유동인구"] , d25["폐업률"] , color = "purple" , s = 20 , alpha = 0.4 )
plt.title( f"가설 1 : 총유동인구 vs 폐업률 (2025, r = {r1_list[4]:.2f})" )
plt.xlabel( "총유동인구" )
plt.ylabel( "폐업률(%)" )
plt.grid()

plt.subplot( 1 , 2 , 2 )
plt.plot( year_str , r1_list , color = "purple" , marker = "o" )
plt.plot( year_str , [ 0 , 0 , 0 , 0 , 0 ] , color = "gray" , linestyle = "--" )
plt.title( "가설 1 : 연도별 상관계수 r (총유동인구 - 폐업률)" )
plt.xlabel( "연도" )
plt.ylabel( "상관계수 r" )
plt.grid()
plt.show()

# 가설2 낮비중
plt.figure( figsize = ( 14 , 5 ) )

plt.subplot( 1 , 2 , 1 )
plt.scatter( d25["낮비중"] , d25["폐업률"] , color = "purple" , s = 20 , alpha = 0.4 )
plt.title( f"가설 2 : 낮비중 vs 폐업률 (2025, r = {r2_list[4]:.2f})" )
plt.xlabel( "낮비중(%)" )
plt.ylabel( "폐업률(%)" )
plt.grid()

plt.subplot( 1 , 2 , 2 )
plt.plot( year_str , r2_list , color = "purple" , marker = "o" )
plt.plot( year_str , [ 0 , 0 , 0 , 0 , 0 ] , color = "gray" , linestyle = "--" )
plt.title( "가설 2 : 연도별 상관계수 r (낮비중 - 폐업률)" )
plt.xlabel( "연도" )
plt.ylabel( "상관계수 r" )
plt.grid()
plt.show()

# 히트맵
corr_matrix = d25[ [ "폐업률" , "총유동인구" , "낮비중" ] ].corr()
sns.heatmap( corr_matrix , cmap = "coolwarm" , fmt = ".2f" , annot = True )
plt.title( "상관계수 히트맵 (2025)" )
plt.show()