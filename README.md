# دليل تفعيل Dynamic OG Preview لـ Grad Book

## المشكلة التي يحلها هذا التعديل
روبوتات المشاركة (Telegram, WhatsApp, Facebook, Discord, X…) **لا تنفذ JavaScript**.  
لذا كانت كل الدفاتر تُظهر نفس الصورة الافتراضية (`default-og.jpg`) عند المشاركة.

## الحل
**Supabase Edge Function** (`og-preview`) تعمل كـ proxy ذكي:
- **روبوت** ← ترجع HTML بـ OG tags ديناميكية (صورة الطالب + اسمه + كليته + سنته)
- **إنسان** ← redirect مباشر لـ `daftar.html?slug=SLUG`

---

## خطوات التنصيب

### 1. نشر الـ Edge Function

```bash
# في مجلد المشروع
supabase functions deploy og-preview
```

أو من لوحة Supabase:
1. افتح [Supabase Dashboard](https://supabase.com/dashboard)
2. اختر مشروعك (`lhixtovnrpkhzntbcmin`)
3. اذهب لـ **Edge Functions** ← **New Function**
4. اسم الـ Function: `og-preview`
5. الصق محتوى `supabase/functions/og-preview/index.ts`
6. انشر

### 2. تأكد من وجود متغيرات البيئة

في Supabase Dashboard ← Project Settings ← API:
- `SUPABASE_URL` ← موجود تلقائياً داخل الـ Function
- `SUPABASE_SERVICE_ROLE_KEY` ← أضفه في Edge Function secrets

```bash
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 3. رفع `daftar.html` المحدّث

استبدل ملف `daftar.html` الحالي بالنسخة الجديدة.

---

## كيف يصبح رابط المشاركة

**قبل التعديل (❌ كل الدفاتر بنفس الصورة):**
```
https://yoursite.com/daftar.html?slug=ahmed-2026
```

**بعد التعديل (✅ كل دفتر بصورة الطالب):**
```
https://lhixtovnrpkhzntbcmin.supabase.co/functions/v1/og-preview?slug=ahmed-2026
```

---

## ما يظهر في البريفيو

عند مشاركة الرابط على أي منصة:

```
╔══════════════════════════════╗
║  [صورة الطالب من bg_images] ║
╠══════════════════════════════╣
║  🎓 Ahmed Mohammed — Grad Book
║  General Medicine · Class of 2026
║  Graduation Memory Book
╚══════════════════════════════╝
```

---

## جدول الدعم

| المنصة     | يدعم OG | ملاحظة |
|-----------|---------|--------|
| Telegram  | ✅       | يعمل فوراً |
| WhatsApp  | ✅       | يعمل فوراً |
| Facebook  | ✅       | يعمل فوراً |
| Discord   | ✅       | يعمل فوراً |
| X (Twitter) | ✅     | يستخدم twitter:card |
| LinkedIn  | ✅       | يعمل فوراً |
| Messenger | ✅       | يرث إعدادات Facebook |

---

## اختبار البريفيو

بعد النشر، اختبر الرابط في:
- https://developers.facebook.com/tools/debug/
- https://cards-dev.twitter.com/validator
- https://www.linkedin.com/post-inspector/

أو ببساطة شارك الرابط على Telegram وشوف البريفيو.

---

## ملاحظة على الصور

الـ Function تأخذ **أول صورة** من حقل `bg_images` في جدول `guestbooks`.  
هذه هي صورة الغلاف الأساسية للطالب.

إذا أردت تغيير الأولوية (مثلاً: cover_photo منفصل)، عدّل هذا الجزء في `index.ts`:
```typescript
const imgs: string[] = Array.isArray(book.bg_images)
  ? book.bg_images
  : JSON.parse(book.bg_images || "[]");

if (imgs.length > 0) {
  imageUrl = imgs[0].startsWith("http") ? imgs[0] : `${SUPABASE_URL}/.../${imgs[0]}`;
}
```
