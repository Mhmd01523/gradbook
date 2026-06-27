import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SB_URL")!;
const SUPABASE_SERVICE_KEY = Deno.env.get("SERVICE_ROLE_KEY")!;

const BOT_PATTERNS = [
  "telegrambot","whatsapp","facebookexternalhit","facebot",
  "discordbot","linkedinbot","twitterbot","slackbot",
  "pinterest","applebot","googlebot","bingbot",
  "ia_archiver","vkshare","embedly",
];

function isBot(userAgent: string): boolean {
  const ua = userAgent.toLowerCase();
  return BOT_PATTERNS.some((p) => ua.includes(p));
}

async function fetchBookData(slug: string) {
  const sb = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);
  const { data, error } = await sb
    .from("guestbooks")
    .select("owner_name, owner_name_en, owner_name_ru, faculty, grad_year, bg_images, default_lang, slug, order_code")
    .eq("slug", slug)
    .eq("is_active", true)
    .single();
  if (error || !data) return null;
  return data;
}

function getFacultyLabel(faculty: string, lang: string): string {
  const map: Record<string, Record<string, string>> = {
    general: { ar: "كلية الطب العام", en: "General Medicine", ru: "Лечебный факультет" },
    dental:  { ar: "كلية طب الأسنان", en: "Dentistry", ru: "Стоматологический факультет" },
    pharmacy:{ ar: "كلية الصيدلة", en: "Pharmacy", ru: "Фармацевтический факультет" },
  };
  return map[faculty]?.[lang] ?? map[faculty]?.["en"] ?? faculty ?? "";
}

function escHtml(str: string): string {
  return str.replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function buildOGHtml(opts: { name:string; faculty:string; year:string; imageUrl:string; pageUrl:string; lang:string }): string {
  const { name, faculty, year, imageUrl, pageUrl, lang } = opts;
  const title = `🎓 ${name} — Grad Book`;
  const yearLabel = lang==="ru" ? `Выпуск ${year}` : lang==="ar" ? `دفعة ${year}` : `Class of ${year}`;
  const description = [faculty, year ? yearLabel : "", "Graduation Memory Book"].filter(Boolean).join(" · ");

  return `<!DOCTYPE html>
<html lang="${lang}">
<head>
<meta charset="UTF-8">
<title>${escHtml(title)}</title>
<meta property="og:type" content="website">
<meta property="og:site_name" content="Grad Book">
<meta property="og:url" content="${escHtml(pageUrl)}">
<meta property="og:title" content="${escHtml(title)}">
<meta property="og:description" content="${escHtml(description)}">
<meta property="og:image" content="${escHtml(imageUrl)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${escHtml(title)}">
<meta name="twitter:description" content="${escHtml(description)}">
<meta name="twitter:image" content="${escHtml(imageUrl)}">
<meta http-equiv="refresh" content="0; url=${escHtml(pageUrl)}">
</head>
<body><p>Redirecting… <a href="${escHtml(pageUrl)}">${escHtml(name)} — Grad Book</a></p></body>
</html>`;
}

Deno.serve(async (req: Request) => {
  const url = new URL(req.url);
  const slug = url.searchParams.get("slug") || "";

  if (!slug) return new Response("Missing slug", { status: 400 });

  const userAgent = req.headers.get("user-agent") || "";
  const pageUrl = `https://mhmd01523.github.io/gradbook/daftar.html?slug=${encodeURIComponent(slug)}`;

  if (!isBot(userAgent)) {
    return Response.redirect(pageUrl, 302);
  }

  const book = await fetchBookData(slug);
  if (!book) return Response.redirect("https://mhmd01523.github.io/gradbook/index.html", 302);

  const lang = book.default_lang || "en";
  const name = (lang==="en" ? book.owner_name_en : lang==="ru" ? book.owner_name_ru : null) || book.owner_name || "";
  const faculty = getFacultyLabel(book.faculty || "", lang);
  const year = book.grad_year || "";

  // الأولوية: نسخة og-cover.jpg المصغّرة (إن وُجدت) — أصغر حجماً وأكثر توافقاً
  // مع معاينات الروابط. إن لم توجد (دفاتر قديمة)، نستخدم الصورة الأصلية.
  let imageUrl = `${SUPABASE_URL}/storage/v1/object/public/covers/default-og.jpg`;
  const ogCoverUrl = `${SUPABASE_URL}/storage/v1/object/public/gradbook-photos/orders/${book.order_code || slug}/og-cover.jpg`;

  try {
    const headRes = await fetch(ogCoverUrl, { method: "HEAD" });
    if (headRes.ok) {
      imageUrl = ogCoverUrl;
    } else {
      const imgs: string[] = Array.isArray(book.bg_images) ? book.bg_images : JSON.parse(book.bg_images || "[]");
      if (imgs.length > 0) {
        const img = imgs[0];
        imageUrl = img.startsWith("http") ? img : `${SUPABASE_URL}/storage/v1/object/public/gradbook-photos/${img}`;
      }
    }
  } catch (_) {}

  const html = buildOGHtml({ name, faculty, year, imageUrl, pageUrl, lang });

  return new Response(html, {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=300" },
  });
});
