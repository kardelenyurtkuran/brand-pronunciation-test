import streamlit as st
from gtts import gTTS
import os
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import io

# 1. Marka Listesi ve Orijinal Dilleri
# Ekibinizin sattığı markalara göre bu listeyi genişletebilirsiniz.
BRANDS = {
    # --- İTALYAN MARKALARI (it) ---
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

    # --- FRANSIZ MARKALARI (fr) ---
    "Balmain": {"lang": "fr"},
    "Kenzo": {"lang": "fr"},
    "Lacoste": {"lang": "fr"},
    "Longchamp": {"lang": "fr"},

    # --- ALMAN MARKALARI (de) ---
    "Boss": {"lang": "de"},
    "Birkenstock": {"lang": "de"},
    "Hugo": {"lang": "de"},
    "Hugo Boss": {"lang": "de"},
    "Philipp Plein": {"lang": "de"},
    "Plein Sport": {"lang": "de"},

    # --- JAPON MARKALARI (ja) ---
    "Asics": {"lang": "ja"},

    # --- TÜRK / TÜRK KÖKENLİ MARKALAR (tr) ---
    "Bohonomad": {"lang": "tr"},      # İzmir menşeili halat sandalet markası
    "Bluemint": {"lang": "tr"},       # Türk lüks mayo/giyim markası
    "BSB": {"lang": "tr"},            # Türkiye odaklı/kökenli hazır giyim
    "Les Benjamins": {"lang": "tr"},  # İstanbul kökenli sokak modası markası

    # --- AMERİKAN, İNGİLİZ VE DİĞER GLOBAL MARKALAR (en) ---
    # (Bu markalar küresel olarak İngilizce telaffuz kalıplarıyla değerlendirilir)
    "Autry": {"lang": "en"},
    "Burberry": {"lang": "en"},
    "BALR.": {"lang": "en"},           # Hollanda kökenli ancak global İngilizce okunur
    "Brooks Brothers": {"lang": "en"},
    "Crocs": {"lang": "en"},
    "Calvin Klein": {"lang": "en"},
    "Camper": {"lang": "en"},          # İspanyol kökenli ancak İngilizce telaffuzu yaygındır
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
    "On": {"lang": "en"},              # İsviçre kökenli performans markası
    "Rayban": {"lang": "en"},
    "Stanley": {"lang": "en"},
    "Tiffany&Co": {"lang": "en"},
    "Tommy Hilfiger": {"lang": "en"},
    "Tommy Jeans": {"lang": "en"},
    "UGG": {"lang": "en"},
    "Vans": {"lang": "en"}
}

st.title("🗣️ Marka Telaffuz Eğitimi ve Testi")
st.write("Doğru telaffuzu dinleyin, ardından kendi sesinizi kaydederek kendinizi test edin!")

# Marka Seçimi
selected_brand_name = st.selectbox("Çalışmak istediğiniz markayı seçin:", list(BRANDS.keys()))
brand_info = BRANDS[selected_brand_name]

# --- BÖLÜM 1: DİNLEME ---
st.subheader("1. Doğru Telaffuzu Dinleyin")

if st.button("Doğru Okunuşu Seslendir"):
    # gTTS ile markanın orijinal dilindeki sesini üretiyoruz
    tts = gTTS(text=selected_brand_name, lang=brand_info["lang"])
    filename = "correct_pronunciation.mp3"
    tts.save(filename)
    
    # Sesi arayüzde oynatıyoruz
    audio_file = open(filename, 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3')
    audio_file.close()
    os.remove(filename) # Geçici dosyayı siliyoruz

st.divider()

# --- BÖLÜM 2: TEST ETME ---
st.subheader("2. Kendinizi Test Edin")
st.write("Düğmeye basılı tutarak veya tıklayarak markanın ismini söyleyin:")

# Mikrofon kaydı bileşeni
audio_record = mic_recorder(
    start_prompt="🔴 Kaydı Başlat",
    stop_prompt="⏹️ Kaydı Bitir",
    key='recorder'
)

if audio_record:
    # Kaydedilen sesi arayüzde dinleme imkanı sunalım
    st.audio(audio_record['bytes'], format='audio/wav')
    
    # Ses tanıma (Speech Recognition) işlemi
    r = sr.Recognizer()
    audio_data = io.BytesIO(audio_record['bytes'])
    
    with sr.AudioFile(audio_data) as source:
        audio = r.record(source)
        
        try:
            # Kullanıcının sesini, markanın orijinal diline göre metne çeviriyoruz
            user_said = r.recognize_google(audio, language=brand_info["lang"])
            st.info(f"Sizin Söylediğiniz: **{user_said}**")
            
            # Doğruluk Kontrolü (Büyük/küçük harf duyarlılığını ortadan kaldırarak)
            if user_said.lower() == selected_brand_name.lower():
                st.success("🎉 Tebrikler! Doğru telaffuz ettiniz.")
            else:
                st.error("❌ Maalesef eşleşmedi. Tekrar deneyebilirsiniz.")
                st.caption(f"Beklenen: {selected_brand_name} | Algılanan: {user_said}")
                
        except sr.UnknownValueError:
            st.warning("Sesiniz tam anlaşılamadı, lütfen daha net ve mikrofona yakın konuşarak tekrar deneyin.")
        except sr.RequestError as e:
            st.error(f"Ses tanıma servisinde bir sorun oluştu: {e}")