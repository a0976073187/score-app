import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# ==================== 🎨 網頁 Logo 與主題設定 ====================
LOGO_IMAGE = "logo.png"  # 如果有放 Fun Learning 圖片在同資料夾，會自動讀取
has_logo = os.path.exists(LOGO_IMAGE)

st.set_page_config(
    page_title="學生成績登記與追蹤系統",
    page_icon="📈",
    layout="centered"
)
# ================================================================

# 設定成績資料儲存檔案名稱
DB_FILE = "score_records.csv"

# ==================== 🎒 學生名單與年級設定區 ====================
STUDENT_LIST = {
    "李星呈": "五年級", 
    "魏靖芸": "五年級", 
    "杜祤安": "五年級", 
    "蕭楷翰": "五年級",
    "許睿恆": "五年級", 
    "陳靚恩": "五年級", 
    "汪靖荃": "五年級", 
    "王子齊": "五年級",
    "許小樂": "五年級", 
    "吳苡安": "五年級"
}

GRADE_ORDER = {"一年級": 1, "二年級": 2, "三年級": 3, "四年級": 4, "五年級": 5, "六年級": 6, "未知名級": 7}

sorted_students_info = sorted(STUDENT_LIST.items(), key=lambda x: (GRADE_ORDER.get(x, 99), x))
name_list_by_grade = [f"[{grade}] {name}" for name, grade in sorted_students_info]
# ================================================================

# 載入資料
if os.path.exists(DB_FILE):
    try:
        df = pd.read_csv(DB_FILE)
    except:
        df = pd.DataFrame(columns=["日期", "姓名", "年級", "考試類型", "科目", "分數", "備註"])
else:
    df = pd.DataFrame(columns=["日期", "姓名", "年級", "考試類型", "科目", "分數", "備註"])

# --- 側邊欄導覽選單 ---
st.sidebar.title("📈 成績後台管理")
if has_logo:
    st.sidebar.image(LOGO_IMAGE, use_container_width=True)

page = st.sidebar.radio("請選擇功能：", ["📝 登記學生成績", "📊 成績分析與趨勢圖表", "⚙️ 管理歷史成績"])

# 確保資料格式正確
if not df.empty:
    df["日期"] = pd.to_datetime(df["日期"], format='mixed')
    df["分數"] = pd.to_numeric(df["分數"])
    if "考試類型" not in df.columns:
        df["考試類型"] = "未分類"

# ==================== 頁面 1：登記成績 ====================
if page == "📝 登記學生成績":
    st.title("📝 學生成績登記系統")
    st.write("請在下方輸入測驗成績資訊：")
    
    if "last_score_date" not in st.session_state: st.session_state["last_score_date"] = datetime.now()
    if "last_exam_type" not in st.session_state: st.session_state["last_exam_type"] = "平時考"
    if "last_subject" not in st.session_state: st.session_state["last_subject"] = "數學"
    if "last_score_note" not in st.session_state: st.session_state["last_score_note"] = ""

    date = st.date_input("選擇測驗日期", st.session_state["last_score_date"])
    selected_display = st.selectbox("選擇學生姓名", ["請選擇學生..."] + name_list_by_grade)
    
    exam_types = ["平時考", "月考", "期中考", "期末考", "模擬考", "其他"]
    exam_type = st.selectbox("選擇考試類型", exam_types, index=exam_types.index(st.session_state["last_exam_type"]))
    
    subject = st.selectbox("選擇測驗科目", ["數學", "國文", "英文", "自然", "社會", "其他"], index=["數學", "國文", "英文", "自然", "社會", "其他"].index(st.session_state["last_subject"]))
    score = st.number_input("測驗分數", min_value=0, max_value=100, step=1, value=100)
    note = st.text_input("備註說明（例如：第三次單元測驗、期中考）", st.session_state["last_score_note"])
    
    submit = st.button("🚀 送出分數")

    if submit:
        if selected_display == "請選擇學生...":
            st.error("❌ 請先選擇一位學生！")
        else:
            st.session_state["last_score_date"] = date
            st.session_state["last_exam_type"] = exam_type
            st.session_state["last_subject"] = subject
            st.session_state["last_score_note"] = note
            
            pure_name = selected_display.split("] ")[1]
            grade = STUDENT_LIST.get(pure_name, "未知名級")
            
            new_data = pd.DataFrame([[date.strftime("%Y-%m-%d"), pure_name, grade, exam_type, subject, score, note]], columns=["日期", "姓名", "年級", "考試類型", "科目", "分數", "備註"])
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.success(f"✅ 已成功記錄：【{grade}】{pure_name} - {exam_type}({subject})：{score} 分！")
            st.rerun()

# ==================== 頁面 2：成績分析與趨勢圖表 ====================
elif page == "📊 成績分析與趨勢圖表":
    st.title("📊 成績分析與趨勢圖表")
    if not df.empty:
        
        st.subheader("📉 個人成績進步趨勢圖")
        st.write("您可以選擇特定學生與科目，系統會畫出歷史分數變化折線圖：")
        
        col1, col2 = st.columns(2)
        with col1:
            pure_students = sorted(list(STUDENT_LIST.keys()))
            search_name = st.selectbox("🔍 選擇查詢學生", pure_students)
        with col2:
            search_subject = st.selectbox("📚 選擇查詢科目", ["數學", "國文", "英文", "自然", "社會", "開他"])
            
        chart_df = df[(df["姓名"] == search_name) & (df["科目"] == search_subject)].sort_values(by="日期")
        
        if not chart_df.empty:
            plot_data = chart_df.copy()
            plot_data["測驗識別"] = plot_data["日期"].dt.strftime("%m/%d") + " " + plot_data["考試類型"]
            
            st.line_chart(
                data=plot_data,
                x="測驗識別",
                y="分數",
                use_container_width=True
            )
        else:
            st.info(f"💡 目前還沒有 {search_name} 在 {search_subject} 科目的歷史分數數據，無法繪製折線圖。")
            
        st.markdown("---")
        
        st.subheader("🎯 最新成績與進步追蹤")
        df_sorted_time = df.sort_values(by="日期")
        latest_records = []
        for (name, sub), sub_df in df_sorted_time.groupby(["姓名", "科目"]):
            if name not in STUDENT_LIST:
                continue
            if len(sub_df) >= 1:
                latest_row = sub_df.iloc[-1]
                prev_score = sub_df.iloc[-2]["分數"] if len(sub_df) >= 2 else None
                grade = STUDENT_LIST.get(name, "未知名級")
                current_score = latest_row["分數"]
                
                if prev_score is not None:
                    diff = current_score - prev_score
                    diff_str = f"🔺 +{diff} 分" if diff > 0 else (f"🔻 {diff} 分" if diff < 0 else "➡️ 持平")
                else:
                    diff_str = "🆕 首次登記"
                    
                latest_records.append({
                    "年級": grade, "姓名": name, "考試類型": latest_row["考試類型"], "科目": sub, 
                    "最新測驗日期": latest_row["日期"].strftime("%Y-%m-%d"),
                    "最新分數": current_score, 
                    "上一次分數": prev_score if prev_score is not None else "-", 
                    "進步幅度": diff_str
                })
        
        if latest_records:
            progress_df = pd.DataFrame(latest_records)
            progress_df["年級權重"] = progress_df["年級"].map(GRADE_ORDER)
            progress_df = progress_df.sort_values(by=["年級權重", "姓名", "科目"]).drop(columns=["年級權重"])
            st.dataframe(progress_df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("👥 學生各科歷史平均分數")
        avg_summary = df[df["姓名"].isin(STUDENT_LIST.keys())].groupby(["年級", "姓名", "科目"])["分數"].mean().round(1).reset_index()
        if not avg_summary.empty:
            avg_summary["年級權重"] = avg_summary["年級"].map(GRADE_ORDER)
            avg_summary = avg_summary.sort_values(by=["年級權重", "姓名", "科目"]).drop(columns=["年級權重"])
            st.dataframe(avg_summary, use_container_width=True)
        
        st.markdown("---")
        if latest_records and not avg_summary.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                progress_df.to_excel(writer, sheet_name='最新成績與進步追蹤', index=False)
                avg_summary.to_excel(writer, sheet_name='各科平均分數', index=False)
                
            st.download_button(
                label="📥 下載 Excel 成績總報表",
                data=buffer.getvalue(),
                file_name=f"學生成績追蹤表_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("目前還沒有任何成績紀錄，請先登記成績吧！")

# ==================== 頁面 3：管理歷史成績 ====================
elif page == "⚙️ 管理歷史成績":
    st.title("⚙️ 管理歷史成績（修改 / 刪除）")
    if not df.empty:
        display_df = df.copy()
        display_df["日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
        
        record_options = [f"編號 {i}: {row['日期']} - [{row['年級']}] {row['姓名']} ({row['考試類型']}-{row['科目']}: {row['分數']}分)" for i, row in display_df.iterrows()]
        selected_option = st.selectbox("請選擇一筆您想要修改或刪除的成績：", record_options)
        
        if selected_option:
            # 💡 關鍵修復點：精確拆解字串，抓取第一個冒號前的編號數字
            selected_index = int(selected_option.split(":")[0].replace("編號 ", ""))
            current_row = df.loc[selected_index]
            
            st.markdown("---")
            action = st.radio("您想要對這筆紀錄做什麼？", ["修改此筆成績", "刪除此筆成績"])
            
            if action == "修改此筆成績":
                st.subheader("✏️ 修改資料內容")
                edit_date = st.date_input("修改日期", pd.to_datetime(current_row["日期"]))
                
                current_display_name = f"[{current_row['年級']}] {current_row['姓名']}"
                default_idx = name_list_by_grade.index(current_display_name) + 1 if current_display_name in name_list_by_grade else 0
                edit_selected = st.selectbox("修改姓名", ["請選擇學生..."] + name_list_by_grade, index=default_idx)
                
                exam_types = ["平時考", "月考", "期中考", "期末考", "模擬考", "其他"]
                default_exam_idx = exam_types.index(current_row["考試類型"]) if current_row["考試類型"] in exam_types else 0
                edit_exam_type = st.selectbox("修改考試類型", exam_types, index=default_exam_idx)
                
                edit_sub = st.selectbox("修改科目", ["數學", "國文", "英文", "自然", "社會", "其他"], index=["數學", "國文", "英文", "自然", "社會", "其他"].index(current_row["科目"]))
                edit_price = st.number_input("修改分數", min_value=0, max_value=100, value=int(current_row["分數"]), step=1)
                edit_note = st.text_input("修改備註", str(current_row["備註"]) if pd.notna(current_row["備註"]) else "")
                
                if st.button("💾 儲存修改"):
                    if edit_selected == "請選擇學生...":
                        st.error("❌ 請選擇學生姓名！")
                    else:
                        pure_edit_name = edit_selected.split("] ")[1]
                        df.at[selected_index, "日期"] = pd.to_datetime(edit_date)
