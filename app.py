import streamlit as st
import cv2
import pytesseract
import numpy as np
import re

# Sayfa ayarları
st.set_page_config(page_title="Koordinat -> DXF Çevirici", page_icon="📐", layout="centered")

def dxf_metni_olustur(noktalar):
    """Noktaları alıp doğrudan indirilebilir DXF metnine (string) çevirir."""
    dxf_icerik = "  0\nSECTION\n  2\nHEADER\n  0\nENDSEC\n  0\nSECTION\n  2\nENTITIES\n"
    
    for pt in noktalar:
        no = pt['no']
        cad_x = pt['y'] 
        cad_y = pt['x'] 
        
        # Nokta Ekle
        dxf_icerik += f"  0\nPOINT\n  8\nKoordinatlar\n 10\n{cad_x}\n 20\n{cad_y}\n"
        # Yazı Ekle
        dxf_icerik += f"  0\nTEXT\n  8\nNokta_No\n 10\n{cad_x + 1.5}\n 20\n{cad_y + 1.5}\n 40\n2.0\n  1\n{no}\n"
        
    dxf_icerik += "  0\nENDSEC\n  0\nEOF\n"
    return dxf_icerik

def metinden_koordinat_cikar(metin):
    """Verilen metindeki X ve Y değerlerini Regex ile bulur."""
    # Sadece doğru formatta yan yana dizilmiş rakamları ve noktaları yakalar
    desen = r"(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)"
    eslesmeler = re.findall(desen, metin)
    
    noktalar = []
    for no, y, x in eslesmeler:
        noktalar.append({"no": no, "y": float(y), "x": float(x)})
    return noktalar

# --- VİTRİN (ARAYÜZ) ---

st.title("📐 Koordine Özeti DXF Çevirici")
st.markdown("Mimari ve harita projeleriniz için koordinat tablolarını saniyeler içinde DXF formatına dönüştürün.")

# ANA SEÇENEK: GÖRSEL YÜKLEME
st.subheader("1. Seçenek: Tablo Görseli Yükle")
yuklenen_resim = st.file_uploader("Koordinat tablosunun fotoğrafını yükleyin (PNG, JPG)", type=["png", "jpg", "jpeg"])

noktalar = []

if yuklenen_resim is not None:
    # Resmi Streamlit'ten okuma
    dosya_baytlari = np.asarray(bytearray(yuklenen_resim.read()), dtype=np.uint8)
    img = cv2.imdecode(dosya_baytlari, 1)
    
    with st.spinner('Görüntü netleştiriliyor ve koordinatlar okunuyor...'):
        # --- GÖRÜNTÜ İYİLEŞTİRME (PRE-PROCESSING) ---
        # 1. Resmi 2 kat büyüt
        img_buyuk = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        # 2. Gri tonlamaya çevir
        gri = cv2.cvtColor(img_buyuk, cv2.COLOR_BGR2GRAY)
        # 3. Kontrastı patlat (Yazılar simsiyah, arka plan bembeyaz)
        _, temiz_resim = cv2.threshold(gri, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        # --- OCR AYARLARI ---
        # Sadece rakamlar, noktalar ve boşlukları oku. PSM 6: Tablo düzenini koru
        ozel_ayar = r'--psm 6 -c tessedit_char_whitelist="0123456789. \n"'
        okunan_metin = pytesseract.image_to_string(temiz_resim, config=ozel_ayar)
        
        noktalar = metinden_koordinat_cikar(okunan_metin)
        
    if noktalar:
        st.success(f"Harika! Görüntüden {len(noktalar)} adet koordinat yüksek doğrulukla okundu.")
        with st.expander("Okunan Değerleri Kontrol Et"):
            for n in noktalar:
                st.write(f"Nokta: {n['no']} | Y: {n['y']} | X: {n['x']}")
    else:
        st.error("Görüntüden koordinat okunamadı. Resim çok bulanık olabilir. Lütfen manuel girişi deneyin.")

st.markdown("---")

# ALTERNATİF SEÇENEK: MANUEL GİRİŞ
st.subheader("2. Seçenek: Manuel Veri Girişi")
with st.expander("Görsel yüklemek istemiyorsanız buraya tıklayın"):
    st.info("Koordinatları 'Nokta No  Y  X' formatında, aralarında boşluk bırakarak alt alta yapıştırın.")
    manuel_metin = st.text_area("Koordinat Verileri:", height=150, placeholder="Örnek:\n1  507597.29  4136997.02\n2  507590.59  4136978.38")
    
    if st.button("Manuel Verileri Çevir"):
        noktalar = metinden_koordinat_cikar(manuel_metin)
        if noktalar:
            st.success(f"Manuel girişten {len(noktalar)} adet koordinat okundu.")
        else:
            st.error("Girdiğiniz format hatalı. Lütfen örnekteki gibi girdiğinizden emin olun.")

# --- İNDİRME BUTONU ---
if noktalar:
    st.markdown("### Sonuç Hazır!")
    dxf_verisi = dxf_metni_olustur(noktalar)
    
    st.download_button(
        label="📥 DXF Dosyasını İndir",
        data=dxf_verisi,
        file_name="proje_koordinatlari.dxf",
        mime="application/dxf"
    )
    st.caption("İndirdiğiniz dosyayı AutoCAD'de açtıktan sonra Z (Zoom) ve E (Extents) komutlarını uygulamayı unutmayın.")
