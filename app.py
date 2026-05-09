import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="전국 산불 대응 사각지대 분석", layout="wide")

# DB 연결 및 데이터 로드 (가정)
conn = sqlite3.connect('wildfire.db', check_same_thread=False)

# --- 사이드바: 지역 필터 설정 ---
st.sidebar.header("🗺️ 지역 필터 설정")
st.sidebar.markdown("---")

# 1. 광역 지역 선택
sido_list = ["선택하세요", "강원", "경기", "경북", "경남", "전북", "전남", "충북", "충남", "서울", "인천", "대전", "대구", "부산", "울산", "세종", "제주"]
selected_sido = st.sidebar.selectbox("1. 광역 지역(시/도)을 선택하세요", sido_list)

# 2. 상세 지역 입력 (강조)
st.sidebar.warning("⚠️ **반드시 아래에 상세 지역(시/군/구)을 입력해야 정확한 분석이 가능합니다.**")
selected_sigungu = st.sidebar.text_input("2. 상세 지역(시/군/구) 입력", placeholder="예: 속초시, 안동시, 평창군")

# --- 메인 화면 로직 ---
st.title("🔥 전국 산불 대응 취약 지역 분석")

# 지역 선택 여부 검증
if selected_sido == "선택하세요" or not selected_sigungu:
    # 사용자가 지역을 선택/입력하지 않았을 때 보여줄 초기 화면
    st.info("💡 **좌측 사이드바에서 분석하고자 하는 [광역 지역]을 선택하고 [상세 지역]을 입력해 주세요.**")
    st.image("https://images.unsplash.com/photo-1542125387-c71274d94f0a?auto=format&fit=crop&q=80&w=1000", caption="정확한 지역 분석을 위해 상세 위치 정보가 필요합니다.")
    
else:
    # 사용자가 두 정보를 모두 입력했을 때만 차트 렌더링
    st.success(f"🔎 **{selected_sido} {selected_sigungu}** 지역에 대한 분석 결과입니다.")
    
    # 데이터 쿼리
    query = f"""
    SELECT 
        w.region as sido,
        w.location as sigungu, 
        SUM(w.area) as total_area,
        (SELECT COUNT(*) FROM fire_stations f WHERE f.address LIKE '%' || '{selected_sigungu}' || '%') as station_count
    FROM wildfires w
    WHERE w.region LIKE '%{selected_sido}%' AND w.location LIKE '%{selected_sigungu}%'
    GROUP BY w.region, w.location
    """
    df_area = pd.read_sql(query, conn)

    if not df_area.empty:
        # [차트 1] 버블 차트 시각화
        col1, col2 = st.columns([3, 1])
        with col1:
            fig1 = px.scatter(
                df_area, 
                x="station_count", 
                y="total_area", 
                size="total_area", 
                color_discrete_sequence=['#FF4B4B'],
                hover_name="sigungu",
                labels={"station_count": "소방시설 수", "total_area": "피해 면적(ha)"},
                title=f"{selected_sigungu} 산불 대응 인프라 분석",
                size_max=50
            )
            st.plotly_chart(fig1, use_container_width=True, key="bubble_detail")
        
        with col2:
            st.subheader("📝 사용된 SQL")
            st.code(query, language="sql")
            st.subheader("💡 인사이트")
            st.write(f"- {selected_sigungu} 내 소방시설 개수: **{df_area['station_count'].iloc[0]}개**")
            st.write(f"- 누적 피해 면적: **{df_area['total_area'].iloc[0]} ha**")
            
    else:
        st.error(f"❌ '{selected_sigungu}'에 대한 데이터를 찾을 수 없습니다. 지역명을 다시 확인해 주세요.")

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="전국 산불 대응 사각지대 분석", layout="wide")

# DB 연결 및 데이터 로드 (가정)
conn = sqlite3.connect('wildfire.db', check_same_thread=False)

# --- 사이드바: 지역 필터 설정 ---
st.sidebar.header("🗺️ 지역 필터 설정")
st.sidebar.markdown("---")

# 1. 광역 지역 선택
sido_list = ["선택하세요", "강원", "경기", "경북", "경남", "전북", "전남", "충북", "충남", "서울", "인천", "대전", "대구", "부산", "울산", "세종", "제주"]
selected_sido = st.sidebar.selectbox("1. 광역 지역(시/도)을 선택하세요", sido_list)

# 2. 상세 지역 입력 (강조)
st.sidebar.warning("⚠️ **반드시 아래에 상세 지역(시/군/구)을 입력해야 정확한 분석이 가능합니다.**")
selected_sigungu = st.sidebar.text_input("2. 상세 지역(시/군/구) 입력", placeholder="예: 속초시, 안동시, 평창군")

# --- 메인 화면 로직 ---
st.title("🔥 전국 산불 대응 취약 지역 분석")

# 지역 선택 여부 검증
if selected_sido == "선택하세요" or not selected_sigungu:
    # 사용자가 지역을 선택/입력하지 않았을 때 보여줄 초기 화면
    st.info("💡 **좌측 사이드바에서 분석하고자 하는 [광역 지역]을 선택하고 [상세 지역]을 입력해 주세요.**")
    st.image("https://images.unsplash.com/photo-1542125387-c71274d94f0a?auto=format&fit=crop&q=80&w=1000", caption="정확한 지역 분석을 위해 상세 위치 정보가 필요합니다.")
    
else:
    # 사용자가 두 정보를 모두 입력했을 때만 차트 렌더링
    st.success(f"🔎 **{selected_sido} {selected_sigungu}** 지역에 대한 분석 결과입니다.")
    
    # 데이터 쿼리
    query = f"""
    SELECT 
        w.region as sido,
        w.location as sigungu, 
        SUM(w.area) as total_area,
        (SELECT COUNT(*) FROM fire_stations f WHERE f.address LIKE '%' || '{selected_sigungu}' || '%') as station_count
    FROM wildfires w
    WHERE w.region LIKE '%{selected_sido}%' AND w.location LIKE '%{selected_sigungu}%'
    GROUP BY w.region, w.location
    """
    df_area = pd.read_sql(query, conn)

    if not df_area.empty:
        # [차트 1] 버블 차트 시각화
        col1, col2 = st.columns([3, 1])
        with col1:
            fig1 = px.scatter(
                df_area, 
                x="station_count", 
                y="total_area", 
                size="total_area", 
                color_discrete_sequence=['#FF4B4B'],
                hover_name="sigungu",
                labels={"station_count": "소방시설 수", "total_area": "피해 면적(ha)"},
                title=f"{selected_sigungu} 산불 대응 인프라 분석",
                size_max=50
            )
            st.plotly_chart(fig1, use_container_width=True, key="bubble_detail")
        
        with col2:
            st.subheader("📝 사용된 SQL")
            st.code(query, language="sql")
            st.subheader("💡 인사이트")
            st.write(f"- {selected_sigungu} 내 소방시설 개수: **{df_area['station_count'].iloc[0]}개**")
            st.write(f"- 누적 피해 면적: **{df_area['total_area'].iloc[0]} ha**")
            
    else:
        st.error(f"❌ '{selected_sigungu}'에 대한 데이터를 찾을 수 없습니다. 지역명을 다시 확인해 주세요.")

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
