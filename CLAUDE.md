# haber-bulteni – kurallar

- Sayfa `python3 build.py data/daily/<YYYY-MM-DD>.json` ile üretilir. index.html'i elle düzenleme.
- `build.py` içindeki `render_internships()` fonksiyonu, Fırsat Etkinlikleri kutusunun hemen altında "Staj İlanları – İnşaat Mühendisliği" bölümünü `data/internships.json` dosyasından üretir. Bu bölümü ve fonksiyon çağrısını silme veya kaldırma.
- `data/internships.json` dosyası 3 günde bir çalışan ayrı bir staj tarama göreviyle güncellenir. Günlük bülten görevi bu dosyayı değiştirmez.
- Commit etmeden önce `__pycache__` klasörünü sil. Doğrudan `main` dalına push et (önce `git pull --rebase`).
