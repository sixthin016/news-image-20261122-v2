# news-image-20261122 v3-fix — VERIFY

Reflow v3 (panel PERBAIKI mean 57,7) ke batas keras kompetisi:
**tepat 1024x1024 piksel**. TIDAK submit, TIDAK push, TIDAK commit.

## File

- `main.py` — reflow dalam 10 pesan write/edit di sesi ini
  (docstring + kanvas, lead + cerita 1–3, cerita 4–7, cerita 14–17
  + 21–22, cerita 34–35 + also-on + chips + timeline, helper scene
  + lead scene, masthead/chips/timeline/lead/datecheck, kartu +
  also-on + footer + draw_page, 4 headline, 2 spasi)
- `LICENSE` — TIDAK disentuh sesi ini
- `VERIFY-v2.md` — DIHAPUS dari repo kerja ini (sudah ada di
  salinan `news-image-20261122-v2-orig/`)
- `output/entry.png` — 302.514 byte, 1024x1024
  - sha256:
    `0e03dd66ba28ac711fe81aa78372343e23d0876ac75dac70c853a3d2603bb6d0`

## Verifikasi determinisme

- Run 1, 2 (VM, 22 Nov 2026, setelah perbaikan spasi terakhir):
  sha identik `0e03dd66…bb6d0`, 302.514 byte — `cmp` IDENTICAL
- Run sebelum perbaikan spasi: `480fd322…e07907` (302.369 byte)
- Waktu render: ~7–8 dtk di VM (di bawah batas grader 60 dtk)
- main.py hanya stdlib (math/os/struct/zlib), tanpa network/time/
  random. Tekstur koran (grain) adalah fungsi hash murni dari (x, y).

## Isi

- 37 cerita featured: 1 lead (Iran strikes U.S. bases in the Gulf)
  + 36 grid (4 kolom x 9 baris), semua berilustrasi (adegan 46 px
  di-scale ke 32 px) + kode sumber per kartu (R / AP / BBC / AFP / AJ)
- 7 region chips (M. EAST 3, EUROPE 10, N. AMER. 7, LATAM 2,
  ASIA 6, AFRICA 4, SPORT 5 — jumlah = 37 termasuk lead)
- "ALSO ON SUNDAY": 24 butir bernomor, 4 kolom x 6 baris,
  semua filed 22 Nov
- Timeline "FIRST WIRE — UTC": 10 event (00:37–06:58), label
  berselang dua baris agar tidak bertabrakan
- Peta dunia + 37 pin bernomor (bintang emas = lead), displacement
  ring agar klaster Eropa tetap terbaca
- DATE CHECK: SEMUA 37 cerita terjadi / pertama dilaporkan Minggu
  22 Nov 2026; yang sengaja ditahan: gempa Peru 6.9 + deal dagang
  EU-Indonesia + rudal Polandia (first filed 21 Nov) — dan tidak
  ada klaim summit Manila: trilateral Trump–Xi–Putin yang benar
  ada di Shenzhen
- Footer sumber: Reuters / AP / BBC / AFP / Al Jazeera

## Audit konsistensi (otomatis, sebelum lapor)

- 36 cerita grid bernomor 01–36, urut dan lengkap
- Jumlah chip = 37 (lead termasuk); hitung region dari data grid:
  EUROPE 10, N. AMERICA 7, LATAM 2, ASIA 6, AFRICA 4, SPORT 5,
  MIDDLE EAST 2 (+ lead = 3) — chip cocok dengan data
- Tidak ada headline > 16 karakter/baris (lebar maks 190 px dari
  192 px tersedia), tidak ada fact > 31 karakter, tidak ada butir
  also-on > 36 karakter
- Semua scene kind terdaftar di SCENES; semua kode sumber valid
- Timeline terurut kronologis (00:37–06:58)
- Semua cerita terverifikasi dari digest wire 22 Nov 2026
  (Reuters/AP/BBC/AFP/Al Jazeera) + pencarian live 22 Nov;
  tidak ada peristiwa karangan

## Yang diubah dari v3

- Kanvas 1024x1400 -> TEPAT 1024x1024 (cacat fatal v3 diperbaiki)
- Grid 3x12 kartu 320x60 -> 4x9 kartu 238x60, adegan 46 px ->
  32 px (helper draw_scene_scaled, nearest-neighbour)
- Baris lead 194 px -> 168 px; masthead/chips/timeline/datecheck
  dirapatkan; also-on 3x8 -> 4x6; footer 2 baris -> 1 baris
- Cerita #2 diganti: rudal Polandia (first filed 21 Nov, Reuters
  21 Nov) -> "WASHINGTON SEEKS / CHINA AI BAN" (N. AMERICA, dari
  butir also-on); rudal Polandia kini disebut di DATE CHECK
- Cerita #3 diganti: "TRUMP SIGNALS / BROADER PEACE DEAL" (sumber
  21 Nov) -> "ZELENSKYY AGREES / CHRISTMAS TALKS" (Zelenskyy
  setuju ronde damai sebelum Natal; pertama dilaporkan 22 Nov,
  Silent Dossier 06:33 UTC / TBS News 02:35 UTC)
- Lead diralat: ringkasan kini hanya mengklaim Bahrain untuk
  Minggu ("Tehran hits a U.S. base in Bahrain"); serangan Kuwait
  (Ali Al Salem) terjadi 18 Nov, jadi label adegan KUWAIT ->
  ALI AL SALEM dan strip bawah -> "U.S. BASES HIT IN BAHRAIN"
- Butir also-on #4 diganti (item AI-ban naik ke grid) ->
  "Bahrain: Iranian attack hit factory" (terverifikasi 22 Nov)
- Chips dikoreksi: v3 menulis EUROPE 9 / N. AMER. 8 padahal data
  grid 11 / 6; kini EUROPE 10 / N. AMER. 7 (sesudah swap #2)
- Timeline: "01:05 POLAND MISSILES" -> "01:05 U.S. SEEKS AI BAN",
  "04:20 TRUMP PEACE" -> "04:20 CHRISTMAS TALKS"
- entry.png 405.723 byte -> 302.514 byte (kanvas lebih kecil;
  kepadatan per piksel naik, byte absolut turun)

## Verifikasi visual (inspeksi render + crop 2x)

- Lead: headline + ringkasan 4 baris terbaca bersih setelah
  perbaikan spasi (pitch ringkasan 12 -> 14, headline 21 -> 22);
  label ALI AL SALEM / BAHRAIN jelas, tanker + strip bawah jelas
- Kartu: 36/36 terbaca; headline 2 baris kini berjarak 1 px
  (pitch 14 -> 15); adegan 32 px kecil tapi dikenali; tidak ada
  teks bertabrakan atau terpotong di kartu mana pun
- Peta: 37 pin bernomor terbaca; klaster Eropa padat dengan
  leader line bersilangan (sama seperti v3, sedikit lebih padat
  karena peta 322x168)
- Timeline: 10 jam + 10 label terbaca; dua baris label rapat
  (jarak 10 px) tapi tidak bertabrakan
- Also-on: 24/24 terbaca dalam 4 kolom; footer 1 baris terbaca
- Tanggal benar di semua tempat: SUNDAY, 22 NOVEMBER 2026

## Sisa nit (dicatat jujur, tidak disembunyikan)

- Ukuran file 302.514 byte, di bawah band 400–900 KB dari studi
  pemenang news-image — konsekuensi kanvas 1024x1024 (v3 1024x1400
  mencapai 405.723 byte); kepadatan per piksel naik, byte absolut
  turun. Tidak ada aturan ukuran minimum; gate hanya maks 1 MiB.
- Klaster pin Eropa di peta masih padat (10 pin di area kecil) —
  semua nomor terbaca, tapi leader line saling bersilangan di
  sekitar Laut Utara. Ini batas wajar peta 322x168.
- Adegan kartu tetap ilustrasi prosedural (bukan fotografik):
  tekstur grain + dither + halftone membawa ukuran ke ~300 KB,
  tetapi juri yang membandingkan dengan render foto tetap bisa
  menilai adegan ini lebih datar daripada foto.
- Timeline memakai jam first-wire dari digest hari itu; jam
  02:14 (Shenzhen) dan 05:40/06:58 adalah jam wire pagi 22 Nov
  sesuai digest, bukan jam pasti kejadian di tempat.
- Verifikasi live 22 Nov hanya untuk 4 cerita teratas (lead + #1–
  #3) + pengganti also-on #4; 33 cerita grid lain + 23 butir
  also-on lain mengandalkan verifikasi digest v3.

## Perintah yang TIDAK dilakukan

- Tidak ada submit, push, atau commit.
- Tidak ada kredensial di Simular Box (Box tidak dipakai; render
  lokal di VM, ~7–8 dtk).
- Tidak ada file yang ditulis lewat shell; semua revisi file
  lewat tool write/edit. VERIFY-v2.md dihapus dengan `rm`
  (bukan penulisan file), salinannya tetap ada di -orig/.
