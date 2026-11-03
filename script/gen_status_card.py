import os
import json
import base64
import io
from datetime import datetime, timedelta
import requests
from PIL import Image, ImageDraw, ImageFont

# config
SERVER_IP = "animextremes.org"  
OUTPUT_PATH = "../games/minecraft/server/saintontas_mc/statuscard/status.png"
HISTORY_FILE = "../games/minecraft/server/saintontas_mc/statuscard/history.json"
BG_COLOR = (18, 18, 18)        
GRAPH_COLOR = (0, 230, 118)    

MINECRAFT_COLORS = {
    '0': (0, 0, 0),         '1': (0, 0, 170),
    '2': (0, 170, 0),       '3': (0, 170, 170),
    '4': (170, 0, 0),       '5': (170, 0, 170),
    '6': (255, 170, 0),     '7': (170, 170, 170),
    '8': (85, 85, 85),      '9': (85, 85, 255),
    'a': (85, 255, 85),     'b': (85, 255, 255),
    'c': (255, 85, 85),     'd': (255, 85, 255),
    'e': (255, 255, 85),    'f': (255, 255, 255),
}

def fetch_server_data():
    try:
        url = f"https://api.mcsrvstat.us/3/{SERVER_IP}"
        res = requests.get(url, timeout=5).json()
        if res.get("online"):
            motd_raw = res.get("motd", {}).get("raw", ["Minecraft Server", "Online"])
            online_players = res.get("players", {}).get("online", 0)
            max_players = res.get("players", {}).get("max", 100)
            icon_data = res.get("icon")
            return {
                "online": True,
                "motd": motd_raw if isinstance(motd_raw, list) else [motd_raw],
                "players": f"{online_players}/{max_players}",
                "online_count": online_players,
                "icon": icon_data
            }
    except Exception as e:
        print(f"Error fetching status: {e}")
        
    return {
        "online": False,
        "motd": ["§cServer Offline", "§7Check back later"],
        "players": "0/20",
        "online_count": 0,
        "icon": None
    }

def update_history(current_count):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = []
    
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            history = []
            
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    history.append({"time": now_str, "players": current_count})
    
    # Prune data older than 7 days
    cutoff = datetime.utcnow() - timedelta(days=7)
    history = [h for h in history if datetime.strptime(h["time"], "%Y-%m-%d %H:%M") > cutoff]
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
        
    return history

def draw_minecraft_text(draw, xy, text, font, default_color=(255, 255, 255)):
    x, y = xy
    current_color = default_color
    text = str(text).replace('&', '§')
    parts = text.split('§')
    
    if parts[0]:
        draw.text((x, y), parts[0], fill=current_color, font=font)
        x += font.getlength(parts[0])
        
    for part in parts[1:]:
        if not part:
            continue
        code = part[0].lower()
        actual_text = part[1:]
        
        if code in MINECRAFT_COLORS:
            current_color = MINECRAFT_COLORS[code]
        elif code == 'r':
            current_color = default_color
            
        if actual_text:
            draw.text((x, y), actual_text, fill=current_color, font=font)
            x += font.getlength(actual_text)

def generate_card():
    data = fetch_server_data()
    history = update_history(data["online_count"])
    
    width, height = 940, 360
    img = Image.new("RGB", (width, height), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 20)
        font_motd = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 13)
    except IOError:
        font_title = font_motd = font_small = ImageFont.load_default()


    draw.rectangle([20, 20, 84, 84], outline=(60, 60, 60), fill=(30, 30, 30))

    if data["icon"]:
        try:
            if "," in data["icon"]:
                icon_base64_str = data["icon"].split(",")[1]
            else:
                icon_base64_str = data["icon"]
                
            icon_bytes = base64.b64decode(icon_base64_str)
            icon_img = Image.open(io.BytesIO(icon_bytes)).convert("RGBA")
            icon_img = icon_img.resize((64, 64), Image.Resampling.NEAREST)
            img.paste(icon_img, (20, 20), icon_img)
        except Exception as e:
            print(f"Failed to load server icon: {e}")
            draw.text((32, 42), "", fill=GRAPH_COLOR, font=font_title)
    else:
        draw.text((32, 42), "", fill=GRAPH_COLOR, font=font_title)

    server_title = data["motd"][0] if len(data["motd"]) > 0 else "Minecraft Server"
    clean_title_text = server_title.replace('§0','').replace('§1','').replace('§2','').replace('§3','').replace('§4','').replace('§5','').replace('§6','').replace('§7','').replace('§8','').replace('§9','').replace('§a','').replace('§b','').replace('§c','').replace('§d','').replace('§e','').replace('§f','').replace('§l','').replace('§r','')
    
    draw.text((100, 20), clean_title_text, fill=(255, 255, 255), font=font_title)
    draw.text((width - 120, 20), data["players"], fill=(200, 200, 200), font=font_title)
    

    for i in range(4):
        bar_h = (i + 1) * 4
        draw.rectangle([width - 40 + (i * 6), 38 - bar_h, width - 37 + (i * 6), 38], fill=GRAPH_COLOR)

    if len(data["motd"]) > 1:
        draw_minecraft_text(draw, (100, 48), data["motd"][1], font=font_motd)

    draw.line([(20, 100), (width - 20, 100)], fill=(45, 45, 45), width=1)

  
    draw.text((20, 115), f"Player activity — {clean_title_text}", fill=(255, 255, 255), font=font_title)
    draw.text((20, 140), "last 7 days", fill=(120, 120, 120), font=font_small)

    graph_x1, graph_y1 = 60, 160
    graph_x2, graph_y2 = width - 30, 310
    
    max_players_recorded = max([h["players"] for h in history]) if history else 5
    y_max = max(6, max_players_recorded + 2)

    for y_val in range(y_max + 1):
        y_pos = graph_y2 - int(y_val * ((graph_y2 - graph_y1) / y_max))
        if y_pos >= graph_y1:
            draw.line([(graph_x1, y_pos), (graph_x2, y_pos)], fill=(35, 35, 35), width=1)
            draw.text((35, y_pos - 6), str(y_val), fill=(150, 150, 150), font=font_small)

  
    if len(history) > 1:
        step = (graph_x2 - graph_x1) / (len(history) - 1)
        points = []
        for i, entry in enumerate(history):
            x_pos = graph_x1 + (i * step)
            p_count = entry["players"]
            y_pos = graph_y2 - int(p_count * ((graph_y2 - graph_y1) / y_max))
            points.append((x_pos, y_pos))
            draw.ellipse([x_pos - 2, y_pos - 2, x_pos + 2, y_pos + 2], fill=GRAPH_COLOR)

        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=GRAPH_COLOR, width=2)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    img.save(OUTPUT_PATH)
    print("Status card generated successfully.")

if __name__ == "__main__":
    generate_card()