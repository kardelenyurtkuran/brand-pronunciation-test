import streamlit as st
from gtts import gTTS
import os
import speech_recognition as sr
import io
from difflib import SequenceMatcher

# --- 1. TÜM MARKA LİSTESİ VE DİLLERİ ---
BRANDS = {
    "Armani Collezioni": {"lang": "it"},
    "Armani Exchange": {"lang": "it"},
    "Armani Jeans": {"lang": "it"},
    "C.P. Company": {"lang": "it"},
    "Dolce Gabbana": {"lang": "it"},
    "Dsquared2": {"lang": "it"},
    "EA7": {"lang": "it"},
    "Emporio Armani": {"lang": "it"},
    "Etro": {"lang": "it"},
    "Exxe": {"lang": "it"},
    "Fendi": {"lang": "it"},
    "Giorgio Armani": {"lang": "it"},
    "Giuseppe Zanotti": {"lang": "it"},
    "Golden Goose": {"lang": "it"},
    "Gran Sasso": {"lang": "it"},
    "Jacob Cohen": {"lang": "it"},
    "Just Cavalli": {"lang": "it"},
    "Lazzerini Tiziana": {"lang": "it"},
    "Love Moschino": {"lang": "it"},
    "Manuel Ritz": {"lang": "it"},
    "Marni": {"lang": "it"},
    "Moaconcept": {"lang": "it"},
    "Montecore": {"lang": "it"},
    "Marcelo Burlon": {"lang": "it"},
    "Moon Boot": {"lang": "it"},
    "Miu Miu": {"lang": "it"},
    "Palm Angels": {"lang": "it"},
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

st.set_page_config(page_title="Zorunlu Marka Telaffuz Testi", page_icon="🗣️")

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
    st.success(f"Tüm {total_brands} markanın telaffuzunu başarıyla tamamladınız ve sertifikasyon sürecini geçtiniz!")
    if st.button("Testi Yeniden Başlat"):
        st.session_state.current_index = 0
        st.session_state.audio_listened = False
        st.session_state.test_completed = False
        st.session_state.current_audio = None
        st.rerun()
    st.stop()

selected_brand_name = brand_keys[st.session_state.current_index]
brand_info = BRANDS[selected_brand_name]

# --- 4. SAYAÇ VE GÖRSEL ARAYÜZ ---
st.title("🗣️ Satış Ekibi Telaffuz Sertifikasyonu")

progress_text = f"İlerleme Durumu: {st.session_state.current_index + 1} / {total_brands}"
st.subheader(progress_text)
st.progress((st.session_state.current_index + 1) / total_brands)

st.divider()

st.markdown(f"Mevcut Marka: **{selected_brand_name}** ({LANG_MAP.get(brand_info['lang'], 'Global')})")

# --- LOGO ALANI ---
formatted_name = selected_brand_name.replace(".", "").replace("&", "").replace(" ", "_").lower()
logo_path_png = os.path.join("logos", f"{formatted_name}_logo.png")
logo_path_jpg = os.path.join("logos", f"{formatted_name}_logo.jpg")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists(logo_path_png):
        st.image(logo_path_png, width=220)
    elif os.path.exists(logo_path_jpg):
        st.image(logo_path_jpg, width=220)
    else:
        st.info(f"💡 Logo bulunamadı: `logos/{formatted_name}_logo.png`")

st.divider()

# --- BÖLÜM 1: ZORUNLU DİNLEME ---
st.subheader("1. Doğru Telaffuzu Dinleyin (Mecburi)")
st.info("⚠️ Ses kaydı yapabilmek için öncelikle doğru okunuşu en az bir kez dinlemelisiniz.")

if st.button("🔊 Doğru Okunuşu Seslendir"):
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

st.divider()

# --- BÖLÜM 2: TEST ETME & GEÇİŞ KİLİDİ ---
st.subheader("2. Kendinizi Test Edin")

if not st.session_state.audio_listened:
    st.warning("🔒 Önce yukarıdaki butondan doğru telaffuzu dinleyin.")
else:
    st.write("Aşağıdaki mikrofon alanını kullanarak sesinizi kaydedin:")
    
    audio_file_input = st.audio_input(
        label="Sesinizi kaydedin", 
        key=f"audio_input_{st.session_state.current_index}"
    )

    if audio_file_input is not None:
        r = sr.Recognizer()
        
        # Streamlit'in audio_input bileşeninden gelen byte verisini Wav formatına hazırlıyoruz
        audio_data = io.BytesIO(audio_file_input.read())
        
        with sr.AudioFile(audio_data) as source:
            audio = r.record(source)
            
            try:
                # Tanıma motorunu çalıştırıyoruz
                user_said = r.recognize_google(audio, language=brand_info["lang"])
                st.info(f"Sizin Söylediğiniz: **{user_said}**")
                
                clean_user_said = user_said.lower().replace(".", "").replace(" ", "")
                clean_brand_name = selected_brand_name.lower().replace(".", "").replace(" ", "")
                
                # İki metin arasındaki benzerlik oranını hesaplıyoruz
                similarity_ratio = SequenceMatcher(None, clean_user_said, clean_brand_name).ratio()
                
                # %75 ve üzeri benzerliği personelin akıcılığı için yeterli görüp DOĞRU kabul ediyoruz
                if similarity_ratio >= 0.75:
                    st.success(f"🎉 Harika! Doğru telaffuz. (Benzerlik Skoru: %{int(similarity_ratio*100)})")
                    
                    if st.button("➡️ Sonraki Markaya Geç"):
                        if st.session_state.current_index + 1 < total_brands:
                            st.session_state.current_index += 1
                            st.session_state.audio_listened = False 
                            st.session_state.current_audio = None 
                        else:
                            st.session_state.test_completed = True
                        st.rerun()
                else:
                    st.error(f"❌ Eşleşmedi! Doğru yapana kadar bu markayı geçemezsiniz. Lütfen tekrar deneyin. (Benzerlik: %{int(similarity_ratio*100)})")
                    st.caption(f"Beklenen: {selected_brand_name} | Algılanan: {user_said}")
                    
            except sr.UnknownValueError:
                st.warning("Ses net anlaşılamadı. Lütfen mikrofona yakın şekilde, kelimeyi tane tane ve biraz daha yüksek sesle tekrar söyleyin.")
            except sr.RequestError as e:
                st.error(f"Sistem hatası (Bağlantı sorunu): {e}")