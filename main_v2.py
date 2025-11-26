import requests
import torch
import oci
import os
import json
import datetime
from PIL import Image, ImageStat
from io import BytesIO
from transformers import CLIPProcessor, CLIPModel

# ==========================================
#  USER CONFIGURATION (EDIT THIS)
# ==========================================
CAT_API_KEY = 'YOUR-API-KEY' 
OCI_NAMESPACE = 'NAMESPACE'
OCI_BUCKET_NAME = 'bucket-cats'

# --- NOTIFICATION CONFIG ---
# Paste your Discord Webhook URL here.Leave blank if using Telegram.
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/144286970/FUZv6vPPYV1qm4VrUV-FvxqFGK4ovStBocGAc7RCc8-Cdvtryv8ELHH'

# Or, fill these if you prefer Telegram(Leave blank if using Discord)
TELEGRAM_BOT_TOKEN = ''
TELEGRAM_CHAT_ID = ''

# ==========================================
#  AI & CLOUD SETUP
# ==========================================
print("Loading AI Brain...")
MODEL_ID = "openai/clip-vit-base-patch32"
model = CLIPModel.from_pretrained(MODEL_ID)
processor = CLIPProcessor.from_pretrained(MODEL_ID)

# ==========================================
#  HELPER FUNCTIONS
# ==========================================

def send_notification(message):
    """Sends the daily report to Discord or Telegram."""
    try:
        #  Try Discord
        if DISCORD_WEBHOOK_URL:
            data = {"content": message}
            requests.post(DISCORD_WEBHOOK_URL, json=data)
            print(" Discord Notification Sent.")
            return

        #  Try Telegram
        elif TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
            requests.post(url, json=data)
            print(" Telegram Notification Sent.")
            return
            
        print(" No notification configured.")

    except Exception as e:
        print(f" Notification Failed: {e}")

def get_warmth(img):
    stat = ImageStat.Stat(img)
    r, g, b = stat.mean
    return "Warm" if r > b else "Cool"

def get_vibe(img):
    labels = ["a funny goofy cat", "a normal calm cat"]
    inputs = processor(text=labels, images=img, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)
    return "Funny" if probs[0][0].item() > 0.6 else "Normal"

def upload_to_oracle(file_content, destination_path):
    try:
        config = oci.config.from_file()
        object_storage = oci.object_storage.ObjectStorageClient(config)
        object_storage.put_object(OCI_NAMESPACE, OCI_BUCKET_NAME, destination_path, file_content)
        return True
    except Exception as e:
        print(f" Upload Error: {e}")
        return False

def fetch_cats():
    url = "https://api.thecatapi.com/v1/images/search?limit=10"
    headers = {'x-api-key': CAT_API_KEY}
    try:
        resp = requests.get(url, headers=headers)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []


#  MAIN LOGIC WITH REPORTING
###########################################
def main():
    start_time = datetime.datetime.now()
    print(f"--- Job Started at {start_time} ---")
    
    cats = fetch_cats()
    
    #  Statistics Counters
    stats = {
        "processed": 0,
        "failed": 0,
        "warm": 0,
        "cool": 0,
        "funny": 0,
        "normal": 0
    }

    for cat in cats:
        try:
            # Download
            response = requests.get(cat['url'])
            img_data = BytesIO(response.content)
            img = Image.open(img_data).convert('RGB')
            
            # Analyze
            warmth = get_warmth(img)
            vibe = get_vibe(img)
            
            # Update Stats
            stats[warmth.lower()] += 1
            stats[vibe.lower()] += 1
            
            # Upload
            filename = f"{cat['id']}.jpg"
            cloud_path = f"{warmth}/{vibe}/{filename}"
            print(f"Processing: {filename} -> [{warmth} | {vibe}]")
            
            img_data.seek(0)
            if upload_to_oracle(img_data, cloud_path):
                stats["processed"] += 1
            else:
                stats["failed"] += 1
                
        except Exception as e:
            print(f"Error on {cat['id']}: {e}")
            stats["failed"] += 1

    #  Generate Report Message
    duration = datetime.datetime.now() - start_time
    report = (
        f"** Daily Cat Segregator Report**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f" **Success:** {stats['processed']}\n"
        f" **Failed:** {stats['failed']}\n"
        f" **Duration:** {duration.seconds} seconds\n\n"
        f"** Segregation Stats:**\n"
        f"•  Warm: {stats['warm']} |  Cool: {stats['cool']}\n"
        f"•  Funny: {stats['funny']} |  Normal: {stats['normal']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f" *Oracle Cloud System Status: Online*"
    )

    # Send Notification
    print("Sending Notification...")
    send_notification(report)
    print("Done.")

if __name__ == "__main__":
    main()
