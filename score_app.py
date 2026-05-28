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
    "李星呈": "五年級", "魏靖芸": "五年級", "杜祤安": "五年級", "蕭楷翰": "五年級",
    "許睿恆": "五年級", "陳靚恩": "五年級", "汪靖荃": "五年級", "王子齊": "五年級",
    "許小樂": "五年級", "吳苡安": "五年級",
}

GRADE_ORDER = {"一年級": 1, "二年級": 2, "三年級": 3, "四年級": 4, "五年級": 5, "六年級": 6, "未知名級": 7}

sorted_students_info = sorted(STUDENT_LIST.items(), key=lambda x: (GRADE_ORDER.get(x[1], 99), x[0]))
name_list_by_grade = [f"[{grade}] {name}" for name, grade in sorted_students_info]
# ================================================================

# 載入資料
if os.path.exists(DB_FILE):
    try:
        df = pd.read_csv(DB_FILE)
    except:
        df = pd.DataFrame(columns=["日期", "姓名", "年級", "科目", "分數", "備註"])
else:
    df = pd.DataFrame(columns=["日期", "姓名", "年級", "科目", "分數", "備註"])

# --- 側邊欄導覽選單 ---
st.sidebar.title("📈 成績後台管理")
if has_logo:
    st.sidebar.image(LOGO_IMAGE, use_container_width=True)

page = st.sidebar.radio("請選擇功能：", ["📝 登記學生成績", "📊 成績分析與進步追蹤", "⚙️ 管理歷史成績"])

# 確保日期與分數格式正確
if not df.empty:
    df["日期"] = pd.to_datetime(df["日期"], format='mixed')
    df["分數"] = pd.to_numeric(df["分數"])

# ==================== 頁面 1：登記成績 ====================
if page == "📝 登記學生成績":
    st.title("📝 學生成績登記系統")
    st.write("請在下方輸入測驗成績資訊：")
    
    # 自動鎖定上次填寫的日期、科目與備註，方便連續填寫
    if "last_score_date" not in st.session_state: st.session_state["last_score_date"] = datetime.now()
    if "last_subject" not in st.session_state: st.session_state["last_subject"] = "數學"
    if "last_score_note" not in st.session_state: st.session_state["last_score_note"] = ""

    date = st.date_input("選擇測驗日期", st.session_state["last_score_date"])
    selected_display = st.selectbox("選擇學生姓名（依年級排序）", ["請選擇學生..."] + name_list_by_grade)
    
    subject = st.selectbox("選擇測驗科目", ["數學", "國文", "英文", "自然", "社會", "其他"], index=["數學", "國文", "英文", "自然", "社會", "其他"].index(st.session_state["last_subject"]))
    score = st.number_input("測驗分數", min_value=0, max_value=100, step=1, value=100)
    note = st.text_input("備註說明（例如：第三次單元測驗、期中考）", st.session_state["last_score_note"])
    
    submit = st.button("🚀 送出分數")

    if submit:
        if selected_display == "請選擇學生...":
            st.error("❌ 請先選擇一位學生！")
        else:
            st.session_state["last_score_date"] = date
            st.session_state["last_subject"] = subject
            st.session_state["last_score_note"] = note
            
            pure_name = selected_display.split("] ")[1]
            grade = STUDENT_LIST.get(pure_name, "未知名級")
            
            new_data = pd.DataFrame([[date.strftime("%Y-%m-%d"), pure_name, grade, subject, score, note]], columns=["日期", "姓名", "年級", "科目", "分數", "備註"])
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.success(f"✅ 已成功記錄：【{grade}】{pure_name} - {subject}：{score} 分！")
            st.rerun()

# ==================== 頁面 2：成績分析與進步追蹤 ====================
elif page == "📊 成績分析與進步追蹤":
    st.title("📊 成績分析與進步追蹤")
    if not df.empty:
        # 按時間排序，方便計算最新進步
        df_sorted_time = df.sort_values(by="日期")
        
        # 💡 核心邏輯：計算每位學生在該科目的「上一次分數」與「最新分數」的差額
        latest_records = []
        for (name, sub), sub_df in df_sorted_time.groupby(["姓名", "科目"]):
            if len(sub_df) >= 1:
                latest_row = sub_df.iloc[-1]  # 最新一筆
                prev_score = sub_df.iloc[-2]["分數"] if len(sub_df) >= 2 else None  # 上一次分數
                
                grade = STUDENT_LIST.get(name, "未知名級")
                current_score = latest_row["分數"]
                
                if prev_score is not None:
                    diff = current_score - prev_score
                    diff_str = f"📈 +{diff} 分" if diff > 0 else (f"📉 {diff} 分" if diff < 0 else "➡️ 持平")
                else:
                    diff_str = "🆕 首次登記"
                    
                latest_records.append({
                    "年級": grade, "姓名": name, "科目": sub, 
                    "最新測驗日期": latest_row["日期"].strftime("%Y-%m-%d"),
                    "最新分數": current_score, 
                    "上一次分數": prev_score if prev_score is not None else "-", 
                    "進步幅度": diff_str
                })
        
        progress_df = pd.DataFrame(latest_records)
        progress_df["年級權重"] = progress_df["年級"].map(GRADE_ORDER)
        progress_df = progress_df.sort_values(by=["年級權重", "姓名", "科目"]).drop(columns=["年級權重"])
        
        st.subheader("🎯 每位學生最新成績與進步追蹤")
        st.write("*(進步幅度會自動比對該生該科目上一次的成績)*")
        st.dataframe(progress_df, use_container_width=True)
        
        # 平均分統計
        st.markdown("---")
        st.subheader("👥 學生各科平均分數")
        avg_summary = df.groupby(["年級", "姓名", "科目"])["分數"].mean().round(1).reset_index()
        avg_summary["年級權重"] = avg_summary["年級"].map(GRADE_ORDER)
        avg_summary = avg_summary.sort_values(by=["年級權重", "姓名", "科目"]).drop(columns=["年級權重"])
        st.dataframe(avg_summary, use_container_width=True)
        
        # Excel 下載
        st.markdown("---")
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
        
        record_options = [f"編號 {i}: {row['日期']} - [{row['年級']}] {row['姓名']} ({row['科目']}: {row['分數']}分) [{row['備註'] if pd.notna(row['備註']) else ''}]" for i, row in display_df.iterrows()]
        selected_option = st.selectbox("請選擇一筆您想要修改或刪除的成績：", record_options)
        
        if selected_option:
            selected_index = int(selected_option.split(": ")[0].replace("編號 ", ""))
            current_row = df.loc[selected_index]
            
            st.markdown("---")
            action = st.radio("您想要對這筆紀錄做什麼？", ["修改此筆成績", "刪除此筆成績"])
            
            if action == "修改此筆成績":
                st.subheader("✏️ 修改資料內容")
                edit_date = st.date_input("修改日期", pd.to_datetime(current_row["日期"]))
                
                current_display_name = f"[{current_row['年級']}] {current_row['姓名']}"
                default_idx = name_list_by_grade.index(current_display_name) + 1 if current_display_name in name_list_by_grade else 0
                edit_selected = st.selectbox("修改姓名", ["請選擇學生..."] + name_list_by_grade, index=default_idx)
                
                edit_sub = st.selectbox("修改科目", ["數學", "國文", "英文", "自然", "社會", "其他"], index=["數學", "國文", "英文", "自然", "社會", "其他"].index(current_row["科目"]))
                edit_price = st.number_input("修改分數", min_value=0, max_value=100, value=int(current_row["分數"]), step=1)
                edit_note = st.text_input("修改備註", str(current_row["備註"]) if pd.notna(current_row["備註"]) else "")
                
                if st.button("💾 儲存修改"):
                    if edit_selected == "請選擇學生...":
                        st.error("❌ 請選擇學生姓名！")
                    else:
                        pure_edit_name = edit_selected.split("] ")[1]
                        df.at[selected_index, "日期"] = pd.to_datetime(edit_date)
                        df.at[selected_index, "姓名"] = pure_edit_name
                        df.at[selected_index, "年級"] = STUDENT_LIST.get(pure_edit_name, "未知名級")
                        df.at[selected_index, "科目"] = edit_sub
                        df.at[selected_index, "分數"] = edit_price
                        df.at[selected_index, "備註"] = edit_note
                        df.to_csv(DB_FILE, index=False)
                        st.success("成績修改成功！")
                        st.rerun()
                    
            elif action == "刪除此筆成績":
                st.subheader("🔴 刪除資料確認")
                st.warning(f"您確定要刪除這筆成績嗎？\n\n【 {current_row['日期'].strftime('%Y-%m-%d')} - {current_row['姓名']} : {current_row['科目']} {current_row['分數']}分 】")
                if st.button("❌ 確認刪除，無法復原"):
                    df = df.drop(selected_index).reset_index(drop=True)
                    df.to_csv(DB_FILE, index=False)
                    st.success("成績已成功刪除！")
                    st.rerun()
    else:
        st.info("目前沒有任何歷史紀錄可以修改或刪除。")
