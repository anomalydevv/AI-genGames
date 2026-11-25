# Global Rules

## Kesin Kural

- Kullanıcının dediklerinin asla dışına çıkma. Sadece isteneni yap; test bile yapma. Dediğimi ekle, yeter.

## Çalışma Tarzı

- Hızlı ol. Gereksiz test, doğrulama veya keşif yapma. "Şuna X ekle" dendiğinde planı kısa tut, doğrudan özelliği ekle. Testleri sadece kullanıcı isterse veya gerçekten riskli bir değişiklikse çalıştır.
- Modüler kod yaz. God class/sınıf yapma. Her kodu doğru sınıfa, doğru dosyaya yaz; görevleri ve sorumlulukları karıştırma.
- Her projede, kullanıcı söylemeden, proje kök dizininde `opencode.md` oluştur ve güncel tut. İçine yapılan işleri kısa maddeler halinde kaydet: görev, dokunulan dosyalar, durum, sonraki adımlar. Bağlam dolarsa veya yeni oturumda önce `opencode.md` okuyup özetle devam et.
- Yıkıcı/toplu silme işlemlerinde hız kuralı geçersizdir: önce tam kapsamı (silinecek her servis/klasör/script) listele, kullanıcıdan onay al ve işlemden önce yerel/yedeğini al. "Temizle" veya "kodları sil" gibi ifadeleri asla "tüm oyunu sil" diye yorumlama; belirsizse sor.

## Hız Protokolü (her görevde)

- Basit soru/tek dosya işi: doğrudan cevap ver veya tek işlem yap; keşif taraması yok, en fazla 2-3 araç çağrısı. "Önce inceleyeyim" diye ekstra okuma turu açma.
- Orta görev: en kısa yolu seç (mevcut bilgi/dosya); gereksiz grep/glob/tree, alt ajan, plan dosyası veya skill töreni yok. Üst sınır ~8 araç çağrısı.
- Basit görevlerde brainstorming/plan/TDD gibi süreç skill'lerini yükleme; sadece gerçekten çok adımlı veya riskli işlerde kullan.
- Doğrulama sadece kullanıcı isterse ya da yıkıcı/yayınlama/veri kaybı riski varsa yap. Aynı çıktıyı iki kez doğrulama.
- İstenen sonuç oluştuysa dur; ek temizlik, ekstra iyileştirme veya özet turu yapma.
- 2 dakikayı geçeceğini düşündüğün işlerde önce tek cümlelik plan + tahmini süre söyle; onay gelirse devam et.
- Yıkıcı işlem güvenliği her zaman hız kuralından önce gelir: kapsam onayı ve yedek atlanmaz.
