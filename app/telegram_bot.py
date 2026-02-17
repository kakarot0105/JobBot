"""Telegram bot for job notifications."""
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
from .db import add_user, set_filters, get_filters, mark_applied, get_unsent_jobs, mark_sent
from .jobs import search_jobs_for_user
import asyncio
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
NOTIFICATION_CHAT_ID = -1003357441031  # JobBot Alerts supergroup (migrated)

# Conversation states
SETTING_KEYWORDS, SETTING_LOCATION, SETTING_SALARY, SETTING_LEVEL, SETTING_TYPE = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    
    # Add user to database
    db_user_id = add_user(str(user_id), username)
    context.user_data['user_id'] = db_user_id
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Set Filters", callback_data="set_filters")],
        [InlineKeyboardButton("🔍 Search Jobs", callback_data="search_jobs")],
        [InlineKeyboardButton("✅ Applied Jobs", callback_data="applied_jobs")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 Welcome to **JobBot**!\n\n"
        "I'll find the best jobs for you across multiple platforms.\n\n"
        "Get started by setting your preferences!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    
    user_id = context.user_data.get('user_id')
    
    if query.data == "set_filters":
        await query.edit_message_text(
            text="📝 Let's set up your job preferences!\n\n"
                 "What keywords are you looking for?\n"
                 "(e.g., Python, Backend, Data)"
        )
        return SETTING_KEYWORDS
    
    elif query.data == "search_jobs":
        filters = get_filters(user_id)
        if not filters:
            await query.edit_message_text(text="❌ Please set your filters first using /set")
            return
        
        await query.edit_message_text(text="🔍 Searching jobs... Please wait")
        
        try:
            jobs = await search_jobs_for_user(user_id)
            if not jobs:
                await query.edit_message_text(text="😕 No jobs found matching your criteria.")
                return
            
            # Get unsent jobs
            unsent = get_unsent_jobs(user_id, limit=5)
            if not unsent:
                await query.edit_message_text(text="✅ All jobs already sent! Check back later.")
                return
            
            # Send jobs to notification chat
            for job in unsent:
                msg = f"""
💼 **{job['title']}**
🏢 {job['company']}
📍 {job['location']}
💰 {job['salary']}
⏰ {job['job_type']}

[Apply Here]({job['url']})
"""
                await context.bot.send_message(
                    chat_id=NOTIFICATION_CHAT_ID,
                    text=msg,
                    parse_mode="Markdown"
                )
                mark_sent(user_id, job['id'])
                await asyncio.sleep(0.5)  # Rate limiting
            
            await query.edit_message_text(
                text=f"✅ Sent {len(unsent)} new jobs!\n\n"
                     f"Keep checking back for more opportunities."
            )
        except Exception as e:
            await query.edit_message_text(text=f"❌ Error: {str(e)}")
    
    elif query.data == "applied_jobs":
        await query.edit_message_text(text="📋 Your applied jobs will be tracked here.")
    
    elif query.data == "stats":
        await query.edit_message_text(
            text="📊 **Your Stats**\n\n"
                 "Total jobs found: X\n"
                 "Applied: X\n"
                 "This week: X"
        )


async def handle_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle keywords input."""
    keywords = update.message.text.split(',')
    keywords = [k.strip() for k in keywords]
    context.user_data['keywords'] = keywords
    
    await update.message.reply_text(
        "Got it! Keywords: " + ", ".join(keywords) + "\n\n"
        "Where do you want to work?\n"
        "(e.g., Remote, USA, NYC, London)"
    )
    return SETTING_LOCATION


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle location input."""
    location = update.message.text
    context.user_data['location'] = location
    
    await update.message.reply_text(
        f"Great! Location: {location}\n\n"
        "What's your minimum salary? (optional)\n"
        "(e.g., 80000 or skip)"
    )
    return SETTING_SALARY


async def handle_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle salary input."""
    salary_text = update.message.text.strip()
    salary_min = None
    
    if salary_text.lower() != 'skip':
        try:
            salary_min = int(''.join(filter(str.isdigit, salary_text)))
        except:
            pass
    
    context.user_data['salary_min'] = salary_min
    
    await update.message.reply_text(
        "Experience level? (optional)\n"
        "(Junior / Mid / Senior / Skip)"
    )
    return SETTING_LEVEL


async def handle_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle level input."""
    level = update.message.text.strip().lower()
    if level == 'skip':
        level = None
    context.user_data['level'] = level
    
    await update.message.reply_text(
        "Job type? (optional)\n"
        "(Full-time / Contract / Both / Skip)"
    )
    return SETTING_TYPE


async def handle_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job type input."""
    job_type = update.message.text.strip().lower()
    if job_type == 'skip':
        job_type = None
    elif job_type == 'both':
        job_type = ['Full-time', 'Contract']
    
    context.user_data['job_type'] = job_type
    
    # Save all filters
    user_id = context.user_data['user_id']
    set_filters(
        user_id,
        keywords=context.user_data['keywords'],
        location=context.user_data['location'],
        salary_min=context.user_data.get('salary_min'),
        level=context.user_data.get('level'),
        job_type=context.user_data.get('job_type')
    )
    
    await update.message.reply_text(
        "✅ **Filters saved!**\n\n"
        f"Keywords: {', '.join(context.user_data['keywords'])}\n"
        f"Location: {context.user_data['location']}\n"
        f"Salary: ${context.user_data.get('salary_min') or 'Any'}\n"
        f"Level: {context.user_data.get('level') or 'Any'}\n"
        f"Type: {context.user_data.get('job_type') or 'Any'}\n\n"
        "Use /search to find jobs!"
    )
    return ConversationHandler.END


def create_bot():
    """Create and setup Telegram bot."""
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    
    # Conversation handler for setting filters
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_keywords, pattern="^set_filters$")],
        states={
            SETTING_KEYWORDS: [CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
            SETTING_LOCATION: [CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
            SETTING_SALARY: [CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
            SETTING_LEVEL: [CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
            SETTING_TYPE: [CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        },
        fallbacks=[],
    )
    
    # Callback handler
    app.add_handler(CallbackQueryHandler(button_callback))
    
    return app
