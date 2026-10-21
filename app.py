from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

# 1. 화면 기본 설정
st.set_page_config(
    page_title="철도 데이터 분석 대시보드",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="auto",
)

BLUE, TEAL, RED = "#3478F6", "#19A79B", "#EF6B73"

# 2. 화면 스타일: 직접 만든 요소와 이름을 지정한 영역 중심으로 적용
st.markdown("""
<style>
.block-container {max-width:1480px; padding-top:4.5rem; padding-bottom:2.5rem;}
.rail-hero {
    display:flex; justify-content:space-between; align-items:center; gap:24px;
    padding:30px 34px; margin-bottom:12px; border-radius:20px;
    background:linear-gradient(115deg,#142543,#203F69); color:white;
    box-shadow:0 8px 24px rgba(20,37,67,.10);
}
.rail-kicker {font-size:11px; letter-spacing:2px; color:#AAC9F5; font-weight:700;}
.rail-hero h1 {color:white; font-size:clamp(24px,2.3vw,34px); margin:9px 0; padding:0; line-height:1.4;}
.rail-hero p {color:#CEDCF0; font-size:14px; margin:0;}
.rail-selection {border-left:1px solid #527093; padding-left:24px; min-width:180px;}
.rail-selection span {display:block; color:#B8CDE9; font-size:12px;}
.rail-selection strong {display:block; color:white; font-size:23px; margin:5px 0;}
.rail-selection small {color:#D5E3F5; font-size:12px;}
.rail-notice {color:#76849A; font-size:12px; margin:0 0 20px;}
.rail-kpi {
    min-height:150px; padding:20px 22px; border:1px solid #E3EAF5;
    border-top:3px solid var(--accent); border-radius:16px;
    background:linear-gradient(145deg,#FFFFFF,#F8FAFE);
    box-shadow:0 4px 14px rgba(30,60,100,.035);
}
.rail-kpi-label {color:#6F7E94; font-size:13px; font-weight:600;}
.rail-kpi-value {color:#192D4B; font-size:clamp(26px,2.4vw,36px); font-weight:750; margin:8px 0 5px; line-height:1.25;}
.rail-kpi-unit {font-size:15px; font-weight:500; color:#8B98AA; margin-left:5px;}
.rail-kpi-note {color:#8290A4; font-size:12px;}
.rail-side-brand {font-size:14px; font-weight:800; letter-spacing:1.5px; color:#3478F6; padding:8px 0;}
.rail-report {white-space:pre-wrap; line-height:1.9; font-size:14px; padding:18px; border-radius:12px; background:rgba(130,150,180,.07);}
.st-key-dashboard_tabs {margin-top:10px;}
.st-key-dashboard_tabs [role="tablist"] {gap:8px; padding:5px; border-radius:12px; background:rgba(130,150,180,.09);}
.st-key-dashboard_tabs [role="tab"] {padding:0 20px; height:44px; border-radius:8px;}
.st-key-dashboard_tabs [role="tab"][aria-selected="true"] {background:#FFF; color:#2861BE; box-shadow:0 2px 7px rgba(20,40,70,.07);}
.st-key-dashboard_tabs [data-baseweb="tab-highlight"],
.st-key-dashboard_tabs .react-aria-SelectionIndicator {background:#3478F6 !important;}
.st-key-downloads button {border-radius:10px; min-height:44px;}
@media (max-width:768px) {
    .rail-hero {flex-direction:column; align-items:flex-start; padding:24px;}
    .rail-selection {border-left:0; border-top:1px solid #527093; padding:14px 0 0; width:100%;}
    .rail-kpi {min-height:125px; margin-bottom:8px;}
    .st-key-dashboard_tabs [role="tab"] {padding:0 12px;}
}
</style>
""", unsafe_allow_html=True)


def metric_card(label, value, unit, note, accent):
    """요약 지표를 카드로 표시합니다."""
    st.markdown(
        f'<div class="rail-kpi" style="--accent:{accent}">'
        f'<div class="rail-kpi-label">{escape(label)}</div>'
        f'<div class="rail-kpi-value">{escape(value)}'
        f'<span class="rail-kpi-unit">{escape(unit)}</span></div>'
        f'<div class="rail-kpi-note">{escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


def style_line_chart(fig, height=370):
    """두 온도 차트에 같은 색상·축·범례 스타일을 적용합니다."""
    fig.update_layout(
        template="plotly_white", height=height,
        margin=dict(l=10, r=15, t=35, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, Malgun Gothic, sans-serif", size=12, color="#75839A"),
        legend=dict(orientation="h", y=1.13, x=0, title_text=""),
        hovermode="x unified",
    )
    fig.update_xaxes(title=None, showgrid=False, tickformat="%m.%d\n%H:%M")
    fig.update_yaxes(title="온도 (℃)", gridcolor="#EAF0F7", zeroline=False)
    return fig


def show_table(data, height=280):
    st.dataframe(
        data, hide_index=True, width="stretch", height=height,
        column_config={
            "측정시각": st.column_config.DatetimeColumn("측정 시각", format="YYYY-MM-DD HH:mm"),
            "목표시각": st.column_config.DatetimeColumn("목표 시각", format="YYYY-MM-DD HH:mm"),
            "온도_C": st.column_config.NumberColumn("온도 (℃)", format="%.1f"),
            "다음온도_C": st.column_config.NumberColumn("실제 다음 온도 (℃)", format="%.1f"),
            "AI예측온도_C": st.column_config.NumberColumn("AI 예측 온도 (℃)", format="%.1f"),
        },
    )


# 3. 데이터 읽기
DATA_PATH = "/content/analysis_result.csv"
try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    st.error(f"데이터 파일을 찾을 수 없습니다. {DATA_PATH} 경로를 확인하세요.")
    st.stop()

required = ["설비ID", "측정시각", "목표시각", "온도_C", "AI결과", "다음온도_C", "AI예측온도_C"]
missing = [column for column in required if column not in df.columns]
if missing:
    st.error("데이터에 필요한 열이 없습니다: " + ", ".join(missing))
    st.stop()

df["측정시각"] = pd.to_datetime(df["측정시각"], errors="coerce")
df["목표시각"] = pd.to_datetime(df["목표시각"], errors="coerce")
for column in ["온도_C", "다음온도_C", "AI예측온도_C"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")

invalid_count = int(df[["설비ID", "측정시각"]].isna().any(axis=1).sum())
df = df.dropna(subset=["설비ID", "측정시각"]).sort_values("측정시각")
if df.empty:
    st.warning("조회할 수 있는 설비와 측정 시각 데이터가 없습니다.")
    st.stop()

# 4. 사이드바
with st.sidebar:
    st.markdown('<div class="rail-side-brand">RAIL ANALYTICS</div>', unsafe_allow_html=True)
    st.caption("설비 데이터 탐색")
    st.divider()
    st.markdown("### 조회 조건")
    equipment = st.selectbox("설비선택", df["설비ID"].unique())
    equipment_view = df[df["설비ID"] == equipment]
    first_day = equipment_view["측정시각"].min().date()
    last_day = equipment_view["측정시각"].max().date()

    start = st.date_input(
        "시작일", first_day, min_value=first_day, max_value=last_day,
        key=f"rail_start_{equipment}",
    )
    end = st.date_input(
        "종료일", last_day, min_value=first_day, max_value=last_day,
        key=f"rail_end_{equipment}",
    )
    st.divider()
    st.caption("선택 설비의 자료 보유 기간")
    st.write(f"{first_day:%Y.%m.%d} ~ {last_day:%Y.%m.%d}")
    st.caption(f"전체 {len(equipment_view):,}건 · 시작일과 종료일 포함")
    if invalid_count:
        st.warning(f"설비ID 또는 측정 시각이 없는 {invalid_count:,}행은 조회에서 제외했습니다.")

# 5. 상단 헤더
st.markdown(
    f'<div class="rail-hero"><div>'
    f'<div class="rail-kicker">RAIL DATA / ANALYTICS</div>'
    f'<h1>철도 데이터 분석 대시보드</h1>'
    f'<p>설비 현황과 AI 분석 결과를 한눈에 확인하세요.</p></div>'
    f'<div class="rail-selection"><span>선택 설비</span>'
    f'<strong>{escape(str(equipment))}</strong>'
    f'<small>{start:%Y.%m.%d} — {end:%Y.%m.%d}</small></div></div>'
    f'<div class="rail-notice">교육용 가상 자료입니다. AI 확인후보는 고장 확정이 아닙니다.</div>',
    unsafe_allow_html=True,
)

if start > end:
    st.warning("시작일이 종료일보다 늦습니다. 조회 기간을 다시 선택하세요.")
    st.stop()

view = equipment_view[
    (equipment_view["측정시각"].dt.date >= start)
    & (equipment_view["측정시각"].dt.date <= end)
].copy()
if view.empty:
    st.info("선택한 기간에 조회 결과가 없습니다. 날짜를 다시 선택하세요.")
    st.stop()

# 6. 공통 계산과 요약 카드
candidates = view[view["AI결과"] == "확인후보"]
pred = view.dropna(subset=["다음온도_C", "AI예측온도_C"])
mae = (pred["다음온도_C"] - pred["AI예측온도_C"]).abs().mean()
mae_value = f"{mae:.2f}" if pd.notna(mae) else "—"
mae_text = f"{mae:.2f} ℃" if pd.notna(mae) else "계산할 자료 없음"
average_temp = view["온도_C"].mean()
average_value = f"{average_temp:.1f}" if pd.notna(average_temp) else "—"
candidate_rate = len(candidates) / len(view) * 100

kpi1, kpi2, kpi3, kpi4 = st.columns(4, gap="small")
with kpi1:
    metric_card("조회 데이터", f"{len(view):,}", "건", f"조회 기간 {(end - start).days + 1:,}일", BLUE)
with kpi2:
    metric_card("AI 확인후보", f"{len(candidates):,}", "건", f"조회 데이터의 {candidate_rate:.1f}%", RED)
with kpi3:
    metric_card("평균 온도", average_value, "℃", "선택 기간의 측정 온도 평균", TEAL)
with kpi4:
    metric_card("예측 오차 (MAE)", mae_value, "℃", f"실제·예측 {len(pred):,}건 비교", "#7085AB")

# 7. 세 개의 탭
with st.container(key="dashboard_tabs"):
    tab1, tab2, tab3 = st.tabs([
        "AI 점검 후보", "다음 1시간 온도 예측", "업무 검토 및 저장"
    ])

    with tab1:
        chart_col, summary_col = st.columns([2.2, 1], gap="medium")

        with chart_col:
            with st.container(border=True):
                st.markdown("#### 온도 추이")
                st.caption("파란 선은 측정 온도, 빨간 점은 AI 확인후보입니다.")
                if view["온도_C"].notna().any():
                    fig = px.line(view, x="측정시각", y="온도_C")
                    fig.update_traces(
                        name="측정 온도", showlegend=True,
                        line=dict(color=BLUE, width=2.5),
                        mode="lines+markers" if view["온도_C"].notna().sum() == 1 else "lines",
                    )
                    fig.add_scatter(
                        x=candidates["측정시각"], y=candidates["온도_C"],
                        mode="markers", name="AI 확인후보",
                        marker=dict(color=RED, size=9, line=dict(color="white", width=1.5)),
                    )
                    st.plotly_chart(style_line_chart(fig), width="stretch", theme=None,
                                    config={"displaylogo": False})
                else:
                    st.info("표시할 온도 측정값이 없습니다.")

        with summary_col:
            with st.container(border=True):
                st.markdown("#### AI 결과 분포")
                st.caption("선택한 조회 데이터의 분류 결과")
                counts = (
                    view["AI결과"].fillna("미분류").value_counts()
                    .rename_axis("AI결과").reset_index(name="건수")
                )
                donut = px.pie(
                    counts, names="AI결과", values="건수", color="AI결과",
                    hole=0.75, color_discrete_map={"확인후보": RED},
                    color_discrete_sequence=[BLUE, TEAL, "#A7B6CE"],
                )
                donut.update_traces(textinfo="none", marker=dict(line=dict(color="white", width=3)))
                donut.update_layout(
                    height=255, margin=dict(l=8, r=8, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#75839A", family="Arial, Malgun Gothic, sans-serif"),
                    legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.08),
                    annotations=[dict(
                        text=f"<b>{candidate_rate:.1f}%</b><br>확인후보 비율",
                        x=0.5, y=0.5, showarrow=False, font=dict(size=17, color="#75839A"),
                    )],
                )
                st.plotly_chart(donut, width="stretch", theme=None, config={"displayModeBar": False})
                st.dataframe(counts, hide_index=True, width="stretch", height=115)

        st.markdown("#### 점검 후보 상세")
        if candidates.empty:
            st.info("선택한 조회 조건에서 AI 확인후보가 없습니다.")
        else:
            show_table(candidates)

    with tab2:
        with st.container(border=True):
            st.markdown("#### 실제 온도와 AI 예측 온도")
            st.caption(f"실제·예측 {len(pred):,}건 비교 · 평균 절대 오차(MAE): {mae_text}")
            comparison = pred.dropna(subset=["목표시각"]).sort_values("목표시각")
            if pred.empty:
                st.info("실제 다음 온도와 AI 예측 온도가 모두 있는 자료가 없습니다.")
            elif comparison.empty:
                st.info("목표 시각이 없어 비교 차트를 표시할 수 없습니다.")
            else:
                fig2 = px.line(comparison, x="목표시각", y=["다음온도_C", "AI예측온도_C"])
                fig2.update_traces(
                    selector=dict(name="다음온도_C"), name="실제 온도",
                    line=dict(color=BLUE, width=2.5),
                )
                fig2.update_traces(
                    selector=dict(name="AI예측온도_C"), name="AI 예측 온도",
                    line=dict(color=TEAL, width=2.5, dash="dash"),
                )
                if len(comparison) == 1:
                    fig2.update_traces(mode="lines+markers")
                st.plotly_chart(style_line_chart(fig2, height=400), width="stretch",
                                theme=None, config={"displaylogo": False})
            st.caption("MAE는 실제 온도와 예측 온도 차이의 절댓값을 평균낸 값입니다. 단위는 ℃입니다.")
        with st.expander("예측 비교 데이터 보기"):
            show_table(pred)

    with tab3:
        note_col, report_col = st.columns(2, gap="medium")
        with note_col:
            with st.container(border=True):
                st.markdown("#### 업무 메모")
                st.caption("확인할 사항과 후속 조치 의견을 작성하세요.")
                note = st.text_area(
                    "확인할 사항 및 조치 제안",
                    "센서 상태와 운전 조건을 확인한 후 담당자 검토가 필요합니다.",
                    height=230, key=f"rail_note_{equipment}",
                )

        report = f"""설비: {equipment}
조회 기간: {start} ~ {end}
조회 건수: {len(view):,}건
AI 확인후보: {len(candidates):,}건 ({candidate_rate:.1f}%)
온도 예측 MAE: {mae_text} ({len(pred):,}건 비교)
업무 메모: {note}
교육용 가상 자료이며, 확인후보는 고장 확정이 아닙니다."""

        with report_col:
            with st.container(border=True):
                st.markdown("#### 보고서 미리보기")
                st.caption("현재 조회 조건과 업무 메모가 반영됩니다.")
                st.markdown(f'<div class="rail-report">{escape(report)}</div>',
                            unsafe_allow_html=True)

        with st.container(key="downloads"):
            st.caption("현재 조회 결과를 파일로 내려받기")
            csv_col, candidates_col, report_download_col = st.columns(3)
            with csv_col:
                st.download_button(
                    "조회 결과 CSV", view.to_csv(index=False).encode("utf-8-sig"),
                    "dashboard_result.csv", mime="text/csv", width="stretch",
                )
            with candidates_col:
                st.download_button(
                    "점검 후보 CSV", candidates.to_csv(index=False).encode("utf-8-sig"),
                    "inspection_candidates.csv", mime="text/csv", width="stretch",
                )
            with report_download_col:
                st.download_button(
                    "보고서 TXT", report.encode("utf-8-sig"),
                    "dashboard_report.txt", mime="text/plain", width="stretch",
                )

# 전체 조회표는 필요한 때 펼쳐서 확인
with st.expander(f"전체 조회 데이터 보기 · {len(view):,}건"):
    show_table(view, height=350)

