# main.py

import os
import logging
import time
import re
from datetime import datetime, timedelta
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from pyrogram.errors import RPCError
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# --- Bot Client Setup ---
session_name = os.environ.get("SESSION_NAME", "group_help_bot")
bot = Client(session_name, bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
bot_start_time = time.time()

# --- Utility Functions ---

async def is_admin(chat_id, user_id):
    """Check if a user is an admin in the chat."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

# --- Welcome and Farewell ---

@bot.on_message(filters.new_chat_members)
async def welcome_new_members(client, message: Message):
    """Welcome new members to the group."""
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        await message.reply_text(f"Hello {member.mention}, welcome to the group!")

@bot.on_message(filters.left_chat_member)
async def farewell_member(client, message: Message):
    """Send a farewell message when a member leaves."""
    if message.left_chat_member.is_bot:
        return
    await message.reply_text(f"Goodbye, {message.left_chat_member.mention}! We will miss you.")

# --- Moderation Commands ---

@bot.on_message(filters.group & filters.command("mute"))
async def mute_user(_, message: Message):
    """Mute a user in the group."""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an admin to use this command.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Please reply to the user you want to mute.")

    target_user_id = message.reply_to_message.from_user.id
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user_id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await message.reply_text(f"🔇 User {message.reply_to_message.from_user.mention} has been muted.")
    except RPCError as e:
        await message.reply_text(f"❌ Failed to mute: {e}")

@bot.on_message(filters.group & filters.command("unmute"))
async def unmute_user(_, message: Message):
    """Unmute a previously muted user."""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an admin to use this command.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Please reply to the user you want to unmute.")

    target_user_id = message.reply_to_message.from_user.id
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await message.reply_text(f"🔊 User {message.reply_to_message.from_user.mention} has been unmuted.")
    except RPCError as e:
        await message.reply_text(f"❌ Failed to unmute: {e}")

@bot.on_message(filters.group & filters.command("ban"))
async def ban_user(_, message: Message):
    """Ban a user from the group."""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an admin to use this command.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Please reply to the user you want to ban.")

    target_user_id = message.reply_to_message.from_user.id
    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user_id)
        await message.reply_text(f"🔨 User {message.reply_to_message.from_user.mention} has been banned.")
    except RPCError as e:
        await message.reply_text(f"❌ Failed to ban: {e}")

@bot.on_message(filters.group & filters.command("unban"))
async def unban_user(_, message: Message):
    """Unban a previously banned user."""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an admin to use this command.")
    
    if not message.reply_to_message:
        return await message.reply_text("❌ Please reply to the user you want to unban.")

    target_user_id = message.reply_to_message.from_user.id
    try:
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user_id)
        await message.reply_text(f"✅ User {message.reply_to_message.from_user.mention} has been unbanned.")
    except RPCError as e:
        await message.reply_text(f"❌ Failed to unban: {e}")

@bot.on_message(filters.group & filters.command("kick"))
async def kick_user(_, message: Message):
    """Kick a user from the group."""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You are not an admin to use this command.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Please reply to the user you want to kick.")

    target_user_id = message.reply_to_message.from_user.id
    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user_id)
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user_id)
        await message.reply_text(f"🦶 User {message.reply_to_message.from_user.mention} has been kicked.")
    except RPCError as e:
        await message.reply_text(f"❌ Failed to kick: {e}")

@bot.on_message(filters.group & filters.command("del"))
async def delete_message(_, message: Message):
    """Delete a replied message."""
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if message.reply_to_message:
        await message.reply_to_message.delete()
        await message.delete()

# --- Group Management ---

@bot.on_message(filters.group & filters.command("ginfo"))
async def group_info(_, message: Message):
    """Get group information."""
    chat = message.chat
    chat_info = (
        f"**Group Information**\n"
        f"**Title:** {chat.title}\n"
        f"**ID:** `{chat.id}`\n"
        f"**Type:** {chat.type}\n"
        f"**Members:** {await bot.get_chat_members_count(chat.id)}\n"
    )
    if chat.username:
        chat_info += f"**Username:** @{chat.username}\n"
    await message.reply_text(chat_info, parse_mode=ParseMode.MARKDOWN)

@bot.on_message(filters.group & filters.command("uinfo"))
async def user_info(_, message: Message):
    """Get a user's information."""
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    user_info = (
        f"**User Information**\n"
        f"**Name:** {user.first_name}\n"
        f"**ID:** `{user.id}`\n"
    )
    if user.username:
        user_info += f"**Username:** @{user.username}\n"
    await message.reply_text(user_info, parse_mode=ParseMode.MARKDOWN)

@bot.on_message(filters.group & filters.command("setrules"))
async def set_rules(_, message: Message):
    """Set or update group rules."""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You must be an admin to set rules.")
    
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/setrules Your new rules here`")
    
    rules = " ".join(message.command[1:])
    # You can save this to a file or database if needed for persistence
    # For now, we'll store it as a global variable.
    message.chat.rules = rules
    await message.reply_text("✅ Group rules have been updated!")

@bot.on_message(filters.command("rules"))
async def get_rules(_, message: Message):
    """Display group rules."""
    if hasattr(message.chat, 'rules'):
        await message.reply_text(f"**Current Group Rules:**\n\n{message.chat.rules}")
    else:
        await message.reply_text("❌ No rules have been set for this group yet.")

# --- Utility and Fun ---

@bot.on_message(filters.command("ping"))
async def ping_handler(_, message):
    """Check bot's response time."""
    start_time = time.time()
    ping_msg = await message.reply_text("Pinging...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000)
    uptime_seconds = int(time.time() - bot_start_time)
    uptime_str = str(timedelta(seconds=uptime_seconds))
    
    await ping_msg.edit_text(
        f"🏓 **Pong!**\n"
        f"**Ping:** `{ping_time}ms`\n"
        f"**Uptime:** `{uptime_str}`"
    )

@bot.on_message(filters.private & filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_handler(_, message: Message):
    """Broadcast a message to all chats."""
    if not message.reply_to_message:
        return await message.reply_text("❌ Please reply to a message to broadcast it.")

    sent_count = 0
    failed_count = 0
    async for dialog in bot.get_dialogs():
        try:
            if dialog.chat.id != OWNER_ID:
                await message.reply_to_message.copy(dialog.chat.id)
                sent_count += 1
                await asyncio.sleep(0.5)
        except Exception:
            failed_count += 1
    
    await message.reply_text(f"✅ Broadcast complete. Sent to {sent_count} chats, failed for {failed_count}.")

@bot.on_message(filters.text & filters.group)
async def auto_responder(_, message: Message):
    """Automatically respond to specific keywords."""
    text = message.text.lower()
    if "hello bot" in text:
        await message.reply_text("Hello there! How can I help you?")
    elif "thanks bot" in text:
        await message.reply_text("You're welcome!")

@bot.on_inline_query()
async def inline_search(_, inline_query: InlineQuery):
    """Handle inline queries for fun features."""
    query = inline_query.query.strip().lower()
    
    results = [
        InlineQueryResultArticle(
            title="Help",
            input_message_content=InputTextMessageContent(
                "You can use the bot in a group for moderation and other features."
            ),
            description="Get help about bot commands."
        ),
        InlineQueryResultArticle(
            title="Ping",
            input_message_content=InputTextMessageContent(
                "🏓 Pong! The bot is online."
            ),
            description="Check if the bot is alive."
        )
    ]

    await inline_query.answer(results=results, cache_time=5)

# --- Basic Info Commands ---

@bot.on_message(filters.command("start"))
async def start_handler(_, message):
    """Bot ke start hone par welcome message bheje."""
    caption = (
        f"👋 Hello, **{message.from_user.first_name}**!\n\n"
        "Main ek advanced group help bot hoon. commands ke liye **/help** type karein."
    )
    buttons = [
        [
            InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{bot.get_me().username}?startgroup=true"),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="show_help"),
            InlineKeyboardButton("📢 Updates", url="https://t.me/bestshayri_raj")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

@bot.on_message(filters.command("help"))
async def help_handler(_, message):
    """Sabhi available commands ki list dikhata hai."""
    help_text = (
        "**Group Help Bot Commands**\n"
        "------------------------------\n"
        "**Core:** /start, /help, /ping\n"
        "**Moderation:** /mute, /unmute, /ban, /unban, /kick, /del\n"
        "**Group Info:** /ginfo, /uinfo\n"
        "**Management:** /setrules, /rules, /broadcast (Owner Only)\n"
    )
    await message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# --- Callback Queries ---

@bot.on_callback_query(filters.regex("^show_help$"))
async def show_help_callback(_, callback_query):
    help_text = (
        "**Group Help Bot Commands**\n"
        "------------------------------\n"
        "**Core:** /start, /help, /ping\n"
        "**Moderation:** /mute, /unmute, /ban, /unban, /kick, /del\n"
        "**Group Info:** /ginfo, /uinfo\n"
        "**Management:** /setrules, /rules, /broadcast (Owner Only)\n"
    )
    await callback_query.message.edit_text(help_text, parse_mode=ParseMode.MARKDOWN)

# --- Bot Run ---
if __name__ == "__main__":
    logging.info("Starting bot...")
    bot.run()
    logging.info("Bot started successfully.")
