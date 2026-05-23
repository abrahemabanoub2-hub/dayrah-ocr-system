import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="منظومة عقود ديرة الذكية", layout="wide")
st.title("📊 منظومة عقود ديرة الذكية (فحص الـ OCR والذكاء الاصطناعي)")

# الاتصال بالخدمات باستخدام الـ Secrets
try:
    # 1. إعداد الـ Gemini API
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 2. إعداد الجوجل شيت
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    gcp_json = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    creds = Credentials.from_service_account_info(gcp_json, scopes=scope)
    client = gspread.authorize(creds)
    
    # فتح الشيت باستخدام الرابط
    sheet_url = "https://docs.google.com/spreadsheets/d/1D6oMs773jqapasEZoMfqw4o_xgWd4u1QpiEfsDt896M/edit"
    sheet = client.open_by_url(sheet_url).sheet1
except Exception as e:
    st.error(f"حدث خطأ في الاتصال بالخادم والـ Secrets: {e}")

# واجهة المستخدم للموظف
st.subheader("✍️ محطة إدخال الموظف (الفرع والملفات)")

# إدخال الفرع يدوياً
branch = st.text_input("📍 اكتب اسم الفرع:")

# رفع الملفات (صور أو PDF)
uploaded_files = st.file_uploader("📂 ارفع أوراق المعاملة (العقد الإطاري، التزامات الشركة، إقرار التوقيع، إلخ...)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'pdf'])

if st.button("🚀 بدء الفحص الذكي واستخراج البيانات"):
    if not branch:
        st.warning("رجاءً اكتب اسم الفرع أولاً!")
    elif not uploaded_files:
        st.warning("رجاءً ارفع ملفات وأوراق المعاملة أولاً!")
    else:
        with st.spinner("جاري تشغيل الذكاء الاصطناعي ومراجعة الـ 8 مستندات..."):
            try:
                # تجهيز الملفات لإرسالها للـ AI
                images_data = []
                for file in uploaded_files:
                    bytes_data = file.read()
                    images_data.append({"mime_type": file.type, "data": bytes_data})
                
                # الـ Prompt الذكي لتحليل الأوراق الاستراتيجية وباقي المستندات
                prompt = """
                أنت مراجع قانوني ومالي صارم بشركة 'ديرة'. أمامك مستندات مرفوعة لمعاملة عميل. 
                قم بفحص الـ 8 مستندات التالية واستخرج البيانات المطلوبة بالملي باللغة العربية:
                1. العقد الإطاري: استخرج منه (اسم العميل بالكامل، الرقم القومي للعميل المكون من 14 رقم، وتاريخ إنشاء العقد). وابحث هل توجد خانة لاسم الضامن أم لا.
                2. إقرار تم التوقيع أمامي: استخرج منه (كود التمويل الخاص بجمعية العميل).
                3. التزامات الشركة: استخرج منه (قيمة الجمعية / التمويل).
                4. نسخ العقد: إذا وجدت خانة للضامن في العقد الإطاري، فتأكد من وجود ورقة 'نسخ العقد' وموقعة من الضامن.
                5. باقي المستندات (صورة الرقم القومي للعميل والضامن، إقرار الزيارة، إيصال المرافق، إقرار الأيسكور مرفق 6): تأكد من وجودها واكتب تقريراً هل الأوراق كاملة أم ناقصة.

                يجب أن تكون إجابتك بصيغة JSON فقط كالتالي دون أي كلام جانبي:
                {
                  "client_name": "اسم العميل هنا",
                  "national_id": "الرقم القومي للعميل هنا",
                  "contract_date": "تاريخ إنشاء العقد هنا",
                  "funding_code": "كود التمويل بالجمعية هنا",
                  "amount": "قيمة الجمعية هنا",
                  "has_guarantor": "يوجد أو لا يوجد بناءً على الفحص",
                  "document_report": "كاملة أو ناقصة (مع ذكر النواقص إن وجدت)"
                }
                """
                
                # استدعاء نموذج جيميناي برو للرؤية
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content([prompt] + images_data)
                
                # تنظيف النتيجة وتحويلها لـ JSON
                result_text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(result_text)
                
                # عرض النتيجة للموظف للمراجعة والـ Confirmation
                st.success("✅ تم الفحص بنجاح! رجاءً مراجعة البيانات قبل الحفظ النهائي:")
                
                col1, col2 = st.columns(2)
                with col1:
                    final_branch = st.text_input("الفرع", value=branch)
                    final_name = st.text_input("اسم العميل", value=data.get("client_name"))
                    final_id = st.text_input("الرقم القومي للعميل", value=data.get("national_id"))
                    final_date = st.text_input("تاريخ إنشاء العقد", value=data.get("contract_date"))
                with col2:
                    final_code = st.text_input("كود التمويل بالجمعية", value=data.get("funding_code"))
                    final_amount = st.text_input("قيمة الجمعية", value=data.get("amount"))
                    final_guarantor = st.text_input("حالة الضامن", value=data.get("has_guarantor"))
                    final_report = st.text_input("تقرير فحص باقي الأوراق", value=data.get("document_report"))
                
                # زر الحفظ النهائي في الجوجل شيت
                if st.button("💾 حفظ البيانات وإرسالها للصراف"):
                    row = [
                        final_branch, final_name, final_id, final_date, 
                        final_code, final_amount, final_guarantor, final_report,
                        "في انتظار الصراف", "في انتظار المندوب"
                    ]
                    sheet.append_row(row)
                    st.balloons()
                    st.success("🎯 تم إرسال البيانات وحفظها في الجوجل شيت بنجاح مذهل!")
                    
            except Exception as error:
                st.error(f"حدث خطأ أثناء تحليل البيانات من الـ AI: {error}")
                st.info("تأكد أن الصور واضحة وأن ملف الـ Secrets يحتوي على المفاتيح الصحيحة.")
