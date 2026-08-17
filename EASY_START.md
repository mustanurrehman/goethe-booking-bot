# 🚀 Goethe Booking Bot — EASY START (Bina hosting paye)

Ye teen tarike hain. **Sabse easy = Option 2 (GitHub Actions — 100% free, koi hosting nahi).**

---

## Option 1 — Is PC par chalao (limited, www.goethe.de blocked)

Aapke PC ka IP Goethe ko `www.goethe.de` par block karta hai, isliye **B1 booking form nahi khulega** yahan.
Sirf login page (`my.goethe.de`) khulta hai.

```
python booking_helper.py --config config.csv
```

---

## Option 2 — GitHub Actions (BEST — free, clean IP) ✅

GitHub ke cloud runners ka IP alag hota hai — Goethe unko block NAHI karta.

### Step-by-step (5 min):

**1. GitHub repo banao**
- Open https://github.com/new
- Repo name: `goethe-booking-bot`
- **Public** rakho (free)
- "Create repository"

**2. Is folder ko repo mein push karo**

Windows PowerShell:
```powershell
cd C:\Users\DELL\Downloads\goethe-booking-bot-main\goethe-booking-bot-main
git init
git add -A
git commit -m "goethe bot"
git branch -M main
git remote add origin https://github.com/AAPKA_USERNAME/goethe-booking-bot.git
git push -u origin main
```

**3. Apni student config secret mein daalo**
- GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
- Name: `CONFIG_CSV`
- Value: apne **config.csv** ka **poora content** (header row samet)

```csv
name,email,password,level,city,dob,booking_datetime
Ali Ali,hamdamstyle@gmail.com,MERA_PASSWORD,B1,Lahore,15.08.2000,2026-09-14T09:00:00
```

**4. Bot chalao**
- GitHub repo → **Actions** tab → **Book Goethe Slot** → **Run workflow**
- Bot GitHub runner par chalta hai, slot try karta hai
- Result neeche steps mein dikhta hai (secrets/log)

### Scheduled (auto every ~10 min):
`book-slot.yml` mein already `*/10 * * * *` hai. Apne booking window per edit kar sakte ho
(e.g. slot 09:00 khulega to 08:55–09:05 par baar-baar).

---

## Option 3 — Render (free web, dashboard ke saath)

Agar aapko web dashboard bhi chahiye (students list, start/stop button):
- https://dashboard.render.com → New → Web Service → GitHub repo
- render.yaml already ready hai → Deploy
- Render free tier: 750 hrs/month (kaafi)

---

## Important:
- **password** facing in config.csv is your student's Goethe login password. GitHub secret mein rakho, repo mein plain nahi.
- Bot ka login `my.goethe.de`/`login.goethe.de` par hota hai — GitHub runner se reachable hai.
- Agar `www.goethe.de` runner par bhi block ho to log mein `Forbidden` dikhega — tab Railway/Render ka clean IP chahiye.