import os, json
from datetime import datetime, time
import pytz
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN      = "8659122854:AAHQFNc8QlUxfa5eZrGuMfKQhxWfDPd_ViY"
ADMIN_ID   = 462890262
TIMEZONE   = pytz.timezone("Asia/Tashkent")
ISH_VAQTI  = time(9, 0)
KECH_MIN   = 15
DATA_FILE  = "attendance.json"

XODIMLAR = {
    "mrsoipov":    "Soipov — Dizayner",
    "javohir381":  "Javohir — Marketolog",
    "jasurll":     "Jasur — Operator",
    "zerodj":      "Zero — Montaj",
    "lnozzaa":     "Nozima — SMM",
    "alimov224":   "Alimov — SMM",
    "abdulfarhod": "Abdulfarhod — SMM",
    "anvarov_501": "Anvarov — CEO",
}

def load():
    return json.load(open(DATA_FILE, encoding="utf-8")) if os.path.exists(DATA_FILE) else {}

def save(d):
    json.dump(d, open(DATA_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def now():   return datetime.now(TIMEZONE)
def today(): return now().strftime("%Y-%m-%d")
def ts(iso):
    try: return datetime.fromisoformat(iso).strftime("%H:%M")
    except: return "—"

def get_key(uname):
    ul = (uname or "").lower()
    for k in XODIMLAR:
        if k.lower() == ul: return k
    return None

def admin_kb():
    return ReplyKeyboardMarkup([[KeyboardButton("📊 Bugungi hisobot"), KeyboardButton("📋 Haftalik hisobot")]], resize_keyboard=True)

def xodim_kb():
    return ReplyKeyboardMarkup([[KeyboardButton("✅ Keldim"), KeyboardButton("🚪 Ketdim")]], resize_keyboard=True)

async def start(u: Update, _):
    uid, uname = u.effective_user.id, u.effective_user.username or ""
    if uid == ADMIN_ID:
        await u.message.reply_text("👑 Admin paneli — PM Pi Media\n\n📊 Bugungi hisobot\n📋 Haftalik hisobot", reply_markup=admin_kb())
    elif get_key(uname):
        ism = XODIMLAR[get_key(uname)]
        await u.message.reply_text(f"👋 Salom, {ism}!\n\n✅ Keldim — kelganingizda bosing\n🚪 Ketdim — ketayotganda bosing", reply_markup=xodim_kb())
    else:
        await u.message.reply_text("⛔ Siz tizimda yo'qsiz. Adminizga murojaat qiling.")

async def keldi(u: Update, ctx):
    uname = u.effective_user.username or ""
    key = get_key(uname)
    if not key:
        await u.message.reply_text("⛔ Siz ro'yxatda yo'qsiz."); return
    d, sana, ism, n = load(), today(), XODIMLAR[key], now()
    d.setdefault(sana, {}).setdefault(key, {"ism": ism})
    if d[sana][key].get("keldi"):
        await u.message.reply_text(f"ℹ️ Allaqachon belgilagansiz — {ts(d[sana][key]['keldi'])}"); return
    d[sana][key]["keldi"] = n.isoformat(); save(d)
    ish  = TIMEZONE.localize(datetime.combine(n.date(), ISH_VAQTI))
    kech = int((n - ish).total_seconds() / 60)
    if kech > KECH_MIN:
        await ctx.bot.send_message(ADMIN_ID, f"⚠️ Kech qoldi!\n👤 {ism}\n🕐 {n.strftime('%H:%M')}\n⏱ {kech} daqiqa kech")
        await u.message.reply_text(f"✅ Qayd etildi — {n.strftime('%H:%M')}\n⚠️ {kech} daqiqa kech qoldingiz.")
    else:
        await u.message.reply_text(f"✅ {ism}, kelgan vaqt: {n.strftime('%H:%M')} 👍")

async def ketdi(u: Update, ctx):
    uname = u.effective_user.username or ""
    key = get_key(uname)
    if not key:
        await u.message.reply_text("⛔ Siz ro'yxatda yo'qsiz."); return
    d, sana, ism, n = load(), today(), XODIMLAR[key], now()
    info = d.get(sana, {}).get(key, {})
    if not info.get("keldi"):
        await u.message.reply_text("⚠️ Avval ✅ Keldim ni bosing."); return
    if info.get("ketdi"):
        await u.message.reply_text("ℹ️ Allaqachon ketganingizni belgilagansiz."); return
    d[sana][key]["ketdi"] = n.isoformat(); save(d)
    mins = int((n - datetime.fromisoformat(info["keldi"])).total_seconds() / 60)
    s, m = divmod(mins, 60)
    await u.message.reply_text(f"🚪 Xayr, {ism}!\nKetgan vaqt: {n.strftime('%H:%M')}\nIsh vaqti: {s} soat {m} daqiqa")
    await ctx.bot.send_message(ADMIN_ID, f"📤 Ketdi: {ism}\n🕐 {n.strftime('%H:%M')}\n⏱ {s} soat {m} daqiqa")

async def hisobot_bugun(u: Update, _):
    if u.effective_user.id != ADMIN_ID: return
    d, sana = load(), today()
    kun  = d.get(sana, {})
    ish  = TIMEZONE.localize(datetime.combine(datetime.now(TIMEZONE).date(), ISH_VAQTI))
    matn = f"📊 Hisobot — {sana}\n{'─'*28}\n"
    kelgan, kelmagan = [], []
    for key, ism in XODIMLAR.items():
        info = kun.get(key, {})
        if info.get("keldi"):
            kech = int((datetime.fromisoformat(info["keldi"]) - ish).total_seconds() / 60)
            st   = f"⚠️ +{kech} daq" if kech > KECH_MIN else "✅"
            ket  = ts(info["ketdi"]) if info.get("ketdi") else "hali ishda"
            kelgan.append(f"👤 {ism} {st}\n   {ts(info['keldi'])} → {ket}")
        else:
            kelmagan.append(f"❌ {ism}")
    if kelgan:   matn += "\n".join(kelgan)
    if kelmagan: matn += "\n\n⛔ Kelmaganlar:\n" + "\n".join(kelmagan)
    if not kelgan and not kelmagan: matn += "Hali hech kim belgilamagan."
    await u.message.reply_text(matn, reply_markup=admin_kb())

async def hisobot_hafta(u: Update, _):
    if u.effective_user.id != ADMIN_ID: return
    d = load()
    if not d:
        await u.message.reply_text("📋 Ma'lumot yo'q.", reply_markup=admin_kb()); return
    matn = "📋 Haftalik hisobot\n" + "─"*28 + "\n"
    for sana in sorted(d.keys(), reverse=True)[:7]:
        matn += f"\n📅 {sana}\n"
        for key, ism in XODIMLAR.items():
            info = d[sana].get(key, {})
            ico  = "✅" if info.get("keldi") else "❌"
            matn += f"  {ico} {ism}: {ts(info.get('keldi',''))} → {ts(info.get('ketdi',''))}\n"
    await u.message.reply_text(matn, reply_markup=admin_kb())

async def kelmagan_tekshir(ctx):
    d   = load()
    kun = d.get(today(), {})
    kel = [ism for k, ism in XODIMLAR.items() if not kun.get(k, {}).get("keldi")]
    if kel:
        await ctx.bot.send_message(ADMIN_ID, "⚠️ Soat 10:00 — kelmagan xodimlar:\n" + "\n".join(f"❌ {i}" for i in kel))

async def router(u: Update, ctx):
    t = u.message.text or ""
    if   t == "✅ Keldim":           await keldi(u, ctx)
    elif t == "🚪 Ketdim":           await ketdi(u, ctx)
    elif t == "📊 Bugungi hisobot":  await hisobot_bugun(u, ctx)
    elif t == "📋 Haftalik hisobot": await hisobot_hafta(u, ctx)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))
    app.job_queue.run_daily(kelmagan_tekshir, time=time(10, 0, tzinfo=TIMEZONE))
    print("✅ PM Pi Media HR Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
