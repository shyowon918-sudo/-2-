import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="산불 분석 시각화 대시보드", layout="wide")

# --- 데이터베이스 세션 연결 ---
def get_connection():
    conn = sqlite3.connect(':memory:', check_same_thread=False) # 테스트를 위해 메모리 DB 사용
    return conn

conn = get_connection()
cursor = conn.cursor()

# --- 데이터 세팅 (샘플 데이터 생성) ---
def init_db():
    # 1. 소방서 데이터
    cursor.execute("CREATE TABLE IF NOT EXISTS fire_stations (name TEXT, address TEXT, phone TEXT, x REAL, y REAL, region TEXT)")
    # 2. 기상 데이터
    cursor.execute("CREATE TABLE IF NOT EXISTS weather (region TEXT, year INTEGER, temp REAL, humidity REAL, rain REAL, wind_speed REAL)")
    # 3. 산불 데이터
    cursor.execute("CREATE TABLE IF NOT EXISTS wildfires (year INTEGER, region TEXT, cause TEXT, area REAL)")
    
    # 샘플 데이터 삽입 (예시)
    stations = [('강원소방서', '강원도...', '033-', 128.0, 37.5, '강원'), ('경기소방서', '경기도...', '031-', 127.0, 37.2, '경기')]
    cursor.executemany("INSERT INTO fire_stations VALUES (?,?,?,?,?,?)", stations)
    
    weather_data = [('강원', 2023, 15.2, 45.0, 100, 5.5), ('경기', 2023, 16.0, 55.0, 120, 3.2)]
    cursor.executemany("INSERT INTO weather VALUES (?,?,?,?,?,?)", weather_data)
    
    fires = [(2023, '강원', '입산자 실화', 500.5), (2023, '경기', '담배꽁초', 50.2), (2023, '강원', '쓰레기 소각', 120.0)]
    cursor.executemany("INSERT INTO wildfires VALUES (?,?,?,?)", fires)
    conn.commit()

init_db()

# --- 대시보드 UI ---
st.title("🔥 산불 발생 현황 및 취약 지역 분석 대시보드")
st.markdown("산림청, 기상청 및 소방청 데이터를 통합하여 산불 위험을 분석합니다.")

# 사이드바: 지역 선택
region_list = ["전체", "강원", "경기", "경북", "경남", "충북", "충남", "전북", "전남"]
selected_region = st.sidebar.selectbox("📍 분석 지역 선택", region_list)

# --- 차트 1: 화재 대응 속도와 취약 지역 (버블 차트) ---
st.header("1. 지역별 대응 취약 지역 파악")
sql1 = """
SELECT w.region, SUM(w.area) as total_area, COUNT(f.name) as station_count
FROM wildfires w
LEFT JOIN fire_stations f ON w.region = f.region
GROUP BY w.region
"""
if selected_region != "전체":
    sql1 = sql1.replace("GROUP BY", f"WHERE w.region = '{selected_region}' GROUP BY")

df1 = pd.read_sql(sql1, conn)

col1_1, col1_2 = st.columns([2, 1])
with col1_1:
    fig1 = px.scatter(df1, x="station_count", y="total_area", size="total_area", 
                     color="region", hover_name="region", text="region",
                     labels={"station_count": "소방서 수", "total_area": "누적 피해 면적(ha)"},
                     title=f"지역별 산불 피해 면적 대비 소방 시설 현황")
    st.plotly_chart(fig1, use_container_width=True)

with col1_2:
    st.subheader("📝 SQL Query")
    st.code(sql1, language='sql')
    st.subheader("💡 인사이트")
    st.write("- 버블의 크기가 크고 왼쪽(소방서 적음)에 위치할수록 **대응 사각지대**입니다.")
    st.write("- 선택한 지역의 소방 인프라 확충 필요성을 직관적으로 파악할 수 있습니다.")

st.divider()

# --- 차트 2: 기상 조건과 피해 면적 상관관계 ---
st.header("2. 기상 조건(습도/풍속)과 피해 면적의 관계")
sql2 = """
SELECT w.humidity, w.wind_speed, f.area
FROM weather w
JOIN wildfires f ON w.region = f.region AND w.year = f.year
"""
df2 = pd.read_sql(sql2, conn)

col2_1, col2_2 = st.columns([2, 1])
with col2_1:
    # 산점도 (습도 vs 면적)
    fig2 = px.scatter(df2, x="humidity", y="area", trendline="ols",
                     labels={"humidity": "상대습도(%)", "area": "피해 면적(ha)"},
                     title="습도와 피해 면적 상관관계")
    
    # 풍속 영향도 추가 (빨간 선)
    df2_sorted = df2.sort_values("wind_speed")
    fig2.add_trace(go.Scatter(x=df2_sorted["humidity"], y=df2_sorted["wind_speed"] * 10, 
                             mode='lines', name='풍속 가중치(추세)', line=dict(color='red', width=3)))
    st.plotly_chart(fig2, use_container_width=True)

with col2_2:
    st.subheader("📝 SQL Query")
    st.code(sql2, language='sql')
    st.subheader("💡 인사이트")
    st.write("- 습도가 낮을수록 피해 면적이 급증하는 반비례 관계를 보입니다.")
    st.write("- **빨간 선(풍속)**이 상승할수록 피해 면적의 규모가 커지는 양의 상관관계가 뚜렷합니다.")

st.divider()

# --- 차트 3: 발생 원인별 피해 분석 ---
st.header("3. 발생 원인별 피해 규모 순위")
sql3 = """
SELECT cause, SUM(area) as total_area
FROM wildfires
GROUP BY cause
ORDER BY total_area DESC
"""
df3 = pd.read_sql(sql3, conn)

col3_1, col3_2 = st.columns([2, 1])
with col3_1:
    fig3 = px.bar(df3, x="cause", y="total_area", color="total_area",
                 labels={"cause": "발생 원인", "total_area": "총 피해 면적(ha)"},
                 title="원인별 피해 면적 합계 (내림차순)")
    st.plotly_chart(fig3, use_container_width=True)

with col3_2:
    st.subheader("📝 SQL Query")
    st.code(sql3, language='sql')
    st.subheader("💡 인사이트")
    st.write("- 통계적으로 자연발화보다 **인적 요인**에 의한 피해 규모가 압도적입니다.")
    st.write("- 특히 입산자 실화와 소각 행위가 주요 원인으로 분석됩니다.")

# --- 경고 문구 ---
st.error("⚠️ **주의: 대부분의 산불은 우리의 사소한 부주의에서 시작됩니다.**")
st.info("입산 시 화기 소지 금지 및 논·밭두렁 소각 자제를 통해 우리의 소중한 산림을 지킵시다.")