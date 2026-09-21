#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سنّي-CLI — نواة منصة الحرفيين من الترمينال (بدون تطبيق)
الاستعمال: python3 sanni_cli.py <أمر> [خيارات]

الأوامر:
  add <اسم> <هاتف> <تخصص> <حي> <وصف> <سعر>   → تسجيل طلب جديد
  list [--today]                              → عرض الطلبات المفتوحة
  assign <رقم_الطلب> <اسم_الفني>              → إسناد طلب لفني
  done <رقم_الطلب>                            → إتمام الطلب وحساب العمولة
  tech add <اسم> <هاتف> <تخصص>                → تسجيل فني جديد
  stats                                       → إحصائيات اليوم/الشهر
  post <رقم_الطلب>                            → نص جاهز للنشر على فيسبوك
"""
import sqlite3, sys, datetime, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sanni.db")
COMMISSION = 0.10  # عمولة 10%

def db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT, spec TEXT, hood TEXT,
        desc TEXT, price REAL, status TEXT DEFAULT 'open',
        tech TEXT, created TEXT, done TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS techs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT, spec TEXT, jobs INTEGER DEFAULT 0)""")
    return c

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1:]
    c = db()

    if cmd[0] == "add" and len(cmd) >= 7:
        c.execute("INSERT INTO orders(name,phone,spec,hood,desc,price,created) VALUES(?,?,?,?,?,?,?)",
                  (cmd[1], cmd[2], cmd[3], cmd[4], cmd[5], float(cmd[6]),
                   datetime.datetime.now().isoformat(timespec='minutes')))
        n = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        print(f"[OK] تم تسجيل الطلب رقم {n} — للنشر على فيسبوك: python3 sanni_cli.py post {n}")

    elif cmd[0] == "list":
        q = "SELECT * FROM orders WHERE status='open'" + \
            (" AND created LIKE date('now')||'%'" if "--today" in cmd else "")
        rows = c.execute(q).fetchall()
        print(f"{'#':<4}{'الحريف':<14}{'التخصص':<10}{'الحي':<10}{'السعر':<7}{'الفني'}")
        for r in rows:
            print(f"{r[0]:<4}{r[1]:<14}{r[3]:<10}{r[4]:<10}{r[6]:<7.0f}{r[8] or '-'}")
        if not rows:
            print("لا طلبات مفتوحة")

    elif cmd[0] == "assign" and len(cmd) == 3:
        c.execute("UPDATE orders SET tech=?, status='assigned' WHERE id=?", (cmd[2], cmd[1]))
        print(f"[OK] اسند الطلب {cmd[1]} الى {cmd[2]} — ابعث رقم هاتف الحريف على واتساب")

    elif cmd[0] == "done" and len(cmd) == 2:
        r = c.execute("SELECT price, tech FROM orders WHERE id=?", (cmd[1],)).fetchone()
        if not r:
            print("طلب غير موجود")
            return
        c.execute("UPDATE orders SET status='done', done=? WHERE id=?",
                  (datetime.datetime.now().isoformat(timespec='minutes'), cmd[1]))
        c.execute("UPDATE techs SET jobs=jobs+1 WHERE name=?", (r[1],))
        print(f"[OK] انجز الطلب {cmd[1]} | {r[0]:.0f} د.ت -> عمولتك {r[0]*COMMISSION:.1f} د.ت -> للفني {r[0]*(1-COMMISSION):.1f} د.ت")

    elif cmd[0] == "tech" and len(cmd) == 5 and cmd[1] == "add":
        c.execute("INSERT INTO techs(name,phone,spec) VALUES(?,?,?)", (cmd[2], cmd[3], cmd[4]))
        print(f"[OK] انضم الفني {cmd[2]} ({cmd[4]}) — ابعث له رابط مجموعة الواتساب")

    elif cmd[0] == "stats":
        t = c.execute("SELECT COUNT(*), SUM(price), SUM(price)*? FROM orders WHERE status='done' AND done LIKE date('now')||'%'", (COMMISSION,)).fetchone()
        m = c.execute("SELECT COUNT(*), SUM(price)*? FROM orders WHERE status='done' AND strftime('%Y-%m',done)=strftime('%Y-%m','now')", (COMMISSION,)).fetchone()
        print(f"اليوم: {t[0]} تدخلات | {t[1] or 0:.0f} د.ت | عمولتك {t[2] or 0:.1f} د.ت")
        print(f"الشهر: {m[0]} تدخلات | عمولتك {m[1] or 0:.1f} د.ت")

    elif cmd[0] == "post" and len(cmd) == 2:
        r = c.execute("SELECT * FROM orders WHERE id=?", (cmd[1],)).fetchone()
        if not r:
            print("طلب غير موجود")
            return
        print("--- انسخ هذا على صفحة فيسبوك ---")
        print(f"[مفتاح] مطلوب فني {r[3]} — {r[4]}")
        print(f"الوصف: {r[5]}")
        print(f"الاجرة المعروضة: {r[6]:.0f} د.ت | الموعد: {r[9][:10]}")
        print(f"الفنيين الموثقين فقط: ابعث 'مهتم' في تعليق + راسلنا خاصا برقم هاتفك")
        print(f"#سنّي #{r[3]} #تونس")

    else:
        print(__doc__)

    c.commit()
    c.close()

if __name__ == "__main__":
    main()
