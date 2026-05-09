import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 1. 페이지 설정 및 레이아웃
st.set_page_config(page_title="전국 산불 취약 지역 분석 대시보드", layout="wide")

# --- 데이터베이스 연결 및 초기화 (샘플 데이터 생성) ---
@st.cache_resource
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    
    # 테이블 생성
    cursor.execute("CREATE TABLE IF NOT EXISTS fire_stations (name TEXT, address TEXT, phone TEXT, x REAL, y REAL, region TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS weather (region TEXT, year INTEGER, temp REAL, humidity REAL, rain REAL, wind_speed REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS wildfires (year INTEGER, region TEXT, location TEXT, cause TEXT, area REAL)")
    
    # 샘플 데이터 (속초시 등 전국 데이터 예시)
    stations = [
        ('속초소방서', '강원도 속초시 번영로', '033-123', 128.5, 38.2, '강원'),
        ('강릉소방서', '강원도 강릉시 홍제동', '033-456', 128.8, 37.7, '강원'),
        ('안동소방서', '경상북도 안동시 제비원로', '054-789', 128.7, 36.5, '경북')
    ]
    cursor.executemany("INSERT INTO fire_stations VALUES (?,?,?,?,?,?)", stations)
    
    weather_data = [
        ('강원', 2023, 15.2, 42.0, 100, 8.5),
        ('경북', 2023, 16.5, 38.0, 80, 10.2)
    ]
    cursor.executemany("INSERT INTO weather VALUES (?,?,?,?,?,?)", weather_data)
    
    fires = [
        (2023, '강원', '속초시', '입산자 실화', 450.0),
        (2023, '강원', '강릉시', '담배꽁초', 120.5),
        (2023, '경북', '안동시', '쓰레기 소각', 320.0),
        (2023, '강원', '속초시', '논밭 소각', 50.0)
    ]
    cursor.executemany("INSERT INTO wildfires VALUES (?,?,?,?,?)", fires)
    conn.commit()
    return conn

conn = init_db()

# --- 사이드바: 지역 필터 및 안내 ---
st.sidebar.header("🗺️ 분석 지역 설정")
sido_list = ["선택하세요", "강원", "경기", "경북", "경남", "전북", "전남", "충북", "충남", "서울", "대구", "부산"]
selected_sido = st.sidebar.selectbox("1. 광역 지역(시/도) 선택", sido_list, key="sido_box")

st.sidebar.warning("⚠️ **반드시 아래에 상세 지역을 입력해야 분석이 시작됩니다.**")
selected_sigungu = st.sidebar.text_input("2. 상세 지역(시/군/구) 입력", placeholder="예: 속초시, 안동시", key="sigungu_input")

# --- 메인 대시보드 ---
st.title("🔥 산불 분석 시각화 및 대응 체계 대시보드")

if selected_sido == "선택하세요" or not selected_sigungu:
    st.info("💡 **좌측 사이드바에서 광역 지역을 선택하고 상세 지역(시/군/구)을 입력하면 분석 차트가 나타납니다.**")
    st.stop() # 이후 코드 실행 방지

# --- 데이터 쿼리 ---
# 차트 1용 데이터 (선택된 시군구 상세)
sql1 = f"""
SELECT 
    w.location as sigungu, 
    SUM(w.area) as total_area,
    (SELECT COUNT(*) FROM fire_stations f WHERE f.address LIKE '%' || '{selected_sigungu}' || '%') as station_count
FROM wildfires w
WHERE w.region LIKE '%{selected_sido}%' AND w.location LIKE '%{selected_sigungu}%'
GROUP BY w.location
"""
df1 = pd.read_sql(sql1, conn)

# 차트 2용 데이터 (기상 상관관계 - 해당 광역 지역 기준)
sql2 = f"SELECT w.humidity, w.wind_speed, f.area FROM weather w JOIN wildfires f ON w.region = f.region WHERE w.region LIKE '%{selected_sido}%'"
df2 = pd.read_sql(sql2, conn)

# 차트 3용 데이터 (원인별 분석 - 전국 혹은 해당 지역)
sql3 = f"SELECT cause, SUM(area) as total_area FROM wildfires WHERE location LIKE '%{selected_sigungu}%' GROUP BY cause ORDER BY total_area DESC"
df3 = pd.read_sql(sql3, conn)

# --- [차트 1] 화재 대응 속도와 취약 지역 (버블 차트) ---
st.header(f"1. {selected_sigungu} 대응 취약 지역 파악")
if not df1.empty:
    col1_1, col1_2 = st.columns([2, 1])
    with col1_1:
        fig1 = px.scatter(df1, x="station_count", y="total_area", size="total_area", 
                         color_discrete_sequence=['#FF4B4B'], hover_name="sigungu",
                         labels={"station_count": "관내 소방시설 수", "total_area": "누적 피해 면적(ha)"},
                         title=f"{selected_sigungu} 피해 면적 대비 소방 시설 현황", size_max=40)
        st.plotly_chart(fig1, use_container_width=True, key="chart1")
    with col1_2:
        st.subheader("📝 SQL Query")
        st.code(sql1, language='sql')
        st.subheader("💡 인사이트")
        st.write(f"- {selected_sigungu} 지역의 소방시설은 현재 **{df1['station_count'].iloc[0]}개**로 집계됩니다.")
        st.write("- 면적 대비 시설이 좌측 상단에 위치할수록 **대응 사각지대**입니다.")
else:
    st.error("해당 상세 지역의 데이터를 찾을 수 없습니다.")

st.divider()

# --- [차트 2] 기상 조건과 피해 면적 (상관관계) ---
st.header("2. 기상 조건(습도/풍속)과 피해 규모의 상관성")
if not df2.empty:
    col2_1, col2_2 = st.columns([2, 1])
    with col2_1:
        # 산점도 및 추세선
        fig2 = px.scatter(df2, x="humidity", y="area", trendline="ols",
                         labels={"humidity": "상대습도(%)", "area": "피해 면적(ha)"},
                         title=f"{selected_sido} 지역 습도별 피해 면적 추이",
                         trendline_color_override="red")
        st.plotly_chart(fig2, use_container_width=True, key="chart2")
    with col2_2:
        st.subheader("📝 SQL Query")
        st.code(sql2, language='sql')
        st.subheader("💡 인사이트")
        st.write("- **습도**가 낮을수록 연소 속도가 빨라져 피해 면적이 커지는 경향을 보입니다.")
        st.write("- **빨간색 추세선**의 기울기가 가파를수록 기상 변화에 민감한 위험 지역입니다.")
st.divider()

# --- [차트 3] 발생 원인별 피해 분석 ---
st.header(f"3. {selected_sigungu} 산불 발생 원인 순위")
if not df3.empty:
    col3_1, col3_2 = st.columns([2, 1])
    with col3_1:
        fig3 = px.bar(df3, x="cause", y="total_area", color="total_area",
                     labels={"cause": "원인", "total_area": "피해 합계(ha)"},
                     title="원인별 피해 면적 규모")
    st.plotly_chart(fig3, use_container_width=True, key="chart3")
    with col3_2:
        st.subheader("📝 SQL Query")
        st.code(sql3, language='sql')
        st.subheader("💡 인사이트")
        st.write(f"- {selected_sigungu}의 주요 원인은 **{df3['cause'].iloc[0]}**입니다.")
        st.write("- 인적 부주의에 의한 산불이 전체의 높은 비중을 차지합니다.")

# --- 최종 경고 문구 ---
st.markdown("---")
st.error("⚠️ **[경고] 우리 모두의 부주의가 소중한 산림을 앗아갑니다.**")
st.info("성묘객 실화, 쓰레기 소각 금지 등 작은 실천이 산불 사각지대를 없애는 첫걸음입니다.")
