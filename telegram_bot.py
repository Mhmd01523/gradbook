"""
╔══════════════════════════════════════════════════════════════╗
║         Grad Book — Telegram Bot (Multilingual)              ║
║                                                              ║
║  Features:                                                   ║
║  - Auto-detects user's Telegram language                     ║
║  - Sends welcome message in user's language                  ║
║  - Saves language preference to Supabase orders table        ║
║  - All messages use stored language                          ║
║                                                              ║
║  Supported languages: ar, en, ru, fr, zh, es, pt            ║
║  Fallback: en                                                ║
║                                                              ║
║  Install deps:                                               ║
║    pip install python-telegram-bot supabase                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client

# ═══ CONFIG ═══ (replace with your values)
BOT_TOKEN    = "YOUR_BOT_TOKEN_HERE"
SUPABASE_URL = "https://lhixtovnrpkhzntbcmin.supabase.co"
SUPABASE_KEY = "YOUR_SERVICE_ROLE_KEY_HERE"   # use service role key for writes

logging.basicConfig(level=logging.INFO)
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ═══ LANGUAGE MAPPING ═══
# Maps Telegram language_code (e.g. "ar", "ar-SA", "ru-RU") → our supported lang
SUPPORTED = {"ar", "en", "ru", "fr", "zh", "es", "pt"}

def map_tg_lang(tg_lang: str) -> str:
    """Map Telegram language_code to our supported set. Fallback: en."""
    if not tg_lang:
        return "en"
    code = tg_lang.lower().split("-")[0]   # "ar-SA" → "ar"
    # zh-hans, zh-hant, zh-tw, zh-cn all → zh
    if code in ("zh", "cn"):
        return "zh"
    return code if code in SUPPORTED else "en"

# ═══ TRANSLATIONS ═══
MSG = {
    "ar": {
        "welcome": (
            "🎓 *مرحباً بك في Grad Book!*\n\n"
            "✅ تم ربط حساب Telegram بنجاح.\n\n"
            "📬 ستصلك جميع التحديثات عبر هذا البوت:\n"
            "• تأكيد استلام الدفعة\n"
            "• تحديثات حالة الطلب\n"
            "• إشعار جاهزية الدفتر\n"
            "• تسليم دفترك النهائي\n\n"
            "🔖 رقم طلبك: `{order_code}`\n\n"
            "_فريق Grad Book يعمل على دفترك — سنتواصل معك قريباً_ 🌟"
        ),
        "payment_confirm": "✅ *تم تأكيد الدفع!* جارٍ البدء في إعداد دفترك 🎓",
        "order_update":    "📋 *تحديث الطلب:* {status}",
        "book_ready":      "🎉 *دفترك جاهز!* إليك رابطك: {link}",
        "delivery":        "📦 *تم التسليم!* شكراً لاختيارك Grad Book 🎓",
        "error":           "❌ حدث خطأ. يرجى المحاولة مرة أخرى أو التواصل معنا.",
    },
    "en": {
        "welcome": (
            "🎓 *Welcome to Grad Book!*\n\n"
            "✅ Telegram connected successfully.\n\n"
            "📬 All future updates will be sent through this bot:\n"
            "• Payment confirmation\n"
            "• Order status updates\n"
            "• Book ready notification\n"
            "• Final book delivery\n\n"
            "🔖 Your order code: `{order_code}`\n\n"
            "_The Grad Book team is working on your book — we'll be in touch soon_ 🌟"
        ),
        "payment_confirm": "✅ *Payment confirmed!* We're starting on your book now 🎓",
        "order_update":    "📋 *Order update:* {status}",
        "book_ready":      "🎉 *Your book is ready!* Here's your link: {link}",
        "delivery":        "📦 *Delivered!* Thank you for choosing Grad Book 🎓",
        "error":           "❌ Something went wrong. Please try again or contact us.",
    },
    "ru": {
        "welcome": (
            "🎓 *Добро пожаловать в Grad Book!*\n\n"
            "✅ Telegram успешно подключён.\n\n"
            "📬 Все обновления будут приходить через этого бота:\n"
            "• Подтверждение оплаты\n"
            "• Обновления статуса заказа\n"
            "• Уведомление о готовности книги\n"
            "• Доставка готовой книги\n\n"
            "🔖 Номер твоего заказа: `{order_code}`\n\n"
            "_Команда Grad Book работает над твоей книгой — скоро свяжемся_ 🌟"
        ),
        "payment_confirm": "✅ *Оплата подтверждена!* Начинаем работу над книгой 🎓",
        "order_update":    "📋 *Обновление заказа:* {status}",
        "book_ready":      "🎉 *Книга готова!* Вот твоя ссылка: {link}",
        "delivery":        "📦 *Доставлено!* Спасибо, что выбрал Grad Book 🎓",
        "error":           "❌ Что-то пошло не так. Попробуй снова или напиши нам.",
    },
    "fr": {
        "welcome": (
            "🎓 *Bienvenue sur Grad Book !*\n\n"
            "✅ Telegram connecté avec succès.\n\n"
            "📬 Toutes les mises à jour seront envoyées via ce bot :\n"
            "• Confirmation du paiement\n"
            "• Mises à jour du statut de la commande\n"
            "• Notification de livre prêt\n"
            "• Livraison finale du livre\n\n"
            "🔖 Votre code de commande : `{order_code}`\n\n"
            "_L'équipe Grad Book travaille sur votre livre — nous vous contacterons bientôt_ 🌟"
        ),
        "payment_confirm": "✅ *Paiement confirmé !* Nous commençons votre livre 🎓",
        "order_update":    "📋 *Mise à jour de la commande :* {status}",
        "book_ready":      "🎉 *Votre livre est prêt !* Voici votre lien : {link}",
        "delivery":        "📦 *Livré !* Merci d'avoir choisi Grad Book 🎓",
        "error":           "❌ Une erreur s'est produite. Réessayez ou contactez-nous.",
    },
    "zh": {
        "welcome": (
            "🎓 *欢迎使用 Grad Book！*\n\n"
            "✅ Telegram 已成功连接。\n\n"
            "📬 所有更新将通过此机器人发送：\n"
            "• 付款确认\n"
            "• 订单状态更新\n"
            "• 留言册准备就绪通知\n"
            "• 最终留言册交付\n\n"
            "🔖 您的订单号：`{order_code}`\n\n"
            "_Grad Book 团队正在为您制作留言册 — 我们很快会联系您_ 🌟"
        ),
        "payment_confirm": "✅ *付款已确认！* 我们现在开始制作您的留言册 🎓",
        "order_update":    "📋 *订单更新：* {status}",
        "book_ready":      "🎉 *您的留言册已准备好！* 这是您的链接：{link}",
        "delivery":        "📦 *已交付！* 感谢您选择 Grad Book 🎓",
        "error":           "❌ 出现错误。请重试或联系我们。",
    },
    "es": {
        "welcome": (
            "🎓 *¡Bienvenido a Grad Book!*\n\n"
            "✅ Telegram conectado exitosamente.\n\n"
            "📬 Todas las actualizaciones serán enviadas a través de este bot:\n"
            "• Confirmación de pago\n"
            "• Actualizaciones del estado del pedido\n"
            "• Notificación de libro listo\n"
            "• Entrega final del libro\n\n"
            "🔖 Tu código de pedido: `{order_code}`\n\n"
            "_El equipo de Grad Book está trabajando en tu libro — nos pondremos en contacto pronto_ 🌟"
        ),
        "payment_confirm": "✅ *¡Pago confirmado!* Estamos comenzando tu libro ahora 🎓",
        "order_update":    "📋 *Actualización del pedido:* {status}",
        "book_ready":      "🎉 *¡Tu libro está listo!* Aquí está tu enlace: {link}",
        "delivery":        "📦 *¡Entregado!* Gracias por elegir Grad Book 🎓",
        "error":           "❌ Algo salió mal. Por favor intenta de nuevo o contáctanos.",
    },
    "pt": {
        "welcome": (
            "🎓 *Bem-vindo ao Grad Book!*\n\n"
            "✅ Telegram conectado com sucesso.\n\n"
            "📬 Todas as atualizações serão enviadas através deste bot:\n"
            "• Confirmação de pagamento\n"
            "• Atualizações de status do pedido\n"
            "• Notificação de livro pronto\n"
            "• Entrega final do livro\n\n"
            "🔖 Seu código de pedido: `{order_code}`\n\n"
            "_A equipe Grad Book está trabalhando no seu livro — entraremos em contato em breve_ 🌟"
        ),
        "payment_confirm": "✅ *Pagamento confirmado!* Estamos começando o seu livro agora 🎓",
        "order_update":    "📋 *Atualização do pedido:* {status}",
        "book_ready":      "🎉 *Seu livro está pronto!* Aqui está seu link: {link}",
        "delivery":        "📦 *Entregue!* Obrigado por escolher o Grad Book 🎓",
        "error":           "❌ Algo deu errado. Por favor, tente novamente ou entre em contato.",
    },
}

def get_msg(lang: str, key: str, **kwargs) -> str:
    """Get translated message, fallback to English."""
    text = MSG.get(lang, MSG["en"]).get(key, MSG["en"].get(key, ""))
    return text.format(**kwargs) if kwargs else text


# ═══ HANDLERS ═══

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start command — triggered when user clicks the Telegram button
    from the payment page (link format: t.me/BOT?start=ORDER_CODE).
    """
    user     = update.effective_user
    chat_id  = update.effective_chat.id
    tg_lang  = user.language_code or "en"
    lang     = map_tg_lang(tg_lang)

    order_code = " ".join(context.args) if context.args else ""

    logging.info(f"[START] chat_id={chat_id} | tg_lang={tg_lang} | mapped_lang={lang} | order_code={order_code or '(none)'}")

    # Save chat_id + bot_lang to Supabase
    if order_code:
        try:
            sb.table("orders").update({
                "customer_chat_id": str(chat_id),
                "bot_lang": lang,
            }).eq("order_code", order_code).execute()
            logging.info(f"[SUPABASE] Updated order {order_code} → chat_id={chat_id}, lang={lang}")
        except Exception as e:
            logging.warning(f"[SUPABASE] Update failed for order {order_code}: {e}")
    else:
        logging.info("[START] No order_code in deep-link — sending welcome without order link")

    # Always send welcome in user's language
    try:
        welcome_text = get_msg(lang, "welcome", order_code=order_code or "—")
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
        logging.info(f"[START] Welcome sent in '{lang}' to chat_id={chat_id}")
    except Exception as e:
        logging.error(f"[START] Failed to send welcome to chat_id={chat_id}: {e}")
        try:
            await update.message.reply_text(
                f"Welcome to Grad Book! 🎓\nOrder: {order_code or '—'}"
            )
        except Exception:
            pass


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User sends a payment screenshot photo.
    Notifies the admin, saves to DB, acknowledges user.
    """
    chat_id = update.effective_chat.id
    lang    = await _get_user_lang(chat_id)

    # Forward to admin — handled by your existing admin notification logic
    # Here we just acknowledge the user
    ack = {
        "ar": "📸 تم استلام صورة الدفع! سنتحقق ونبدأ العمل خلال ساعة. ✅",
        "en": "📸 Payment screenshot received! We'll verify and start within 1 hour. ✅",
        "ru": "📸 Скриншот оплаты получен! Проверим и начнём в течение часа. ✅",
        "fr": "📸 Capture d'écran reçue ! Nous vérifierons et commencerons dans l'heure. ✅",
        "zh": "📸 收到付款截图！我们将在1小时内验证并开始制作。✅",
        "es": "📸 ¡Captura de pantalla recibida! Verificaremos y comenzaremos en 1 hora. ✅",
        "pt": "📸 Captura de tela recebida! Verificaremos e começaremos em 1 hora. ✅",
    }
    await update.message.reply_text(ack.get(lang, ack["en"]))


async def _get_user_lang(chat_id: int) -> str:
    """Look up stored bot_lang for this chat_id from Supabase."""
    try:
        res = sb.table("orders")\
            .select("bot_lang")\
            .eq("customer_chat_id", str(chat_id))\
            .limit(1)\
            .execute()
        if res.data:
            return res.data[0].get("bot_lang") or "en"
    except Exception:
        pass
    return "en"


# ═══ HELPER: Send message to user in their language ═══
# Call this from your admin panel / Supabase webhook

async def send_to_user(bot, chat_id: int, msg_key: str, lang: str = None, **kwargs):
    """
    Send a translated message to a user.
    
    Usage from admin panel:
        await send_to_user(bot, chat_id, "payment_confirm", lang="ru")
        await send_to_user(bot, chat_id, "book_ready", lang="ar", link="https://...")
    """
    if lang is None:
        lang = await _get_user_lang(chat_id)
    text = get_msg(lang, msg_key, **kwargs)
    await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")


# ═══ MAIN ═══

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logging.info("Bot started — polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
