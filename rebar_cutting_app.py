import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import os
import textwrap

# ==========================================
# 1. CUTTING OPTIMIZER FUNCTIONS
# ==========================================
def solve_rebar_cutting(stock_length, demands):
    sorted_demands = sorted(demands, reverse=True)
    bins = [] 
    for demand in sorted_demands:
        placed = False
        for b in bins:
            if b['waste'] >= demand:
                b['cuts'].append(demand)
                b['waste'] -= demand
                placed = True
                break
        if not placed:
            bins.append({'bar_id': len(bins) + 1, 'cuts': [demand], 'waste': stock_length - demand})
    return len(bins), bins

def generate_optimizer_pdf(all_results, stock_length, unit):
    # PDF သည် Font Error မဖြစ်စေရန် အင်္ဂလိပ်စာသားများကိုသာ အသုံးပြု၍ ထုတ်ပေးပါမည်
    pdf = FPDF()
    for code, data in all_results.items():
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, txt="Construction Material Cutting Optimizer Report", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 8, txt=f"Material Type: {code}", ln=True)
        pdf.cell(190, 8, txt=f"Standard Stock Dimension: {stock_length} {unit}", ln=True)
        pdf.cell(190, 8, txt=f"Total Quantity Required: {data['total_bars']}", ln=True)
        pdf.cell(190, 8, txt=f"Total Waste: {data['total_waste']:.3f} {unit}", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, txt="1. Cutting Plan Details", ln=True)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(20, 10, txt="No.", border=1, align='C')
        pdf.cell(100, 10, txt="Cuts Dimension", border=1, align='C')
        pdf.cell(70, 10, txt=f"Waste", border=1, align='C', ln=True)

        pdf.set_font("Arial", size=10)
        for item in data['cutting_plan']:
            bar_id = str(item['bar_id'])
            cuts = str(item['cuts'])
            w_rounded = round(item['raw_waste'], 3)
            if w_rounded > 0:
                waste_txt = f"{w_rounded} {unit}"
                if "(Code:" in item['waste']:
                    code_part = item['waste'].split("(Code: ")[1].replace(")", "")
                    waste_txt += f" (Code: {code_part})"
            else:
                waste_txt = f"0 {unit} (No Waste)"

            wrapped_lines = textwrap.wrap(cuts, width=50)
            if not wrapped_lines: wrapped_lines = [""]
            for i, line in enumerate(wrapped_lines):
                c_bar_id = bar_id if i == 0 else ""
                c_waste = waste_txt if i == 0 else ""
                if len(wrapped_lines) == 1: border_style = 1
                elif i == 0: border_style = 'LTR'
                elif i == len(wrapped_lines) - 1: border_style = 'LBR'
                else: border_style = 'LR'
                pdf.cell(20, 8, txt=c_bar_id, border=border_style, align='C')
                pdf.cell(100, 8, txt=line, border=border_style)
                pdf.cell(70, 8, txt=c_waste, border=border_style, ln=True)

        pdf.ln(10)
        if data['waste_summary_data']:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(190, 10, txt="2. Waste Recovery Summary", ln=True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(60, 10, txt="Waste Code", border=1, align='C')
            pdf.cell(60, 10, txt=f"Dimension ({unit})", border=1, align='C')
            pdf.cell(60, 10, txt="Quantity", border=1, align='C', ln=True)
            pdf.set_font("Arial", size=10)
            for w_len, info in data['waste_summary_data'].items():
                pdf.cell(60, 10, txt=f"{code}-{info['code']}", border=1, align='C')
                pdf.cell(60, 10, txt=str(w_len), border=1, align='C')
                pdf.cell(60, 10, txt=str(info['qty']), border=1, align='C', ln=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f: pdf_bytes = f.read()
    os.remove(tmp.name)
    return pdf_bytes

# ==========================================
# 2. APP LAYOUT & LANGUAGE CONTROL
# ==========================================
st.set_page_config(page_title="Material Optimizer", layout="wide")

# Sidebar - Language Selection
st.sidebar.title("⚙️ Settings")
lang = st.sidebar.radio("Language / ဘာသာစကား", ["မြန်မာ", "English"])

# Translation Dictionary
if lang == "မြန်မာ":
    t = {
        "title": "ဆောက်လုပ်ရေးသုံးပစ္စည်း ဖြတ်တောက်မှု တွက်ချက်ရန်",
        "desc": "ဆောက်လုပ်ရေးသုံး ပစ္စည်းများ (သံချောင်း၊ ပိုက်၊ သစ်သား စသည်) ဖြတ်တောက်မှုကို အလေအလွင့် အနည်းဆုံးဖြစ်အောင် တွက်ချက်ပေးသော Application ဖြစ်ပါသည်။",
        "input_header": "၁။ Data ထည့်သွင်းရန်",
        "unit": "ယူနစ်",
        "stock_len": "မူလပစ္စည်း အတိုင်းအတာ",
        "info": "အောက်ပါဇယားတွင် ပစ္စည်းအမျိုးအစား၊ အတိုင်းအတာ နှင့် ပမာဏတို့ကို ရိုက်ထည့်ပါ။",
        "mat_name": "ပစ္စည်းအမျိုးအစား",
        "len": "အတိုင်းအတာ",
        "qty": "ပမာဏ",
        "calc_btn": "✂️ တွက်ချက်မည်",
        "res_header": "၂။ တွက်ချက်မှု ရလဒ်များ",
        "warn_empty": "ကျေးဇူးပြု၍ Data များကို မှန်ကန်စွာ ထည့်သွင်းပါ။",
        "calc_spin": "အကောင်းဆုံးရလဒ်များကို တွက်ချက်နေပါသည်...",
        "err_exceed_1": "❌ [",
        "err_exceed_2": "] တွင် လိုအပ်သော အတိုင်းအတာသည် မူလပစ္စည်းအတိုင်းအတာထက် ကြီးနေပါသည်။",
        "no_waste": "အလေအလွင့်မရှိ",
        "tot_req_1": "✅ ",
        "tot_req_2": " အတွက် စုစုပေါင်း အသုံးပြုမည့် ပမာဏ: ",
        "col_no": "စဉ်",
        "col_cuts": "ဖြတ်တောက်မည့် အတိုင်းအတာများ",
        "col_waste": "အလေအလွင့်",
        "tot_waste_1": "💡 ",
        "tot_waste_2": " ၏ စုစုပေါင်း အလေအလွင့်: ",
        "waste_sum": "♻️ အလေအလွင့် စာရင်း",
        "dl_btn": "📥 PDF Report ဆွဲယူရန်"
    }
else:
    t = {
        "title": "Construction Material Cutting Optimizer",
        "desc": "This application optimizes the cutting of construction materials to minimize waste.",
        "input_header": "1. Input Data",
        "unit": "Unit",
        "stock_len": "Stock Dimension",
        "info": "Enter the material type, dimension, and quantity in the table below.",
        "mat_name": "Material Type",
        "len": "Dimension",
        "qty": "Quantity",
        "calc_btn": "✂️ Calculate / Optimize",
        "res_header": "2. Results",
        "warn_empty": "Please enter valid data.",
        "calc_spin": "Calculating optimized results...",
        "err_exceed_1": "❌ [",
        "err_exceed_2": "] required dimension exceeds stock dimension.",
        "no_waste": "No Waste",
        "tot_req_1": "✅ Total quantity required for ",
        "tot_req_2": ": ",
        "col_no": "No.",
        "col_cuts": "Cuts Dimension",
        "col_waste": "Waste",
        "tot_waste_1": "💡 Total Waste for ",
        "tot_waste_2": ": ",
        "waste_sum": "♻️ Waste Summary",
        "dl_btn": "📥 Download PDF Report"
    }

# Custom Title with Rotated Scissors Emoji (-90 degree)
st.markdown(
    f'''
    <h1 style="display: flex; align-items: center; gap: 10px;">
        <span style="display: inline-block; transform: rotate(-90deg);">✂️</span> 
        {t["title"]}
    </h1>
    ''', 
    unsafe_allow_html=True
)
st.write(t["desc"])

col1, col2 = st.columns([1, 1.5])
with col1:
    st.header(t["input_header"])
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        unit = st.selectbox(t["unit"], ["m", "ft", "mm", "in"])
    with row1_col2:
        stock_length = st.number_input(f"{t['stock_len']} ({unit})", min_value=1.0, value=12.0 if unit=='m' else 40.0, step=1.0)
    
    st.info(t["info"])
    
    if 'input_df' not in st.session_state:
        st.session_state['input_df'] = pd.DataFrame({
            "Material Type": ["16mm", "16mm", "12mm", "10mm"],
            "Dimension": [7.0, 5.0, 4.0, 3.5],
            "Quantity": [1, 2, 5, 10]
        })

    # Display Dataframe with mapped column names dynamically based on selected language
    display_df = st.session_state['input_df'].copy()
    display_df.columns = [t["mat_name"], f"{t['len']} ({unit})", t["qty"]]
    
    edited_df = st.data_editor(display_df, num_rows="dynamic", use_container_width=True)
    optimize_btn = st.button(t["calc_btn"], type="primary")

with col2:
    st.header(t["res_header"])
    if optimize_btn:
        valid_df = edited_df.dropna()
        valid_df = valid_df[valid_df.iloc[:, 0].astype(str).str.strip() != '']
        
        if valid_df.empty:
            st.warning(t["warn_empty"])
            st.session_state['optimized'] = False
        else:
            # Sync back internal state
            st.session_state['input_df'] = pd.DataFrame({
                "Material Type": valid_df.iloc[:, 0],
                "Dimension": valid_df.iloc[:, 1],
                "Quantity": valid_df.iloc[:, 2]
            })
            
            all_results, has_error = {}, False
            with st.spinner(t["calc_spin"]):
                grouped = valid_df.groupby(valid_df.columns[0])
                for code, group in grouped:
                    code = str(code).strip()
                    demands_list = []
                    for _, row in group.iterrows():
                        try:
                            length = float(row.iloc[1])
                            qty = int(float(row.iloc[2]))
                        except:
                            continue
                        if length > 0 and qty > 0: demands_list.extend([length] * qty)
                    if not demands_list: continue
                    if any(d > stock_length for d in demands_list):
                        st.error(f"{t['err_exceed_1']}{code}{t['err_exceed_2']}")
                        has_error = True; break
                    
                    SCALE = 1000 
                    scaled_stock = int(float(stock_length) * SCALE)
                    scaled_demands = [int(float(d) * SCALE) for d in demands_list]
                    total_bars, scaled_cutting_plan = solve_rebar_cutting(scaled_stock, scaled_demands)
                    
                    unique_wastes, waste_counter = {}, 1
                    for plan in scaled_cutting_plan:
                        w_rounded = round(plan['waste'] / SCALE, 3)
                        if w_rounded > 0 and w_rounded not in unique_wastes:
                            unique_wastes[w_rounded] = f"W{waste_counter}"
                            waste_counter += 1
                    
                    waste_summary_data = {w: {'code': c, 'qty': 0} for w, c in unique_wastes.items()}
                    cutting_plan = []
                    for plan in scaled_cutting_plan:
                        orig_cuts = [c / SCALE for c in plan['cuts']]
                        w_rounded = round(plan['waste'] / SCALE, 3)
                        cuts_str = " + ".join([f"{c} {unit}" for c in orig_cuts])
                        if w_rounded > 0:
                            waste_str = f"{w_rounded} {unit} (Code: {code}-{unique_wastes[w_rounded]})"
                            waste_summary_data[w_rounded]['qty'] += 1 
                        else: waste_str = f"0 {unit} ({t['no_waste']})"
                        cutting_plan.append({'bar_id': plan['bar_id'], 'cuts': cuts_str, 'waste': waste_str, 'raw_waste': plan['waste'] / SCALE})
                    
                    all_results[code] = {
                        'total_bars': total_bars, 'cutting_plan': cutting_plan,
                        'waste_summary_data': waste_summary_data, 'total_waste': sum(item['raw_waste'] for item in cutting_plan)
                    }
                
            if not has_error and all_results:
                st.session_state.update({'all_results': all_results, 'stock_length': stock_length, 'unit': unit, 'optimized': True})
            else: st.session_state['optimized'] = False

    if st.session_state.get('optimized', False):
        all_results, unit, stock_length = st.session_state['all_results'], st.session_state['unit'], st.session_state['stock_length']
        tabs = st.tabs(list(all_results.keys()))
        for idx, (code, data) in enumerate(all_results.items()):
            with tabs[idx]:
                st.success(f"{t['tot_req_1']}**{code}**{t['tot_req_2']}**{data['total_bars']}**")
                display_df = pd.DataFrame(data['cutting_plan'])[['bar_id', 'cuts', 'waste']]
                display_df.columns = [t['col_no'], t['col_cuts'], t['col_waste']]
                st.table(display_df)
                st.info(f"{t['tot_waste_1']}**{code}**{t['tot_waste_2']}**{data['total_waste']:.3f} {unit}**")
                if data['waste_summary_data']:
                    st.divider() 
                    st.subheader(f"{t['waste_sum']} ({code})")
                    summary_list = [{t['mat_name']: f"{code}-{info['code']}", f"{t['len']} ({unit})": w_len, t['qty']: info['qty']} for w_len, info in data['waste_summary_data'].items()]
                    st.dataframe(pd.DataFrame(summary_list).sort_values(by=f"{t['len']} ({unit})", ascending=False), hide_index=True, use_container_width=True)

        st.divider()
        pdf_bytes = generate_optimizer_pdf(all_results, stock_length, unit)
        st.download_button(
            label=t["dl_btn"],
            data=pdf_bytes,
            file_name="Material_Cutting_Report.pdf",
            mime="application/pdf",
            type="primary"
        )