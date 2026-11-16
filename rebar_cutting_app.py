import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import os
import textwrap
import base64

# ------------------------------------------
# SVG ပုံကြမ်းများ (Base64) - BBS UI ဇယားအတွက်
# ------------------------------------------
SVG_COLOR = "#1e90ff"
TEXT_COLOR = "#ff4500"

SHAPE_SVG_STRINGS = {
    "Straight": f'<svg xmlns="http://www.w3.org/2000/svg" width="90" height="40"><line x1="10" y1="20" x2="80" y2="20" stroke="{SVG_COLOR}" stroke-width="3"/><text x="42" y="15" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">A</text></svg>',
    "L-Shape": f'<svg xmlns="http://www.w3.org/2000/svg" width="90" height="40"><polyline points="20,5 20,35 80,35" fill="none" stroke="{SVG_COLOR}" stroke-width="3"/><text x="5" y="20" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">B</text><text x="45" y="30" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">A</text></svg>',
    "U-Shape": f'<svg xmlns="http://www.w3.org/2000/svg" width="90" height="40"><polyline points="20,5 20,35 70,35 70,5" fill="none" stroke="{SVG_COLOR}" stroke-width="3"/><text x="5" y="20" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">A</text><text x="42" y="30" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">B</text><text x="75" y="20" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">C</text></svg>',
    "Stirrup (Rect)": f'<svg xmlns="http://www.w3.org/2000/svg" width="90" height="40"><rect x="25" y="10" width="40" height="20" fill="none" stroke="{SVG_COLOR}" stroke-width="3"/><path d="M 33 18 L 25 10 L 25 30 L 65 30 L 65 10 L 25 10 L 29 22" fill="none" stroke="{SVG_COLOR}" stroke-width="2"/><text x="42" y="8" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">A</text><text x="10" y="25" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">B</text></svg>',
    "Ring": f'<svg xmlns="http://www.w3.org/2000/svg" width="90" height="40"><circle cx="45" cy="20" r="15" fill="none" stroke="{SVG_COLOR}" stroke-width="3"/><text x="35" y="22" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">A</text></svg>',
    "Crank Bar": f'<svg xmlns="http://www.w3.org/2000/svg" width="90" height="40"><polyline points="5,30 30,30 50,10 85,10" fill="none" stroke="{SVG_COLOR}" stroke-width="3"/><text x="12" y="38" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">A</text><text x="35" y="25" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">B</text><text x="60" y="8" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">C</text></svg>',
    "Double Crank": f'<svg xmlns="http://www.w3.org/2000/svg" width="90" height="40"><polyline points="5,10 25,10 35,20 55,20 65,30 85,30" fill="none" stroke="{SVG_COLOR}" stroke-width="3"/><text x="12" y="8" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">A</text><text x="26" y="14" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">B</text><text x="42" y="18" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">C</text><text x="56" y="24" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">D</text><text x="72" y="28" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">E</text></svg>',
    "Bent Up/Down": f'<svg xmlns="http://www.w3.org/2000/svg" width="90" height="40"><polyline points="5,10 20,10 30,30 60,30 70,10 85,10" fill="none" stroke="{SVG_COLOR}" stroke-width="3"/><text x="10" y="8" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">A</text><text x="20" y="25" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">B</text><text x="42" y="38" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">C</text><text x="65" y="25" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">D</text><text x="75" y="8" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">E</text></svg>',
    "Chair": f'<svg xmlns="http://www.w3.org/2000/svg" width="90" height="40"><polyline points="5,35 20,35 20,10 70,10 70,35 85,35" fill="none" stroke="{SVG_COLOR}" stroke-width="3"/><text x="10" y="30" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">A</text><text x="8" y="22" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">B</text><text x="42" y="8" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">C</text><text x="75" y="22" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">D</text><text x="75" y="30" fill="{TEXT_COLOR}" font-size="10" font-family="Arial" font-weight="bold">E</text></svg>'
}

SHAPE_IMAGES = {k: "data:image/svg+xml;base64," + base64.b64encode(v.encode('utf-8')).decode('utf-8') for k, v in SHAPE_SVG_STRINGS.items()}

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
# 2. BBS CALCULATOR FUNCTIONS
# ==========================================
def calculate_bbs(df, unit):
    unit_factors = {"m": 1.0, "ft": 0.3048, "mm": 0.001, "in": 0.0254}
    to_m = unit_factors[unit]

    results = []
    for _, row in df.iterrows():
        def safe_float(val, default=0.0):
            try: return float(val)
            except: return default

        def safe_int(val, default=0):
            try: return int(float(val))
            except: return default

        mark = str(row.get("Bar Mark", ""))
        shape = str(row.get("Shape", "Straight"))

        dia = safe_float(row.get("Bar Size (mm)", 0))
        a = safe_float(row.get(f"A ({unit})", 0))
        b = safe_float(row.get(f"B ({unit})", 0))
        c = safe_float(row.get(f"C ({unit})", 0))
        d = safe_float(row.get(f"D ({unit})", 0))
        e = safe_float(row.get(f"E ({unit})", 0))

        hook_length = safe_float(row.get(f"Standard Hook ({unit})", 0))

        members = safe_int(row.get("No. of Members", 0))
        bars = safe_int(row.get("Bars per Member", 0))

        if shape == "Straight":
            cutting_len = a
        elif shape == "L-Shape":
            cutting_len = a + b
        elif shape == "U-Shape":
            cutting_len = a + b + c
        elif shape == "Stirrup (Rect)":
            cutting_len = 2 * (a + b)
        elif shape == "Ring":
            cutting_len = 3.1416 * a
        elif shape == "Crank Bar":
            cutting_len = a + c + (1.42 * b)
        elif shape == "Double Crank":
            cutting_len = a + c + e + (1.42 * b) + (1.42 * d)
        elif shape == "Bent Up/Down":
            cutting_len = a + c + e + (1.42 * b) + (1.42 * d)
        elif shape == "Chair":
            cutting_len = a + b + c + d + e
        else:
            cutting_len = a + b + c + d + e

        cutting_len = max(0, round(cutting_len + hook_length, 3))
        total_qty = members * bars

        total_length_in_unit = round(cutting_len * total_qty, 3)
        total_length_in_m = total_length_in_unit * to_m

        unit_weight = round((dia ** 2) / 162.2, 3)
        total_weight = round(total_length_in_m * unit_weight, 2)

        sketch = SHAPE_IMAGES.get(shape, "")

        if dia > 0 and (a > 0 or b > 0 or c > 0 or d > 0 or e > 0):
            results.append({
                "Bar Mark": mark,
                "Sketch": sketch,
                "Shape": shape,
                "Bar Size (mm)": dia,
                f"A ({unit})": a, f"B ({unit})": b, f"C ({unit})": c, f"D ({unit})": d, f"E ({unit})": e,
                f"Hook ({unit})": hook_length,
                "Qty": total_qty,
                f"Cut L ({unit})": cutting_len,
                f"Total L ({unit})": total_length_in_unit,
                "Total Wt (kg)": total_weight
            })

    return pd.DataFrame(results)

def generate_bbs_pdf(df_result, unit):
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(277, 10, txt="Bar Bending Schedule (BBS) Report", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 9)
    cols = [("Mark", 16), ("Shape", 22), ("Sketch", 36), ("Size", 10),
            (f"A", 12), (f"B", 12), (f"C", 12), (f"D", 12), (f"E", 12),
            ("Hook", 12), ("Qty", 10), (f"Cut L", 16), (f"Total L", 18), ("Wt(kg)", 20)]

    for col_name, width in cols:
        pdf.cell(width, 10, txt=col_name, border=1, align='C')
    pdf.ln()

    pdf.set_font("Arial", size=9)
    total_weight = 0
    for _, row in df_result.iterrows():
        shape_name = str(row["Shape"])
        row_height = 20

        pdf.cell(16, row_height, txt=str(row["Bar Mark"]), border=1, align='C')
        pdf.cell(22, row_height, txt=shape_name, border=1, align='C')

        x = pdf.get_x()
        y = pdf.get_y()
        pdf.cell(36, row_height, txt="", border=1, align='C')

        pdf.set_line_width(0.4)
        pdf.set_font("Arial", size=6)

        a_val, b_val, c_val, d_val, e_val = row[f"A ({unit})"], row[f"B ({unit})"], row[f"C ({unit})"], row[f"D ({unit})"], row[f"E ({unit})"]

        a_tbl = str(a_val) if a_val > 0 else ""
        b_tbl = str(b_val) if b_val > 0 else ""
        c_tbl = str(c_val) if c_val > 0 else ""
        d_tbl = str(d_val) if d_val > 0 else ""
        e_tbl = str(e_val) if e_val > 0 else ""

        if shape_name == "Straight":
            pdf.line(x+5, y+10, x+31, y+10)
            if a_val > 0: pdf.text(x+16, y+9, f"A={a_val}")
        elif shape_name == "L-Shape":
            pdf.line(x+10, y+4, x+10, y+16)
            pdf.line(x+10, y+16, x+31, y+16)
            if b_val > 0: pdf.text(x+2, y+11, f"B={b_val}")
            if a_val > 0: pdf.text(x+18, y+15, f"A={a_val}")
        elif shape_name == "U-Shape":
            pdf.line(x+10, y+4, x+10, y+16)
            pdf.line(x+10, y+16, x+26, y+16)
            pdf.line(x+26, y+16, x+26, y+4)
            if a_val > 0: pdf.text(x+2, y+11, f"A={a_val}")
            if b_val > 0: pdf.text(x+16, y+19, f"B={b_val}")
            if c_val > 0: pdf.text(x+28, y+11, f"C={c_val}")
        elif shape_name == "Stirrup (Rect)":
            pdf.rect(x+10, y+5, 16, 10)
            pdf.line(x+10, y+5, x+14, y+9)
            pdf.line(x+10, y+5, x+13, y+11)
            if a_val > 0: pdf.text(x+15, y+4, f"A={a_val}")
            if b_val > 0: pdf.text(x+2, y+11, f"B={b_val}")
        elif shape_name == "Ring":
            pdf.ellipse(x+13, y+4, 12, 12)
            if a_val > 0: pdf.text(x+13, y+19, f"A={a_val}")
        elif shape_name == "Crank Bar":
            pdf.line(x+2, y+16, x+10, y+16)
            pdf.line(x+10, y+16, x+18, y+6)
            pdf.line(x+18, y+6, x+32, y+6)
            if a_val > 0: pdf.text(x+3, y+15, f"A={a_val}")
            if b_val > 0: pdf.text(x+12, y+12, f"B={b_val}")
            if c_val > 0: pdf.text(x+22, y+5, f"C={c_val}")
        elif shape_name == "Double Crank":
            pdf.line(x+2, y+6, x+10, y+6)
            pdf.line(x+10, y+6, x+15, y+11)
            pdf.line(x+15, y+11, x+23, y+11)
            pdf.line(x+23, y+11, x+28, y+16)
            pdf.line(x+28, y+16, x+34, y+16)
            if a_val > 0: pdf.text(x+4, y+5, f"A={a_val}")
            if b_val > 0: pdf.text(x+10, y+10, f"B={b_val}")
            if c_val > 0: pdf.text(x+17, y+10, f"C={c_val}")
            if d_val > 0: pdf.text(x+23, y+15, f"D={d_val}")
            if e_val > 0: pdf.text(x+30, y+15, f"E={e_val}")
        elif shape_name == "Bent Up/Down":
            pdf.line(x+2, y+6, x+8, y+6)
            pdf.line(x+8, y+6, x+13, y+16)
            pdf.line(x+13, y+16, x+23, y+16)
            pdf.line(x+23, y+16, x+28, y+6)
            pdf.line(x+28, y+6, x+34, y+6)
            if a_val > 0: pdf.text(x+3, y+5, f"A={a_val}")
            if b_val > 0: pdf.text(x+8, y+12, f"B={b_val}")
            if c_val > 0: pdf.text(x+15, y+19, f"C={c_val}")
            if d_val > 0: pdf.text(x+26, y+12, f"D={d_val}")
            if e_val > 0: pdf.text(x+30, y+5, f"E={e_val}")
        elif shape_name == "Chair":
            pdf.line(x+2, y+16, x+8, y+16)
            pdf.line(x+8, y+16, x+8, y+6)
            pdf.line(x+8, y+6, x+28, y+6)
            pdf.line(x+28, y+6, x+28, y+16)
            pdf.line(x+28, y+16, x+34, y+16)
            if a_val > 0: pdf.text(x+2, y+19, f"A={a_val}")
            if b_val > 0: pdf.text(x+2, y+11, f"B={b_val}")
            if c_val > 0: pdf.text(x+15, y+5, f"C={c_val}")
            if d_val > 0: pdf.text(x+29, y+11, f"D={d_val}")
            if e_val > 0: pdf.text(x+29, y+19, f"E={e_val}")

        pdf.set_font("Arial", size=9)

        pdf.cell(10, row_height, txt=str(row["Bar Size (mm)"]), border=1, align='C')
        pdf.cell(12, row_height, txt=a_tbl, border=1, align='C')
        pdf.cell(12, row_height, txt=b_tbl, border=1, align='C')
        pdf.cell(12, row_height, txt=c_tbl, border=1, align='C')
        pdf.cell(12, row_height, txt=d_tbl, border=1, align='C')
        pdf.cell(12, row_height, txt=e_tbl, border=1, align='C')

        hook_val = row[f"Hook ({unit})"]
        pdf.cell(12, row_height, txt=f"{hook_val:g}" if hook_val > 0 else "", border=1, align='C')
        pdf.cell(10, row_height, txt=str(row["Qty"]), border=1, align='C')
        pdf.cell(16, row_height, txt=str(row[f"Cut L ({unit})"]), border=1, align='C')
        pdf.cell(18, row_height, txt=str(row[f"Total L ({unit})"]), border=1, align='C')
        pdf.cell(20, row_height, txt=str(row["Total Wt (kg)"]), border=1, align='C')
        pdf.ln()
        total_weight += row["Total Wt (kg)"]

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(250, 10, txt=f"Grand Total Weight: {round(total_weight, 2)} kg", ln=True, align='R')

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f: pdf_bytes = f.read()
    os.remove(tmp.name)
    return pdf_bytes

# ==========================================
# 3. APP LAYOUT, LANGUAGE & MENU
# ==========================================
st.set_page_config(page_title="Material Optimizer", layout="wide")

# Sidebar - Language Selection + Module Menu
st.sidebar.title("⚙️ Settings")
lang = st.sidebar.radio("Language / ဘာသာစကား", ["မြန်မာ", "English"])
st.sidebar.divider()

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
        "dl_btn": "📥 PDF Report ဆွဲယူရန်",
        "menu": "မီနူး ရွေးချယ်ရန်",
        "module_opt": "✂️ ဖြတ်တောက်မှု တွက်ချက်ရန်",
        "module_bbs": "📝 Bar Bending Schedule (BBS)",
        "bbs_title": "Bar Bending Schedule (BBS)",
        "bbs_desc": "သံချောင်းပုံစံအမျိုးမျိုးအတွက် ဖြတ်တောက်ရမည့်အရှည်နှင့် အလေးချိန်တို့ကို အလိုအလျောက် တွက်ချက်ပေးပါသည်။"
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
        "dl_btn": "📥 Download PDF Report",
        "menu": "Menu",
        "module_opt": "✂️ Cutting Optimizer",
        "module_bbs": "📝 Bar Bending Schedule (BBS)",
        "bbs_title": "Bar Bending Schedule (BBS)",
        "bbs_desc": "Automatically calculate cutting lengths and weights for various rebar shapes."
    }

module = st.sidebar.radio(t["menu"], [t["module_opt"], t["module_bbs"]])

# ------------------------------------------
# MODULE 1: CUTTING OPTIMIZER
# ------------------------------------------
if module == t["module_opt"]:
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

# ------------------------------------------
# MODULE 2: BAR BENDING SCHEDULE (BBS)
# ------------------------------------------
elif module == t["module_bbs"]:
    st.title(f"📝 {t['bbs_title']}")
    st.write(t["bbs_desc"])

    st.header("၁။ Data ထည့်သွင်းရန်")

    unit_bbs = st.selectbox("ယူနစ် (Unit) ရွေးချယ်ရန်", ["m", "ft", "mm", "in"], key="unit_bbs")

    st.markdown(f"""
    **💡 Shape (ပုံစံ) အလိုက် အနားများ ထည့်သွင်းနည်း -**
    * **(အရေးကြီး) - A, B, C, D, E အားလုံးကို အပြင်အစွန်းမှ အပြင်အစွန်းသို့ (Outer-to-Outer dimension) ဖြင့် ထည့်သွင်းပေးပါ။**
    * ပုံကြမ်းပေါ်ရှိ အနီရောင်စာသား (A, B, C...) လေးများအတိုင်း ဇယားထဲတွင် ယှဉ်တွဲထည့်သွင်းပေးပါ။
    * **Standard Hook:** လိုအပ်ပါက Hook သို့မဟုတ် Lap Length စုစုပေါင်းကို **{unit_bbs}** ယူနစ်ဖြင့် တိုက်ရိုက် ဂဏန်းရိုက်ထည့်ပါ။ (ဒသမနောက် ၄ လုံးအထိ ရိုက်ထည့်နိုင်ပါသည်)
    """)

    if 'bbs_unit_prev' not in st.session_state or st.session_state['bbs_unit_prev'] != unit_bbs or 'bbs_df' not in st.session_state:
        st.session_state['bbs_df'] = pd.DataFrame({
            "Bar Mark": ["B1", "L1", "U1", "S1", "C1", "DC1", "BU1"],
            "Shape": ["Straight", "L-Shape", "U-Shape", "Stirrup (Rect)", "Crank Bar", "Double Crank", "Bent Up/Down"],
            "Sketch": [SHAPE_IMAGES[s] for s in ["Straight", "L-Shape", "U-Shape", "Stirrup (Rect)", "Crank Bar", "Double Crank", "Bent Up/Down"]],
            "Bar Size (mm)": [0]*7,
            f"A ({unit_bbs})": [0.0]*7,
            f"B ({unit_bbs})": [0.0]*7,
            f"C ({unit_bbs})": [0.0]*7,
            f"D ({unit_bbs})": [0.0]*7,
            f"E ({unit_bbs})": [0.0]*7,
            f"Standard Hook ({unit_bbs})": [0.0]*7,
            "No. of Members": [0]*7,
            "Bars per Member": [0]*7
        })
        st.session_state['bbs_unit_prev'] = unit_bbs

    edited_bbs = st.data_editor(
        st.session_state['bbs_df'],
        num_rows="dynamic",
        use_container_width=True,
        column_order=["Bar Mark", "Shape", "Sketch", "Bar Size (mm)", f"A ({unit_bbs})", f"B ({unit_bbs})", f"C ({unit_bbs})", f"D ({unit_bbs})", f"E ({unit_bbs})", f"Standard Hook ({unit_bbs})", "No. of Members", "Bars per Member"],
        column_config={
            "Shape": st.column_config.SelectboxColumn(
                "Shape",
                help="သံချောင်းပုံစံရွေးချယ်ရန်",
                options=list(SHAPE_IMAGES.keys()),
                required=True
            ),
            "Sketch": st.column_config.ImageColumn(
                "ပုံကြမ်း (Sketch)"
            ),
            "Bar Size (mm)": st.column_config.NumberColumn(
                "Bar Size (mm)", min_value=0, step=1, format="%d"
            ),
            f"Standard Hook ({unit_bbs})": st.column_config.NumberColumn(
                f"Standard Hook ({unit_bbs})", help="Hook သို့မဟုတ် Lap Length စုစုပေါင်းအရှည်ကို ရိုက်ထည့်ပါ", min_value=0.0, step=0.0001, format="%.4f"
            )
        }
    )

    needs_rerun = False
    for idx in edited_bbs.index:
        shape = str(edited_bbs.loc[idx, "Shape"])
        correct_sketch = SHAPE_IMAGES.get(shape, "")
        if str(edited_bbs.loc[idx, "Sketch"]) != correct_sketch:
            edited_bbs.loc[idx, "Sketch"] = correct_sketch
            needs_rerun = True

    if needs_rerun:
        st.session_state['bbs_df'] = edited_bbs
        st.rerun()

    bbs_calc_btn = st.button("📊 BBS တွက်ချက်မည် (Calculate)", type="primary")

    if bbs_calc_btn:
        with st.spinner("တွက်ချက်နေပါသည်..."):
            bbs_result_df = calculate_bbs(edited_bbs, unit_bbs)
            st.session_state['bbs_result'] = bbs_result_df
            st.session_state['bbs_calculated'] = True
            st.session_state['bbs_unit'] = unit_bbs
            st.session_state['bbs_df'] = edited_bbs

    if st.session_state.get('bbs_calculated', False):
        st.header("၂။ BBS ရလဒ်များ")
        res_df = st.session_state['bbs_result']
        curr_unit = st.session_state['bbs_unit']

        if not res_df.empty:
            st.dataframe(
                res_df,
                column_config={
                    "Sketch": st.column_config.ImageColumn(
                        "ပုံကြမ်း (Sketch)"
                    )
                },
                hide_index=True,
                use_container_width=True
            )

            total_kg = res_df["Total Wt (kg)"].sum()
            total_ton = round(total_kg / 1000, 3)
            st.success(f"⚖️ စုစုပေါင်း အလေးချိန် (Total Weight) = **{round(total_kg, 2)} kg** ({total_ton} Ton)")

            st.divider()
            st.subheader("📄 BBS Report ဆွဲယူရန်")
            bbs_pdf_bytes = generate_bbs_pdf(res_df, curr_unit)
            st.download_button(
                label="📥 Download BBS PDF Report",
                data=bbs_pdf_bytes,
                file_name="BBS_Report_Detailed.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.warning("တွက်ချက်ရန်အတွက် Bar Size နှင့် အတိုင်းအတာ (A, B သို့မဟုတ် C) များကို ထည့်သွင်းပေးပါ။")
