import streamlit as st
from gtts import gTTS
import os
import speech_recognition as sr
import io
from difflib import SequenceMatcher
import datetime
import pandas as pd
import sqlite3

# Supabase kütüphanesi kontrolü
try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False

# --- 1. MAĞAZALAR VE MARKA LİSTESİ ---
STORES = [
    "EA KORUPARK", 
    "AX KORUPARK", 
    "ES BURSA", 
    "ES SUSURLUK", 
    "EA AKASYA", 
    "ES AFYON", 
    "ES GEBZE", 
    "ES ANTALYA", 
    "MANİSA OKSİJEN", 
    "ES OPTİMUM", 
    "ANTALYA POP-UP", 
    "SİNPAŞ MARMARİS", 
    "ES SELÇUK"
]

BRANDS = {
    "GMG Firenze": {"lang": "en"},
    "Alberto Guardiani": {"lang": "it"},
    "Salvatore Ferragamo": {"lang": "it"},
    "Armani Exchange": {"lang": "it"},
    "Moschino": {"lang": "it"},
    "Claudio Campione": {"lang": "de"},
    "Dolce Gabbana": {"lang": "it"},
    "Dsquared2": {"lang": "en"},
    "EA7": {"lang": "en"},
    "Emporio Armani": {"lang": "it"},
    "Etro": {"lang": "it"},
    "Fendi": {"lang": "it"},
    "Giorgio Armani": {"lang": "it"},
    "Giuseppe Zanotti": {"lang": "it"},
    "Golden Goose": {"lang": "en"},
    "Gran Sasso": {"lang": "it"},
    "Jacob Cohen": {"lang": "it"},
    "Love Moschino": {"lang": "en"},
    "Manuel Ritz": {"lang": "it"},
    "Moaconcept": {"lang": "it"},
    "Montecore": {"lang": "en"},
    "Marcelo Burlon": {"lang": "it"},
    "Moon Boot": {"lang": "it"},
    "Miu Miu": {"lang": "it"},
    "Palm Angels": {"lang": "en"},
    "Prada Sport": {"lang": "it"},
    "Paul & Shark": {"lang": "it"},
    "Pinko": {"lang": "it"},
    "Premiata": {"lang": "it"},
    "Philippe Model": {"lang": "it"},
    "Prada": {"lang": "it"},
    "Santoni": {"lang": "it"},
    "Valentino Garavani": {"lang": "it"},
    "Versace": {"lang": "it"},
    "Versace Jeans Couture": {"lang": "it"},
    "Balmain": {"lang": "fr"},
    "Kenzo": {"lang": "fr"},
    "Lacoste": {"lang": "fr"},
    "Longchamp": {"lang": "fr"},
    "Boss": {"lang": "de"},
    "Birkenstock": {"lang": "de"},
    "Hugo": {"lang": "de"},
    "Philipp Plein": {"lang": "de"},
    "Plein Sport": {"lang": "de"},
    "Asics": {"lang": "ja"},
    "Bohonomad": {"lang": "tr"},
    "Bluemint": {"lang": "tr"},
    "BSB": {"lang": "tr"},
    "Les Benjamins": {"lang": "tr"},
    "Autry": {"lang": "en"},
    "Burberry": {"lang": "en"},
    "Brooks Brothers": {"lang": "en"},
    "Crocs": {"lang": "en"},
    "Calvin Klein": {"lang": "en"},
    "Camper": {"lang": "en"},
    "Fred Perry": {"lang": "en"},
    "Goorin Bros": {"lang": "en"},
    "Guess": {"lang": "en"},
    "Isaora": {"lang": "en"},
    "Marc Jacobs": {"lang": "en"},
    "McQueen": {"lang": "en"},
    "Michael Kors": {"lang": "en"},
    "Marciano by Guess": {"lang": "en"},
    "Mou": {"lang": "en"},
    "Nautica": {"lang": "en"},
    "New Balance": {"lang": "en"},
    "Norway Geographical": {"lang": "en"},
    "Off White": {"lang": "en"},
    "On": {"lang": "en"},
    "Rayban": {"lang": "en"},
    "Stanley": {"lang": "en"},
    "Tiffany&Co": {"lang": "en"},
    "Tommy Hilfiger": {"lang": "en"},
    "Tommy Jeans": {"lang": "en"},
    "UGG": {"lang": "en"},
    "Vans": {"lang": "en"}
}

LANG_MAP = {
    "it": "İtalyanca 🇮🇹", "fr": "Fransızca 🇫🇷", "de": "Almanca 🇩🇪", 
    "en": "İngilizce/Global 🇬🇧", "ja": "Japonca 🇯🇵", "tr": "Türkçe 🇹🇷"
}

st.set_page_config(
    page_title="Zorunlu Marka Telaffuz Eğitimi", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. VERİTABANI YARDIMCI MİMARİSİ (SUPABASE + LOCAL SQLITE FALLBACK) ---
def get_db_connection():
    has_secrets = False
    try:
        if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
            has_secrets = True
    except Exception:
        has_secrets = False

    if has_secrets and HAS_SUPABASE_LIB:
        try:
            client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
            return client, "supabase"
        except Exception:
            pass
            
    # Fallback to SQLite
    conn = sqlite3.connect("telaffuz_analytics.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempt_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT,
            user_fullname TEXT,
            brand_name TEXT,
            status TEXT,
            similarity_score INTEGER,
            attempt_count INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT,
            user_fullname TEXT,
            completed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn, "sqlite"

def save_attempt_log(store_name, user_fullname, brand_name, status, similarity_score, attempt_count):
    db, db_type = get_db_connection()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if db_type == "supabase":
        try:
            db.table("attempt_logs").insert({
                "store_name": store_name,
                "user_fullname": user_fullname,
                "brand_name": brand_name,
                "status": status,
                "similarity_score": int(similarity_score),
                "attempt_count": int(attempt_count),
                "created_at": now_str
            }).execute()
        except Exception as e:
            st.error(f"Veritabanı kayıt hatası: {e}")
    else:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO attempt_logs (store_name, user_fullname, brand_name, status, similarity_score, attempt_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (store_name, user_fullname, brand_name, status, int(similarity_score), int(attempt_count), now_str))
        db.commit()

def save_user_session(store_name, user_fullname, completed=0):
    db, db_type = get_db_connection()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if db_type == "supabase":
        try:
            db.table("user_sessions").insert({
                "store_name": store_name,
                "user_fullname": user_fullname,
                "completed": completed,
                "created_at": now_str
            }).execute()
        except Exception:
            pass
    else:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO user_sessions (store_name, user_fullname, completed, created_at)
            VALUES (?, ?, ?, ?)
        """, (store_name, user_fullname, completed, now_str))
        db.commit()

def fetch_all_logs():
    db, db_type = get_db_connection()
    if db_type == "supabase":
        try:
            res_logs = db.table("attempt_logs").select("*").execute()
            df_logs = pd.DataFrame(res_logs.data)
            res_sess = db.table("user_sessions").select("*").execute()
            df_sess = pd.DataFrame(res_sess.data)
            return df_logs, df_sess
        except Exception:
            return pd.DataFrame(), pd.DataFrame()
    else:
        df_logs = pd.read_sql_query("SELECT * FROM attempt_logs", db)
        df_sess = pd.read_sql_query("SELECT * FROM user_sessions", db)
        return df_logs, df_sess

# --- 3. SESSION STATE (HAFIZA) AYARLARI ---
if "user_store" not in st.session_state:
    st.session_state.user_store = ""
if "user_fullname" not in st.session_state:
    st.session_state.user_fullname = ""
if "brand_list" not in st.session_state:
    st.session_state.brand_list = list(BRANDS.keys())
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "audio_listened" not in st.session_state:
    st.session_state.audio_listened = False
if "test_completed" not in st.session_state:
    st.session_state.test_completed = False
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None
if "current_attempts" not in st.session_state:
    st.session_state.current_attempts = 0

# --- 4. YÖNETİCİ PANELI SEÇENEĞİ (SIDEBAR) ---
st.sidebar.title("🔍 Gezinme ve Yönetim")
mode = st.sidebar.radio("Sayfa Seçimi:", ["🗣️ Telaffuz Testi (Personel)", "📊 Yönetici Rapor Paneli"])

# --- 4. YÖNETİCİ VE İK RAPOR PANELSİ ---
if mode == "📊 Yönetici Rapor Paneli":
    st.title("👔 İK & Mağaza Yönetici Analiz Paneli")
    
    admin_password = st.sidebar.text_input("Yönetici Parolası:", type="password")
    
    # SAFE SECRETS READ (Hata Veren Kısım Düzeltildi)
    correct_password = "Exxe2026!"
    try:
        if "ADMIN_PASSWORD" in st.secrets:
            correct_password = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        pass
    
    if admin_password != correct_password:
        st.warning("🔒 Yönetici panelini görüntülemek için lütfen sol menüden yönetici şifrenizi giriniz.")
        st.stop()
        
    df_logs, df_sess = fetch_all_logs()
    
    if df_logs.empty and df_sess.empty:
        st.info("ℹ️ Sistemde henüz kaydedilmiş bir eğitim katılımı veya test verisi bulunmamaktadır.")
        st.stop()
        
    st.success("✅ Veriler canlı sistemden çekildi.")
    
    # 📌 İK / YÖNETİCİ ÖZET METRİKLERİ
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    unique_users = df_sess["user_fullname"].nunique() if not df_sess.empty else 0
    total_stores = df_sess["store_name"].nunique() if not df_sess.empty else 0
    completed_users = len(df_sess[df_sess["completed"] == 1]) if not df_sess.empty else 0
    completion_rate = int((completed_users / unique_users * 100)) if unique_users > 0 else 0
    
    kpi1.metric("👥 Eğitime Katılan Personel", f"{unique_users} Kişi")
    kpi2.metric("🏪 Aktif Katılan Mağaza", f"{total_stores} Mağaza")
    kpi3.metric("🎓 Tamamlayan Personel", f"{completed_users} Personel")
    kpi4.metric("📈 Genel Sertifikasyon Oranı", f"%{completion_rate}")
    
    st.divider()
    
    # 📊 İK VE MAĞAZA ANALİZLERİ
    tab1, tab2, tab3 = st.tabs(["🎯 İK Odak Alanı (Zorlanılan Markalar)", "🏆 Mağaza Performansı", "📋 Personel Karnesi"])
    
    with tab1:
        st.subheader("⚠️ Ekibin En Çok Takıldığı ve Odaklanılması Gereken 5 Marka")
        st.caption("Bu veriler, mağaza içi satış koçlarının hangi markaların okunuşuna ağırlık vermesi gerektiğini gösterir.")
        
        if not df_logs.empty:
            brand_analytics = df_logs.groupby("brand_name").agg(
                Toplam_Deneme=("attempt_count", "sum"),
                Ortalama_Başarı_Skoru=("similarity_score", "mean"),
                Erteleme_Sayıları=("status", lambda x: (x == "SKIPPED").sum())
            ).reset_index()
            
            brand_analytics["Ortalama_Başarı_Skoru"] = brand_analytics["Ortalama_Başarı_Skoru"].round(1).astype(str) + "%"
            hardest_brands = brand_analytics.sort_values(by="Toplam_Deneme", ascending=False).head(5)
            st.table(hardest_brands)

    with tab2:
        st.subheader("🏆 Mağazalara Göre Katılım ve Başarı Durumu")
        if not df_sess.empty:
            store_analytics = df_sess.groupby("store_name").agg(
                Katılan_Personel_Sayısı=("user_fullname", "nunique"),
                Testi_Tamamlayanlar=("completed", "sum")
            ).reset_index()
            
            store_analytics["Tamamlama_Yüzdesi"] = (
                (store_analytics["Testi_Tamamlayanlar"] / store_analytics["Katılan_Personel_Sayısı"]) * 100
            ).round(0).astype(int).astype(str) + "%"
            
            st.dataframe(store_analytics.sort_values(by="Katılan_Personel_Sayısı", ascending=False), use_container_width=True)

    with tab3:
        st.subheader("📋 Bireysel Personel Detayları")
        if not df_logs.empty:
            st.dataframe(df_logs[["created_at", "store_name", "user_fullname", "brand_name", "status", "similarity_score"]], use_container_width=True)
            
            csv_data = df_logs.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 İK Raporunu Excel/CSV Olarak İndir",
                data=csv_data,
                file_name=f"ik_telaffuz_raporu_{datetime.date.today()}.csv",
                mime="text/csv"
            )

    # 🧹 TEST & DENEME VERİLERİNİ SIFIRLAMA
    st.divider()
    with st.expander("⚙️ Yönetici Araçları: Test Verilerini Temizle / Sıfırla"):
        st.warning("🚨 DİKKAT: Aşağıdaki buton, canlıya geçmeden önce yaptığınız TÜM deneme ve test kayıtlarını veritabanından kalıcı olarak siler!")
        
        confirm_reset = st.checkbox("Evet, tüm deneme verilerini silmek ve sistemi sıfırlamak istiyorum.")
        if st.button("🗑️ TÜM TEST VERİLERİNİ SİL", type="primary", disabled=not confirm_reset):
            db, db_type = get_db_connection()
            if db_type == "supabase":
                db.table("attempt_logs").delete().neq("id", 0).execute()
                db.table("user_sessions").delete().neq("id", 0).execute()
            else:
                cursor = db.cursor()
                cursor.execute("DELETE FROM attempt_logs")
                cursor.execute("DELETE FROM user_sessions")
                db.commit()
            st.success("🎉 Tüm test verileri başarıyla temizlendi! Sistem gerçek personel katılımı için hazır.")
            st.rerun()

    st.stop()

# --- 5. PERSONEL KULLANICI GİRİŞ EKRANI ---
if not st.session_state.user_store or not st.session_state.user_fullname:
    st.title("🗣️ Satış Ekibi Telaffuz Eğitimi")
    st.subheader("👤 Lütfen Teste Başlamadan Önce Bilgilerinizi Girin")
    
    with st.form("user_login_form"):
        store_input = st.selectbox("🏪 Mağazanızı Seçiniz:", options=["Lütfen mağazanızı seçiniz..."] + STORES)
        name_input = st.text_input("👤 Adınız ve Soyadınız:")
        submit_login = st.form_submit_button("🚀 Teste Başla")
        
        if submit_login:
            if store_input != "Lütfen mağazanızı seçiniz..." and name_input.strip():
                st.session_state.user_store = store_input
                st.session_state.user_fullname = name_input.strip()
                save_user_session(st.session_state.user_store, st.session_state.user_fullname, completed=0)
                st.success(f"Hoş geldiniz {st.session_state.user_fullname}! Testiniz yükleniyor...")
                st.rerun()
            else:
                st.error("⚠️ Lütfen hem Mağaza seçiminizi yapın hem de Ad Soyad bilgilerinizi eksiksiz girin.")
    st.stop()

# --- 6. TEST BİTME EKRANI ---
total_brands = len(st.session_state.brand_list)

if st.session_state.test_completed:
    st.balloons()
    st.title("🎉 Tebrikler! Test Tamamlandı")
    st.success(f"Sayın **{st.session_state.user_fullname}** ({st.session_state.user_store}), tüm markaların telaffuzunu başarıyla tamamladınız ve sertifikasyon sürecini geçtiniz!")
    
    save_user_session(st.session_state.user_store, st.session_state.user_fullname, completed=1)
    
    st.info("💡 Testi bitirmek ve sonuçlarınızı kaydetmek için tarayıcı sekmesini kapatabilirsiniz.")
    if st.button("🔄 Testi Yeniden Başlat"):
        st.session_state.brand_list = list(BRANDS.keys())
        st.session_state.current_index = 0
        st.session_state.audio_listened = False
        st.session_state.test_completed = False
        st.session_state.current_audio = None
        st.session_state.current_attempts = 0
        st.rerun()
    st.stop()

# Mevcut markayı dinamik listeden seçiyoruz
selected_brand_name = st.session_state.brand_list[st.session_state.current_index]
brand_info = BRANDS[selected_brand_name]

# --- 7. SAYAÇ VE GÖRSEL ARAYÜZ ---
st.title("Satış Ekibi Telaffuz Eğitimi")
st.caption(f"👤 Aktif Kullanıcı: **{st.session_state.user_fullname}** | 🏪 Mağaza: **{st.session_state.user_store}**")

st.markdown("""
> 📋 **Bilgilendirme:** 
> 1. Önce mevcut markanın **Doğru Okunuşunu Dinle** butonuna basarak sistemi aktifleştirin ve telaffuzu dinleyin.
> 2. Ardından açılacak olan **Kendinizi Test Edin** alanındaki mikrofon simgesine basarak markanın adını söyleyin.
> 3. %80 başarı oranını yakaladığınızda belirecek olan **Sonraki Markaya Geç** butonuyla ilerleyin.
> 4. Telaffuzda zorlanırsanız **Daha Sonra Dene (En Sona At)** butonunu kullanarak o markayı listenin en sonuna erteleyebilirsiniz.
""")

progress_text = f"İlerleme Durumu: {st.session_state.current_index + 1} / {total_brands}"
st.subheader(progress_text)
st.progress((st.session_state.current_index + 1) / total_brands)

st.divider()

# --- DİNAMİK YAN YANA TASARIM (LOGO VE ETKİLEŞİM BİR ARADA) ---
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.subheader("Marka Logosu")
    formatted_name = selected_brand_name.replace(".", "").replace("&", "").replace(" ", "_").lower()
    logo_path_png = os.path.join("logos", f"{formatted_name}_logo.png")
    logo_path_jpg = os.path.join("logos", f"{formatted_name}_logo.jpg")

    if os.path.exists(logo_path_png):
        st.image(logo_path_png, use_container_width=True)
    elif os.path.exists(logo_path_jpg):
        st.image(logo_path_jpg, use_container_width=True)
    else:
        st.info(f"💡 Logo görseli aranıyor: `logos/{formatted_name}_logo.png` veya `.jpg` bulunamadı. Lütfen klasörü kontrol edin.")

with right_col:
    # --- BÖLÜM 1: ZORUNLU DİNLEME ---
    st.subheader(f"1. Doğru Telaffuzu Dinleyin: {selected_brand_name}")
    st.caption(f"Bu markanın hedeflenen orijinal dil kökeni: **{LANG_MAP.get(brand_info['lang'], 'Global')}**")
    
    if st.button("🔊 Doğru Okunuşu Dinle", use_container_width=True):
        tts = gTTS(text=selected_brand_name, lang=brand_info["lang"])
        filename = f"temp_{st.session_state.current_index}.mp3"
        tts.save(filename)
        
        with open(filename, 'rb') as audio_file:
            st.session_state.current_audio = audio_file.read()
        
        os.remove(filename)
        st.session_state.audio_listened = True
        st.rerun()

    if st.session_state.current_audio is not None:
        st.audio(st.session_state.current_audio, format='audio/mp3')
        st.caption("👇 Şimdi aşağıdaki test alanından sesinizi kaydedebilirsiniz.")

    st.divider()

    # --- BÖLÜM 2: TEST ETME & GEÇİŞ KİLİDİ ---
    st.subheader("2. Kendinizi Test Edin")

    if not st.session_state.audio_listened:
        st.warning("🔒 Önce yukarıdaki 'Doğru Okunuşu Dinle' butonuna basarak telaffuzu en az bir kez dinlemelisiniz.")
    else:
        st.write("👉 Siyah mikrofon simgesine basıp konuşun, bitince tekrar basın:")
        
        audio_file_input = st.audio_input(
            label="Ses kaydını başlatın", 
            key=f"audio_input_{st.session_state.current_index}"
        )

        # --- ERTELEME BUTONU ---
        st.write("---")
        st.write("💡 Bu markada zorlandınız mı? Süreci tıkamamak için sıranın en arkasına gönderebilirsiniz:")
        if st.button("⏳ Daha Sonra Dene (En Sona At)", use_container_width=True):
            save_attempt_log(
                st.session_state.user_store,
                st.session_state.user_fullname,
                selected_brand_name,
                "SKIPPED",
                0,
                st.session_state.current_attempts
            )
            
            current_brand = st.session_state.brand_list.pop(st.session_state.current_index)
            st.session_state.brand_list.append(current_brand)
            
            st.session_state.audio_listened = False
            st.session_state.current_audio = None
            st.session_state.current_attempts = 0
            st.rerun()

        if audio_file_input is not None:
            st.session_state.current_attempts += 1
            r = sr.Recognizer()
            audio_data = io.BytesIO(audio_file_input.read())
            
            with sr.AudioFile(audio_data) as source:
                audio = r.record(source)
                
                try:
                    user_said = r.recognize_google(audio, language=brand_info["lang"])
                    st.info(f"Sizin Söylediğiniz: **{user_said}**")
                    
                    clean_user_said = user_said.lower().replace(".", "").replace(" ", "")
                    clean_brand_name = selected_brand_name.lower().replace(".", "").replace(" ", "")
                    
                    similarity_ratio = SequenceMatcher(None, clean_user_said, clean_brand_name).ratio()
                    score_percent = int(similarity_ratio * 100)
                    
                    if similarity_ratio >= 0.80:
                        st.success(f"🎉 Harika! Yeterli telaffuz başarısı yakalandı. (Benzerlik Skoru: %{score_percent})")
                        
                        save_attempt_log(
                            st.session_state.user_store,
                            st.session_state.user_fullname,
                            selected_brand_name,
                            "PASSED",
                            score_percent,
                            st.session_state.current_attempts
                        )
                        
                        st.markdown("👇 Bir sonraki markaya ilerlemek için aşağıdaki butona tıklayın:")
                        if st.button("➡️ Sonraki Markaya Geç", use_container_width=True):
                            if st.session_state.current_index + 1 < total_brands:
                                st.session_state.current_index += 1
                                st.session_state.audio_listened = False 
                                st.session_state.current_audio = None 
                                st.session_state.current_attempts = 0
                            else:
                                st.session_state.test_completed = True
                            st.rerun()
                    else:
                        st.error(f"❌ Telaffuz tam eşleşmedi! İstenen baraj %80, sizin skorunuz: %{score_percent}")
                        st.caption(f"Beklenen Temel Kalıp: {selected_brand_name} | Sizin Söylediğiniz: {user_said}")
                        st.warning("🔄 Lütfen logoya bakın, doğru telaffuzu tekrar dinleyin ve yeniden deneyin ya da yukarıdaki 'Daha Sonra Dene' butonuyla bu markayı erteleyin.")
                        
                        save_attempt_log(
                            st.session_state.user_store,
                            st.session_state.user_fullname,
                            selected_brand_name,
                            "FAILED",
                            score_percent,
                            st.session_state.current_attempts
                        )
                        
                except sr.UnknownValueError:
                    st.warning("⚠️ Ses tam anlaşılamadı. Lütfen ortamdaki gürültüyü azaltıp kelimeyi tane tane ve daha net telaffuz ederek tekrar kaydedin.")
                except sr.RequestError as e:
                    st.error(f"Sistem hatası (Bağlantı sorunu): {e}")