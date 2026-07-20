iClass NFC Version 3.0 — Phase 1
================================

Modul siap:
1. Login pengguna
2. Peranan Admin dan Pensyarah
3. Dashboard
4. User Management untuk Admin
5. Struktur placeholder untuk:
   - Class Management
   - Student Profile
   - NFC Attendance
   - Analytics Dashboard
   - Report & Export

Akaun demo:
Username: admin
Password: admin123

CARA JALANKAN DI WINDOWS
------------------------
1. Buka terminal di folder projek.
2. Cipta virtual environment:

   & "C:\Users\USER\.local\bin\python3.14.exe" -m venv .venv

3. Aktifkan:

   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1

4. Pasang library:

   python -m pip install -r requirements.txt

5. Jalankan:

   python app.py

6. Buka browser:

   http://127.0.0.1:5000

AKSES MELALUI IPAD DALAM WIFI SAMA
----------------------------------
Aplikasi sudah menggunakan host 0.0.0.0.
Cari IPv4 laptop melalui arahan:

   ipconfig

Kemudian buka di iPad:

   http://IP-LAPTOP:5000

Contoh:

   http://192.168.0.105:5000

DEPLOY KE RENDER
----------------
1. Upload semua fail ke GitHub.
2. Di Render, pilih New Web Service.
3. Sambung repository GitHub.
4. Build Command:

   pip install -r requirements.txt

5. Start Command:

   gunicorn app:app

6. Deploy.

NOTA KESELAMATAN
----------------
- Tukar kata laluan admin sebelum penggunaan sebenar.
- Gunakan SECRET_KEY melalui environment variable.
- SQLite sesuai untuk demo. PostgreSQL lebih sesuai untuk ramai pengguna.
