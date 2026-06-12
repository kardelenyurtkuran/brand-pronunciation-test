import streamlit as st
from gtts import gTTS
import os
import speech_recognition as sr
import io
from difflib import SequenceMatcher

# --- 1. TÜM MARKA LİSTESİ VE DİLLERİ ---
# Türkiye'deki yaygın kullanımına göre güncellediğiniz diller aynen korunmuştur.
# --- 1. TÜM MARKA LİSTESİ VE DİLLERİ ---
BRANDS = {
    "Armani Collezioni": {"lang": "it"},
    "Armani Exchange": {"lang": "it"},
    "Armani Jeans": {"lang": "it"},
    "C.P. Company": {"lang": "it"},
    "Dolce Gabbana": {"lang": "it"},
    "Dsquared2": {"lang": "en"},
    "EA7": {"lang": "en"},
    "Emporio Armani": {"lang": "it"},
    "Etro": {"lang": "it"},
    "Exxe": {"lang": "en"},
    "Fendi": {"lang": "it"},
    "Giorgio Armani": {"lang": "it"},
    "Giuseppe Zanotti": {"lang": "it"},
    "Golden Goose": {"lang": "en"},
    "Gran Sasso": {"lang": "it"},
    "Jacob Cohen": {"lang": "it"},
    "Just Cavalli": {"lang": "it"},
    "Lazzerini Tiziana": {"lang": "it"},
    "Love Moschino": {"lang": "en"},
    "Manuel Ritz": {"lang": "it"},
    "Marni": {"lang": "it"},
    "Moaconcept": {"lang": "it"},
    "Montecore": {"lang": "en"},
    "Marcelo Burlon": {"lang": "it"},
    "Moon Boot": {"lang": "it"},
    "Miu Miu": {"lang": "it"},
    "Palm Angels": {"lang": "en"},
    "Pienza": {"lang": "it"},
    "Prada Sport": {"lang": "it"},
    "Paul & Shark": {"lang": "it"},
    "Pinko": {"lang": "it"},
    "Premiata": {"lang": "it"},
    "Philippe Model": {"lang": "it"},
    "Prada": {"lang": "it"},
    "Santoni": {"lang": "it"},
    "Valentino Garavani": {"lang": "it"},
    "Via Dante": {"lang": "it"},
    "Versace": {"lang": "it"},
    "Versace Jeans Couture": {"lang": "it"},
    "Balmain": {"lang": "fr"},
    "Kenzo": {"lang": "fr"},
    "Lacoste": {"lang": "fr"},
    "Longchamp": {"lang": "fr"},
    "Boss": {"lang": "de"},
    "Birkenstock": {"lang": "de"},
    "Hugo": {"lang": "de"},
    "Hugo Boss": {"lang": "de"},
    "Philipp Plein": {"lang": "de"},
    "Plein Sport": {"lang": "de"},
    "Asics": {"lang": "ja"},
    "Bohonomad": {"lang": "tr"},
    "Bluemint": {"lang": "tr"},
    "BSB": {"lang": "tr"},
    "Les Benjamins": {"lang": "tr"},
    "Autry": {"lang": "en"},
    "Burberry": {"lang": "en"},
    "BALR.": {"lang": "en"},
    "Brooks Brothers": {"lang": "en"},
    "Crocs": {"lang": "en"},
    "Calvin Klein": {"lang": "en"},
    "Camper": {"lang": "en"},
    "Champion": {"lang": "en"},
    "Fred Perry": {"lang": "en"},
    "Goorin Bros": {"lang": "en"},
    "Guess": {"lang": "en"},
    "Isaora": {"lang": "en"},
    "Karl Lagerfeld": {"lang": "en"},
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

st.set_page_config(page_title="Zorunlu Marka Telaffuz", layout="wide")

# --- 2. SESSION STATE (HAFIZA) AYARLARI ---
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "audio_listened" not in st.session_state:
    st.session_state.audio_listened = False
if "test_completed" not in st.session_state:
    st.session_state.test_completed = False
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None

brand_keys = list(BRANDS.keys())
total_brands = len(brand_keys)

# --- 3. TEST BİTME EKRANI ---
if st.session_state.test_completed:
    st.balloons()
    st.title("🎉 Tebrikler! Test Tamamlandı")
    st.success(f"Tüm {total_brands} markanın telaffuzunu başarıyla tamamladınız ve sürecini geçtiniz!")
    st.info("💡 Testi bitirmek ve sonuçlarınızı kaydetmek için tarayıcı sekmesini kapatabilirsiniz.")
    if st.button("🔄 Testi Yeniden Başlat"):
        st.session_state.current_index = 0
        st.session_state.audio_listened = False
        st.session_state.test_completed = False
        st.session_state.current_audio = None
        st.rerun()
    st.stop()

selected_brand_name = brand_keys[st.session_state.current_index]
brand_info = BRANDS[selected_brand_name]

# --- 4. SAYAÇ VE GÖRSEL ARAYÜZ ---
st.title("Satış Ekibi Telaffuz Eğitimi")

# --- GENEL SİSTEM YÖNERGESİ ---
st.markdown("""
> 📋 **Bilgilendirme:** > 1. Önce mevcut markanın **Doğru Okunuşunu Seslendir** butonuna basarak sistemi aktifleştirin ve telaffuzu dinleyin.
> 2. Ardından açılacak olan **Kendinizi Test Edin** alanındaki mikrofon simgesine basarak markanın adını söyleyin.
> 3. %80 başarı oranını yakaladığınızda belirecek olan **Sonraki Markaya Geç** butonuyla ilerleyin.
""")

progress_text = f"İlerleme Durumu: {st.session_state.current_index + 1} / {total_brands}"
st.subheader(progress_text)
st.progress((st.session_state.current_index + 1) / total_brands)

st.divider()

# --- DİNAMİK YAN YANA TASARIM (LOGO VE ETKİLEŞİM BİR ARADA) ---
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    # --- LOGO ALANI (TELAFFUZ ALANININ TAM YANINDA OLMASI İÇİN SOL SÜTUNA ALINDI) ---
    st.subheader("🖼️ Marka Logosu")
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
    
    if st.button("🔊 Doğru Okunuşu Seslendir", use_container_width=True):
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
        st.warning("🔒 Önce yukarıdaki 'Doğru Okunuşu Seslendir' butonuna basarak telaffuzu en az bir kez dinlemelisiniz.")
    else:
        st.write("👉 Siyah mikrofon simgesine basıp konuşun, bitince tekrar basın:")
        
        audio_file_input = st.audio_input(
            label="Ses kaydını başlatın", 
            key=f"audio_input_{st.session_state.current_index}"
        )

        if audio_file_input is not None:
            r = sr.Recognizer()
            audio_data = io.BytesIO(audio_file_input.read())
            
            with sr.AudioFile(audio_data) as source:
                audio = r.record(source)
                
                try:
                    user_said = r.recognize_google(audio, language=brand_info["lang"])
                    st.info(f"Sizin Söylediğiniz: **{user_said}**")
                    
                    clean_user_said = user_said.lower().replace(".", "").replace(" ", "")
                    clean_brand_name = selected_brand_name.lower().replace(".", "").replace(" ", "")
                    
                    # Benzerlik oranı hesaplama
                    similarity_ratio = SequenceMatcher(None, clean_user_said, clean_brand_name).ratio()
                    
                    # BAŞARI ORANI İSTEĞİNİZ ÜZERİNE %80'E YÜKSELTİLDİ
                    if similarity_ratio >= 0.85:
                        st.success(f"🎉 Harika! Yeterli telaffuz başarısı yakalandı. (Benzerlik Skoru: %{int(similarity_ratio*100)})")
                        
                        st.markdown("👇 Bir sonraki markaya ilerlemek için aşağıdaki butona tıklayın:")
                        if st.button("➡️ Sonraki Markaya Geç", use_container_width=True):
                            if st.session_state.current_index + 1 < total_brands:
                                st.session_state.current_index += 1
                                st.session_state.audio_listened = False 
                                st.session_state.current_audio = None 
                            else:
                                st.session_state.test_completed = True
                            st.rerun()
                    else:
                        st.error(f"❌ Telaffuz tam eşleşmedi! İstenen baraj %85, sizin skorunuz: %{int(similarity_ratio*100)}")
                        st.caption(f"Beklenen Temel Kalıp: {selected_brand_name} | Sizin Söylediğiniz: {user_said}")
                        st.warning("🔄 Lütfen logoya bakın, doğru telaffuzu tekrar dinleyin ve mikrofona daha yakın konuşarak yeniden deneyin.")
                        
                except sr.UnknownValueError:
                    st.warning("⚠️ Ses tam anlaşılamadı. Lütfen ortamdaki gürültüyü azaltıp kelimeyi tane tane ve daha net telaffuz ederek tekrar kaydedin.")
                except sr.RequestError as e:
                    st.error(f"Sistem hatası (Bağlantı sorunu): {e}")