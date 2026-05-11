import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
import webbrowser  # Tarayıcı açmak için ekledik


# ================= 1. VERİTABANI KURULUMU =================
def sifre_hashle(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()


def veritabani_kur():
    conn = sqlite3.connect("otomasyon_ctk.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kullanicilar
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     kullanici_adi
                     TEXT
                     UNIQUE,
                     sifre_hash
                     TEXT,
                     rol
                     TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ogrenciler
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     ad
                     TEXT,
                     soyad
                     TEXT,
                     okul_no
                     INTEGER
                     UNIQUE
                 )''')

    # Varsayılan Admin Hesabı (Gizli olarak oluşturulur)
    c.execute("SELECT * FROM kullanicilar WHERE kullanici_adi='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO kullanicilar (kullanici_adi, sifre_hash, rol) VALUES (?, ?, ?)",
                  ('admin', sifre_hashle('1234'), 'admin'))

    conn.commit()
    conn.close()


veritabani_kur()

# ================= 2. ANA UYGULAMA (CUSTOMTKINTER) =================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class OtomasyonApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎓 Öğrenci Otomasyonu PRO (CustomTkinter)")
        self.geometry("1100x700")
        self.minsize(950, 600)

        # Oturum Bilgileri
        self.aktif_kullanici = None
        self.aktif_rol = None
        self.secili_ogrenci_id = None
        self.secili_kullanici_id = None

        # Ana Taşıyıcılar (Frame)
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dashboard_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.login_ekranini_olustur()
        self.dashboard_ekranini_olustur()

        self.sayfa_goster("login")

    def sayfa_goster(self, sayfa):
        if sayfa == "login":
            self.dashboard_frame.pack_forget()
            self.login_frame.pack(fill="both", expand=True)
        elif sayfa == "dashboard":
            self.login_frame.pack_forget()
            self.lbl_karsilama.configure(text=f"👋 Hoşgeldin, {self.aktif_kullanici} ({self.aktif_rol.upper()})")

            if self.aktif_rol == "admin":
                self.sol_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
                try:
                    self.sekmeler.add("Kullanıcı Yetkilendirme")
                except:
                    pass
                self.kullanici_tablosunu_yenile()
            else:
                self.sol_panel.grid_forget()
                try:
                    self.sekmeler.delete("Kullanıcı Yetkilendirme")
                except:
                    pass

            self.ogrenci_tablosunu_yenile()
            self.dashboard_frame.pack(fill="both", expand=True)

    # ------------------ GİRİŞ EKRANI ------------------
    def login_ekranini_olustur(self):
        merkez_frame = ctk.CTkFrame(self.login_frame, width=400, height=500, corner_radius=20)
        merkez_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(merkez_frame, text="Sisteme Giriş", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(40, 20))

        self.ent_kullanici = ctk.CTkEntry(merkez_frame, placeholder_text="Kullanıcı Adı", width=300, height=45)
        self.ent_kullanici.pack(pady=10)

        self.ent_sifre = ctk.CTkEntry(merkez_frame, placeholder_text="Şifre", width=300, height=45, show="*")
        self.ent_sifre.pack(pady=10)

        btn_giris = ctk.CTkButton(merkez_frame, text="🚀 Giriş Yap", width=300, height=45,
                                  font=ctk.CTkFont(weight="bold"), command=self.giris_yap)
        btn_giris.pack(pady=(20, 10))

        btn_kayit = ctk.CTkButton(merkez_frame, text="📝 Yeni Kayıt Ol", width=300, height=40, fg_color="transparent",
                                  border_width=1, command=self.kayit_ol)
        btn_kayit.pack(pady=5)

        # GOOGLE İLE GİRİŞ BUTONU
        btn_google = ctk.CTkButton(merkez_frame, text="G  Google ile Giriş Yap", width=300, height=40,
                                   fg_color="#DB4437", hover_color="#C13527", command=self.google_ile_giris)
        btn_google.pack(pady=(15, 40))

        # EKRANDAKİ ADMİN ŞİFRESİ YAZISI KALDIRILDI!

    def giris_yap(self):
        k_adi, sifre = self.ent_kullanici.get().strip(), self.ent_sifre.get().strip()
        conn = sqlite3.connect("otomasyon_ctk.db")
        c = conn.cursor()
        c.execute("SELECT rol FROM kullanicilar WHERE kullanici_adi=? AND sifre_hash=?", (k_adi, sifre_hashle(sifre)))
        user = c.fetchone()
        conn.close()

        if user:
            self.aktif_kullanici = k_adi
            self.aktif_rol = user[0]
            self.ent_kullanici.delete(0, 'end');
            self.ent_sifre.delete(0, 'end')
            self.sayfa_goster("dashboard")
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre yanlış!")

    def kayit_ol(self):
        k_adi, sifre = self.ent_kullanici.get().strip(), self.ent_sifre.get().strip()
        if not k_adi or not sifre:
            messagebox.showwarning("Uyarı", "Lütfen bilgileri doldurun.")
            return
        try:
            conn = sqlite3.connect("otomasyon_ctk.db")
            c = conn.cursor()
            c.execute("INSERT INTO kullanicilar (kullanici_adi, sifre_hash, rol) VALUES (?, ?, ?)",
                      (k_adi, sifre_hashle(sifre), 'user'))
            conn.commit();
            conn.close()
            messagebox.showinfo("Başarılı", "Kayıt olundu! Şimdi giriş yapabilirsiniz.")
            self.ent_sifre.delete(0, 'end')
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu kullanıcı adı zaten alınmış!")

    def google_ile_giris(self):
        # 1. Gerçek tarayıcıyı açarak Google Giriş sayfasına yönlendirir
        webbrowser.open("https://accounts.google.com/signin")

        # 2. Tarayıcı işlemi bittikten sonra sisteme giriş yapabilmesi için mail adresi istenir
        dialog = ctk.CTkInputDialog(
            text="Tarayıcıda giriş işlemini tamamladıysanız,\nGoogle hesabınızı (Gmail) buraya giriniz:",
            title="Google Doğrulama")
        gmail = dialog.get_input()

        if gmail and "@gmail.com" in gmail:
            k_adi = gmail
            conn = sqlite3.connect("otomasyon_ctk.db")
            c = conn.cursor()
            c.execute("SELECT rol FROM kullanicilar WHERE kullanici_adi=?", (k_adi,))
            user = c.fetchone()

            if not user:
                c.execute("INSERT INTO kullanicilar (kullanici_adi, sifre_hash, rol) VALUES (?, ?, ?)",
                          (k_adi, 'GOOGLE_OAUTH', 'user'))
                conn.commit()
                self.aktif_rol = 'user'
            else:
                self.aktif_rol = user[0]
            conn.close()

            self.aktif_kullanici = k_adi
            messagebox.showinfo("Google Auth", f"{gmail} hesabıyla başarıyla giriş yapıldı!")
            self.sayfa_goster("dashboard")
        elif gmail:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir gmail adresi giriniz.")

    # ------------------ PANEL (DASHBOARD) EKRANI ------------------
    def dashboard_ekranini_olustur(self):
        # 1. ÜST BAR
        topbar = ctk.CTkFrame(self.dashboard_frame, height=60, corner_radius=0)
        topbar.pack(fill="x")
        self.lbl_karsilama = ctk.CTkLabel(topbar, text="👋 Hoşgeldin", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_karsilama.pack(side="left", padx=20, pady=15)

        btn_cikis = ctk.CTkButton(topbar, text="Çıkış Yap", fg_color="#c0392b", hover_color="#e74c3c", width=100,
                                  command=self.cikis_yap)
        btn_cikis.pack(side="right", padx=20)

        # 2. SEKMELER
        self.sekmeler = ctk.CTkTabview(self.dashboard_frame)
        self.sekmeler.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tab_ogrenci = self.sekmeler.add("Öğrenci Veritabanı")

        tab_ogrenci.grid_columnconfigure(1, weight=1)
        tab_ogrenci.grid_rowconfigure(0, weight=1)

        # --- SOL PANEL (Yönetim Formu) ---
        self.sol_panel = ctk.CTkFrame(tab_ogrenci, width=300, corner_radius=15)
        self.sol_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(self.sol_panel, text="Kayıt İşlemleri", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        self.ent_ad = ctk.CTkEntry(self.sol_panel, placeholder_text="Öğrenci Adı", width=250, height=40)
        self.ent_ad.pack(pady=10)
        self.ent_soyad = ctk.CTkEntry(self.sol_panel, placeholder_text="Öğrenci Soyadı", width=250, height=40)
        self.ent_soyad.pack(pady=10)
        self.ent_no = ctk.CTkEntry(self.sol_panel, placeholder_text="Okul Numarası", width=250, height=40)
        self.ent_no.pack(pady=10)

        self.btn_ekle = ctk.CTkButton(self.sol_panel, text="➕ Ekle", width=250, height=40, command=self.ogrenci_ekle)
        self.btn_ekle.pack(pady=(20, 5))

        self.btn_guncelle = ctk.CTkButton(self.sol_panel, text="💾 Güncelle", width=250, height=40, fg_color="#d68910",
                                          hover_color="#f39c12", state="disabled", command=self.ogrenci_guncelle)
        self.btn_guncelle.pack(pady=5)

        self.btn_sil = ctk.CTkButton(self.sol_panel, text="🗑️ Sil", width=250, height=40, fg_color="#c0392b",
                                     hover_color="#e74c3c", state="disabled", command=self.ogrenci_sil)
        self.btn_sil.pack(pady=5)

        ctk.CTkButton(self.sol_panel, text="İptal / Temizle", width=250, height=35, fg_color="transparent",
                      border_width=1, command=self.form_temizle).pack(pady=15)

        # --- SAĞ PANEL (Tablo ve Arama) ---
        sag_panel = ctk.CTkFrame(tab_ogrenci, fg_color="transparent")
        sag_panel.grid(row=0, column=1, sticky="nsew", pady=20)

        self.ent_arama = ctk.CTkEntry(sag_panel, placeholder_text="🔍 İsim veya No ile Ara...", height=40)
        self.ent_arama.pack(fill="x", pady=(0, 15))
        self.ent_arama.bind("<KeyRelease>", self.arama_yap)

        # Treeview Stili
        stil = ttk.Style()
        stil.theme_use("default")
        stil.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=35,
                       borderwidth=0)
        stil.configure("Treeview.Heading", background="#1f1f1f", foreground="white", font=('Helvetica', 11, 'bold'))
        stil.map("Treeview", background=[('selected', '#1f538d')])

        self.tablo_frame = ctk.CTkFrame(sag_panel)
        self.tablo_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.tablo_frame)
        scrollbar.pack(side="right", fill="y")

        self.tablo = ttk.Treeview(self.tablo_frame, columns=("ID", "Ad", "Soyad", "No"), show='headings',
                                  yscrollcommand=scrollbar.set)
        self.tablo.heading("ID", text="ID");
        self.tablo.heading("Ad", text="AD");
        self.tablo.heading("Soyad", text="SOYAD");
        self.tablo.heading("No", text="OKUL NO")
        self.tablo.column("ID", width=50, anchor="center");
        self.tablo.column("No", width=100, anchor="center")
        self.tablo.pack(fill="both", expand=True)
        scrollbar.config(command=self.tablo.yview)

        self.tablo.bind("<<TreeviewSelect>>", self.tablodan_secim)

        ctk.CTkButton(sag_panel, text="📊 Süslü Excel Raporu İndir", height=45, fg_color="#27ae60",
                      hover_color="#2ecc71", font=ctk.CTkFont(weight="bold"), command=self.excel_aktar).pack(fill="x",
                                                                                                             pady=(15,
                                                                                                                   0))

        # --- YETKİ (KULLANICI) YÖNETİMİ SEKMESİ ---
        self.kullanici_tablosu = ttk.Treeview(self.dashboard_frame, columns=("ID", "Kullanici", "Rol"), show='headings')
        self.kullanici_tablosu.heading("ID", text="ID");
        self.kullanici_tablosu.heading("Kullanici", text="KULLANICI ADI");
        self.kullanici_tablosu.heading("Rol", text="MEVCUT ROL")
        self.kullanici_tablosu.bind("<<TreeviewSelect>>", self.kullanici_secim)

    def cikis_yap(self):
        self.aktif_kullanici = None
        self.aktif_rol = None
        self.sayfa_goster("login")

    # ------------------ CRUD İŞLEMLERİ ------------------
    def ogrenci_tablosunu_yenile(self, arama=""):
        for item in self.tablo.get_children(): self.tablo.delete(item)
        conn = sqlite3.connect("otomasyon_ctk.db")
        c = conn.cursor()
        if arama:
            terim = f"%{arama}%"
            c.execute("SELECT * FROM ogrenciler WHERE ad LIKE ? OR soyad LIKE ? OR okul_no LIKE ?",
                      (terim, terim, terim))
        else:
            c.execute("SELECT * FROM ogrenciler")

        for ogr in c.fetchall():
            self.tablo.insert("", "end", values=(ogr[0], ogr[1], ogr[2], ogr[3]))
        conn.close()

    def arama_yap(self, event):
        self.ogrenci_tablosunu_yenile(self.ent_arama.get())

    def tablodan_secim(self, event):
        secilenler = self.tablo.selection()
        if secilenler and self.aktif_rol == "admin":
            veri = self.tablo.item(secilenler[0], 'values')
            self.secili_ogrenci_id = veri[0]
            self.ent_ad.delete(0, 'end');
            self.ent_ad.insert(0, veri[1])
            self.ent_soyad.delete(0, 'end');
            self.ent_soyad.insert(0, veri[2])
            self.ent_no.delete(0, 'end');
            self.ent_no.insert(0, veri[3])

            self.btn_ekle.configure(state="disabled")
            self.btn_guncelle.configure(state="normal")
            self.btn_sil.configure(state="normal")

    def ogrenci_ekle(self):
        ad, soyad, no = self.ent_ad.get().strip(), self.ent_soyad.get().strip(), self.ent_no.get().strip()
        if ad and soyad and no.isdigit():
            try:
                conn = sqlite3.connect("otomasyon_ctk.db")
                c = conn.cursor()
                c.execute("INSERT INTO ogrenciler (ad, soyad, okul_no) VALUES (?, ?, ?)",
                          (ad.title(), soyad.upper(), int(no)))
                conn.commit();
                conn.close()
                self.form_temizle()
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu numara sistemde var!")
        else:
            messagebox.showwarning("Uyarı", "Eksik veya hatalı bilgi (No rakam olmalı).")

    def ogrenci_guncelle(self):
        ad, soyad, no = self.ent_ad.get().strip(), self.ent_soyad.get().strip(), self.ent_no.get().strip()
        if self.secili_ogrenci_id and ad and soyad and no.isdigit():
            conn = sqlite3.connect("otomasyon_ctk.db")
            c = conn.cursor()
            c.execute("UPDATE ogrenciler SET ad=?, soyad=?, okul_no=? WHERE id=?",
                      (ad.title(), soyad.upper(), int(no), self.secili_ogrenci_id))
            conn.commit();
            conn.close()
            self.form_temizle()

    def ogrenci_sil(self):
        if self.secili_ogrenci_id and messagebox.askyesno("Onay", "Silmek istediğinize emin misiniz?"):
            conn = sqlite3.connect("otomasyon_ctk.db")
            c = conn.cursor()
            c.execute("DELETE FROM ogrenciler WHERE id=?", (self.secili_ogrenci_id,))
            conn.commit();
            conn.close()
            self.form_temizle()

    def form_temizle(self):
        self.ent_ad.delete(0, 'end');
        self.ent_soyad.delete(0, 'end');
        self.ent_no.delete(0, 'end')
        self.secili_ogrenci_id = None
        for item in self.tablo.selection(): self.tablo.selection_remove(item)
        self.btn_ekle.configure(state="normal")
        self.btn_guncelle.configure(state="disabled")
        self.btn_sil.configure(state="disabled")
        self.ogrenci_tablosunu_yenile()

    # ------------------ KULLANICI / YETKİ YÖNETİMİ ------------------
    def kullanici_tablosunu_yenile(self):
        tab = self.sekmeler.tab("Kullanıcı Yetkilendirme")
        for widget in tab.winfo_children(): widget.destroy()

        ctk.CTkLabel(tab, text="Kullanıcı Seçip Yetkisini Değiştirin", font=("Helvetica", 14)).pack(pady=10)

        self.kullanici_tablosu = ttk.Treeview(tab, columns=("ID", "Kullanici", "Rol"), show='headings')
        self.kullanici_tablosu.heading("ID", text="ID");
        self.kullanici_tablosu.heading("Kullanici", text="KULLANICI ADI");
        self.kullanici_tablosu.heading("Rol", text="MEVCUT ROL")
        self.kullanici_tablosu.pack(fill="both", expand=True, padx=20, pady=10)
        self.kullanici_tablosu.bind("<<TreeviewSelect>>", self.kullanici_secim)

        self.btn_yetki = ctk.CTkButton(tab, text="Yetkiyi Değiştir (Admin <-> User)", height=40, state="disabled",
                                       command=self.yetki_degistir)
        self.btn_yetki.pack(pady=20)

        conn = sqlite3.connect("otomasyon_ctk.db")
        c = conn.cursor()
        c.execute("SELECT id, kullanici_adi, rol FROM kullanicilar")
        for k in c.fetchall(): self.kullanici_tablosu.insert("", "end", values=(k[0], k[1], k[2]))
        conn.close()

    def kullanici_secim(self, event):
        secilenler = self.kullanici_tablosu.selection()
        if secilenler:
            veri = self.kullanici_tablosu.item(secilenler[0], 'values')
            self.secili_kullanici_id = veri[0]
            if veri[1] == self.aktif_kullanici:
                self.btn_yetki.configure(state="disabled")
            else:
                self.btn_yetki.configure(state="normal")

    def yetki_degistir(self):
        if self.secili_kullanici_id:
            conn = sqlite3.connect("otomasyon_ctk.db")
            c = conn.cursor()
            c.execute("SELECT rol FROM kullanicilar WHERE id=?", (self.secili_kullanici_id,))
            mevcut_rol = c.fetchone()[0]
            yeni_rol = "admin" if mevcut_rol == "user" else "user"

            c.execute("UPDATE kullanicilar SET rol=? WHERE id=?", (yeni_rol, self.secili_kullanici_id))
            conn.commit();
            conn.close()
            self.btn_yetki.configure(state="disabled")
            self.kullanici_tablosunu_yenile()

    # ------------------ EXCEL MOTORU ------------------
    def excel_aktar(self):
        conn = sqlite3.connect("otomasyon_ctk.db")
        c = conn.cursor()
        c.execute("SELECT ad, soyad, okul_no FROM ogrenciler")
        veriler = c.fetchall()
        conn.close()

        if not veriler:
            messagebox.showerror("Hata", "Dışa aktarılacak veri yok!")
            return

        dosya_adi = "Ogrenci_Raporu_CTk.xlsx"
        try:
            writer = pd.ExcelWriter(dosya_adi, engine='xlsxwriter')
            workbook = writer.book
            worksheet = workbook.add_worksheet('Kayıtlar')
            writer.sheets['Kayıtlar'] = worksheet

            baslik_formati = workbook.add_format(
                {'bold': True, 'font_size': 18, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#1f497d',
                 'font_color': 'white', 'border': 1})
            worksheet.merge_range('A1:C2', '🎓 CUSTOMTKINTER ÖĞRENCİ RAPORU', baslik_formati)
            worksheet.write('A3', f'Rapor Tarihi: {datetime.now().strftime("%d.%m.%Y - %H:%M")}')
            worksheet.write('C3', f'Toplam Kayıt: {len(veriler)}')

            for r_num, r_data in enumerate(veriler): worksheet.write_row(r_num + 4, 0, list(r_data))
            worksheet.add_table(3, 0, len(veriler) + 3, 2,
                                {'data': [list(v) for v in veriler], 'style': 'Table Style Medium 9',
                                 'columns': [{'header': 'Öğrenci Adı'}, {'header': 'Öğrenci Soyadı'},
                                             {'header': 'Okul Numarası'}]})
            worksheet.set_column('A:B', 25, workbook.add_format({'align': 'center'}))
            worksheet.set_column('C:C', 18, workbook.add_format({'align': 'center'}))
            writer.close()
            messagebox.showinfo("Harika!", f"Süslü Excel dosyası oluşturuldu:\n{dosya_adi}")
        except Exception as ex:
            messagebox.showerror("Hata", f"Dosya açık olabilir:\n{ex}")


if __name__ == "__main__":
    app = OtomasyonApp()
    app.mainloop()
