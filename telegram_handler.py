import telegram
import requests
import re
import os
from telegram.ext import Application, MessageHandler, filters 

# --- KONFIGURASI ---
# Token Bot Telegram Anda
TELEGRAM_BOT_TOKEN = ""

# Konfigurasi GitHub Anda
GITHUB_PAT = ""
REPO_OWNER = "AnGgIt886" 
REPO_NAME = "OEM"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/dispatches"
EVENT_TYPE = "telegram_request"

# Fungsi untuk mengirim request ke GitHub API (menggunakan async)
async def trigger_github_action(payload_data, update):
    
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    body = {
        "event_type": EVENT_TYPE,
        "client_payload": payload_data
    }
    
    try:
        response = requests.post(GITHUB_API_URL, headers=headers, json=body)
        
        if response.status_code == 204:
            await update.message.reply_text(
                text=f"✅ **Request Diterima!**\n\nAndroid: `{payload_data['android_version']}`\nPengirim: {payload_data['username']}\n\nMemulai proses *patch* di GitHub Actions...",
                parse_mode=telegram.constants.ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                text=f"❌ **Gagal Memicu GitHub Actions!**\nStatus: {response.status_code}\nMohon hubungi admin.",
                parse_mode=telegram.constants.ParseMode.MARKDOWN
            )
            print(f"ERROR: GitHub API gagal. Status: {response.status_code}, Pesan: {response.text}")
            
    except Exception as e:
        await update.message.reply_text(
            text=f"❌ **Error Koneksi** saat memicu GitHub:\n`{str(e)[:100]}`",
            parse_mode=telegram.constants.ParseMode.MARKDOWN
        )
        print(f"ERROR: Koneksi gagal. {e}")


# Fungsi utama yang menangani pesan (async untuk kompatibilitas modern)
async def handle_message(update, context):
    message = update.effective_message
    text = message.text
    sender = message.from_user

    # Dapatkan Username Pengirim
    if sender.username:
        request_username = f"@{sender.username}"
    else:
        first_name = sender.first_name if sender.first_name else 'Anonim'
        request_username = f"User ({first_name})"

    # Parsing Pesan berdasarkan format yang Anda inginkan
    if text and text.strip().lower().startswith('#request'):
        
        android_match = re.search(r'Android:\s*(\d+)', text, re.IGNORECASE)
        fw_match = re.search(r'Fw:\s*(\S+)', text, re.IGNORECASE)
        
        android_version = android_match.group(1) if android_match else None
        framework_url = fw_match.group(1) if fw_match else None

        if android_version and framework_url:
            payload = {
                "android_version": android_version,
                "framework_url": framework_url,
                "username": request_username
            }
            
            # Panggil fungsi trigger sebagai async
            await trigger_github_action(payload, update)
            
        else:
            await update.message.reply_text( 
                text="❌ **Format Request Tidak Valid.**\nMohon gunakan format:\n\n```\n#request\n\nAndroid: [versi]\nFw: [URL]\n```",
                parse_mode=telegram.constants.ParseMode.MARKDOWN
            )

# Fungsi main yang menggunakan Application
def main():
    # Menggunakan Application.builder() adalah cara modern dan stabil
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Handler untuk semua pesan teks
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot berjalan dan mendengarkan...")
    
    # run_polling adalah pengganti start_polling/idle
    application.run_polling() 

if __name__ == '__main__':
    main()