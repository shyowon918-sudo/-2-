import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#--- 상단 공지---
st.error(" **📢 본 대시보드는 2024년 산불 발생 공공데이터를 기반으로 제작되었습니다.**")

#--- 타이틀 ---
st.markdown("<h1 style='text-align: center;'> ⛰️ 2024년 전국 산불 피해 공공데이터 분석 대시보드🔥</h1>", unsafe_allow_html=True)


# 1. 페이지 설정
st.set_page_config(page_title="2024 산불 정밀 분석 대시보드", layout="wide")

# --- 데이터베이스 및 데이터 로드 (이전과 동일한 로직) ---
@st.cache_resource
def init_full_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS fire_stations (name TEXT, address TEXT, region TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS weather (region TEXT, humidity REAL, wind_speed REAL, area REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS wildfires (date TEXT, location TEXT, cause TEXT, area REAL, region TEXT)")

    # 데이터 삽입 (사용자 제공 데이터 기반)
    raw_data = [
        ('20241231','군위','입산자실화',19.79), ('20241230','양평','재처리부주의',0.06),
        ('20241230','파주','담뱃불실화',0.7), ('20241229','강릉','쓰레기소각',0.1),
        ('20240427','철원','입산자실화',0.3), ('20240401','수원','재처리부주의',1.2)
    ]
    for d, l, c, a in raw_data:
        cursor.execute("INSERT INTO wildfires VALUES (?,?,?,?,?)", (d, l, c, a, "지역"))
    
    cursor.executemany("INSERT INTO fire_stations VALUES (?,?,?)", [
        ('수원소방서', '경기도 수원시', '경기'), ('철원소방서', '강원도 철원군', '강원'), ('파주소방서', '경기도 파주시', '경기')
    ])
    
    cursor.executemany("INSERT INTO weather VALUES (?,?,?,?)", [
        ('경기', 42.0, 5.0, 150.0), ('강원', 35.0, 12.0, 800.0), ('경북', 38.0, 10.0, 400.0)
    ])
    conn.commit()
    return conn

conn = init_full_db()


# --- 사이드바 ---
st.sidebar.header("📍 상세 지역 분석")
search_loc = st.sidebar.text_input("분석 지역 입력 (예: 수원, 철원, 파주, 군위)", key="search_input")

# --- [차트 1] 대응 사각지대 분석 (개선: 이중 축 차트) ---
st.header("1. 지역별 피해 면적 vs 소방 인프라 비교")

if not search_loc:
    st.info("💡 **왼쪽 사이드바에 분석하고 싶은 지역을 입력하세요.** (전국 2024년 데이터 매칭)")
else:
    sql1 = f"""
    SELECT location, SUM(area) as total_area,
    (SELECT COUNT(*) FROM fire_stations f WHERE f.address LIKE '%' || '{search_loc}' || '%') as station_count
    FROM wildfires WHERE location LIKE '%' || '{search_loc}' || '%' GROUP BY location
    """
    df1 = pd.read_sql(sql1, conn)
    
    if not df1.empty:
        # 이중 축 차트 생성
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 1. 막대 그래프 (피해 면적)
        fig1.add_trace(
            go.Bar(x=df1['location'], y=df1['total_area'], name="피해 면적 (ha)", marker_color='rgba(255, 75, 75, 0.7)'),
            secondary_y=False,
        )
        # 2. 라인 그래프 (소방서 수)
        fig1.add_trace(
            go.Scatter(x=df1['location'], y=df1['station_count'], name="소방 시설 수", 
                       mode='lines+markers+text', text=df1['station_count'], textposition="top center",
                       line=dict(color='RoyalBlue', width=4), marker=dict(size=12)),
            secondary_y=True,
        )

        fig1.update_layout(title_text=f"'{search_loc}' 지역 산불 대응 지표 (2024)", hovermode="x unified")
        fig1.update_yaxes(title_text="<b>피해 면적</b> (ha)", secondary_y=False)
        fig1.update_yaxes(title_text="<b>소방 시설 수</b> (개)", secondary_y=True)
        
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning(f"⚠️ '{search_loc}' 지역에 대한 직접적인 2024년 산불 기록이 없습니다. 근처 지역을 입력해 보세요.")

st.divider()

# --- [차트 2] 전국 기상 상관관계 (개선: 점과 선 확대) ---
st.header("2. [전국] 습도와 피해 규모 상관관계 (정밀 분석)")

sql2 = "SELECT humidity, area FROM weather"
df2 = pd.read_sql(sql2, conn)

# 추세선 강조를 위한 Plotly Express 설정
fig2 = px.scatter(df2, x="humidity", y="area", trendline="ols",
                 labels={"humidity": "습도 (%)", "area": "피해 면적 (ha)"},
                 title="전국 데이터 기반 기상 상관성 (굵은 추세선 적용)")

# 점(Marker) 크기 확대 및 스타일 변경
fig2.update_traces(marker=dict(size=15, opacity=0.6, line=dict(width=2, color='DarkSlateGrey')), 
                   selector=dict(mode='markers'))

# 추세선(Line) 두께 대폭 확대
fig2.update_traces(line=dict(width=6, color="red"), selector=dict(mode='lines'))

st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- [차트 3] 전국 발생 원인 ---
st.header("3. [전국] 2024년 산불 원인별 피해 순위")
sql3 = "SELECT cause, SUM(area) as total_area FROM wildfires GROUP BY cause ORDER BY total_area DESC"
df3 = pd.read_sql(sql3, conn)

fig3 = px.bar(df3, x="cause", y="total_area", color="total_area", 
             text_auto='.2f', color_continuous_scale="Reds", labels={"cause": "발생 원인", "total_area": "누적 피해 면적 (ha)", "total_area": "피해 규모"},
        title="2024년 전국 산불 원인별 피해 규모 (그라데이션 적용)")

fig3.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)

st.plotly_chart(fig3, use_container_width=True)

# --- 주의 문구 및 소방관 헌정 메시지 ---
st.error("🚨 **[주의] 대부분의 산불은 인재(人災)입니다. 우리의 작은 부주의가 거대한 재난을 만듭니다.**")
st.markdown("---")
st.success("""
**👨‍🚒 소방관님들께 드리는 헌사**  
불길 속 재난 현장에서 국민의 생명과 안전을 지키기 위해 헌신하시는 소방관님들의 노고에 깊이 감사드립니다.  
자신의 목숨을 걸고 위급한 순간 가장 먼저 달려와 절망 속에서 희망을 밝혀주시는 숭고한 봉사에 진심 어린 존경과 지지를 보냅니다.
""")
