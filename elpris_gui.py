import tkinter as tk
from tkinter import font, messagebox, ttk
import requests
from datetime import datetime
import threading
import time
import json
import os

# --- KONFIGURATION ---
ELHANDEL_PASLAG = 5.0    
ENERGISKATT = 53.5      
NAT_OVERFORING = 23.0   
FIXED_FEES = ELHANDEL_PASLAG + ENERGISKATT + NAT_OVERFORING
SETTINGS_FILE = "el_settings.json"

class ElprisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Elpriskollen Pro")
        self.root.geometry("1150x420")
        self.root.configure(bg="#020617")
        
        self.settings = self.load_settings()
        self.setup_styles()
        
        # Kolla om det är första gången programmet körs
        if not os.path.exists(SETTINGS_FILE):
            self.setup_ui() # Skapa UI först
            self.root.withdraw()
            self.open_settings(first_run=True)
        else:
            self.setup_ui()
            self.start_threads()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    return json.load(f)
            except: pass
        return {"elomrade": "SE4", "stad": "Helsingborg", "lat": "56.04", "lon": "12.69"}

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f)

    def setup_styles(self):
        self.header_font = font.Font(family="Segoe UI", size=14, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=9, weight="bold")
        self.price_font = font.Font(family="Segoe UI", size=38, weight="bold")
        self.stat_font = font.Font(family="Segoe UI", size=10)

    def setup_ui(self):
        # Översta rubriken
        self.lbl_area_header = tk.Label(self.root, text=f"ELPRISER JUST NU I {self.settings['elomrade']}", 
                                      bg="#020617", fg="#38bdf8", font=self.header_font)
        self.lbl_area_header.pack(pady=(15, 0))

        self.btn_settings = tk.Button(self.root, text="⚙ Inställningar", command=self.open_settings, 
                                     bg="#1e293b", fg="white", font=("Segoe UI", 9), 
                                     borderwidth=0, padx=10, pady=5)
        self.btn_settings.place(relx=0.98, rely=0.02, anchor="ne")

        titles = ["BÖRSPRIS (KVART)", "TOTALKOSTNAD", "BILLIGASTE TIMMEN", "DAGENS SNITT", "VÄDER"]
        colors = ["#1e293b", "#334155", "#4338ca", "#1e1b4b", "#0c4a6e"]
        
        self.cards = []
        card_container = tk.Frame(self.root, bg="#020617")
        card_container.pack(expand=True, fill="both", padx=20, pady=20)

        for i in range(5):
            frame = tk.Frame(card_container, bg=colors[i], highlightbackground="#475569", highlightthickness=1)
            frame.place(relx=i*0.2, rely=0, relwidth=0.19, relheight=0.9)
            
            lbl_title = tk.Label(frame, text=titles[i], bg=colors[i], fg="#94a3b8", font=self.label_font)
            lbl_title.pack(pady=(15, 5))
            
            lbl_price = tk.Label(frame, text="--", bg=colors[i], fg="white", font=self.price_font)
            lbl_price.pack()
            
            lbl_unit = tk.Label(frame, text="Laddar...", bg=colors[i], fg="#94a3b8", font=self.stat_font)
            lbl_unit.pack()
            
            lbl_extra = tk.Label(frame, text="", bg=colors[i], fg="white", font=self.stat_font, justify="center")
            lbl_extra.pack(side="bottom", fill="x", pady=15)
            
            self.cards.append({"frame": frame, "price": lbl_price, "unit": lbl_unit, "extra": lbl_extra})

    def open_settings(self, first_run=False):
        win = tk.Toplevel(self.root)
        win.title("Inställningar")
        win.geometry("350x320")
        win.configure(bg="#1e293b")
        win.grab_set()

        tk.Label(win, text="VÄLJ OMRÅDE & STAD", bg="#1e293b", fg="#38bdf8", font=self.header_font).pack(pady=10)

        tk.Label(win, text="Elområde:", bg="#1e293b", fg="white", font=self.label_font).pack()
        area_var = tk.StringVar(win)
        area_var.set(self.settings["elomrade"])
        area_menu = ttk.OptionMenu(win, area_var, self.settings["elomrade"], "SE1", "SE2", "SE3", "SE4")
        area_menu.pack(pady=5)

        tk.Label(win, text="Stad (för väder):", bg="#1e293b", fg="white", font=self.label_font).pack()
        city_entry = tk.Entry(win, justify="center")
        city_entry.insert(0, self.settings["stad"])
        city_entry.pack(pady=5)

        def save():
            city = city_entry.get()
            try:
                geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=sv&format=json"
                geo_data = requests.get(geo_url).json()
                if "results" in geo_data:
                    self.settings["lat"] = str(geo_data["results"][0]["latitude"])
                    self.settings["lon"] = str(geo_data["results"][0]["longitude"])
                    self.settings["stad"] = geo_data["results"][0]["name"]
                    self.settings["elomrade"] = area_var.get()
                    self.save_settings()
                    
                    self.lbl_area_header.config(text=f"ELPRISER JUST NU I {self.settings['elomrade']}")
                    win.destroy()
                    
                    if first_run:
                        self.root.deiconify()
                        self.start_threads()
                    else:
                        threading.Thread(target=self.refresh_once).start()
                else:
                    messagebox.showerror("Fel", "Staden hittades inte.")
            except:
                messagebox.showerror("Fel", "Nätverksfel.")

        tk.Button(win, text="SPARA INSTÄLLNINGAR", command=save, bg="#059669", fg="white", font=self.label_font, pady=10).pack(pady=20)

    def start_threads(self):
        threading.Thread(target=self.refresh_once, daemon=True).start()
        threading.Thread(target=self.refresh_loop, daemon=True).start()

    def get_data(self):
        now = datetime.now()
        area = self.settings["elomrade"]
        try:
            r = requests.get(f"https://www.elprisetjustnu.se/api/v1/prices/{now.strftime('%Y/%m-%d')}_{area}.json", timeout=10)
            data = r.json()
            all_items = []
            for item in data:
                start = datetime.fromisoformat(item['time_start'].split('+')[0])
                end = datetime.fromisoformat(item['time_end'].split('+')[0])
                sm = item['SEK_per_kWh'] * 100 * 1.25
                all_items.append({
                    'start_dt': start, 'end_dt': end,
                    'total_p': round(sm + FIXED_FEES, 2),
                    'spot_moms': round(sm, 2),
                    'time': f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
                })

            current = next((i for i in all_items if i['start_dt'] <= now < i['end_dt']), all_items[0])
            avg_today = sum(i['total_p'] for i in all_items) / len(all_items)
            
            cheapest_h_avg, cheapest_h_time = float('inf'), ""
            for i in range(len(all_items) - 4):
                avg = sum(all_items[j]['total_p'] for j in range(i, i+4)) / 4
                if avg < cheapest_h_avg:
                    cheapest_h_avg = avg
                    cheapest_h_time = f"{all_items[i]['start_dt'].strftime('%H:%M')} - {all_items[i+3]['end_dt'].strftime('%H:%M')}"

            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={self.settings['lat']}&longitude={self.settings['lon']}&current=temperature_2m,weather_code,wind_speed_10m"
            w_res = requests.get(w_url).json()['current']
            w_desc = "Klart" if w_res['weather_code'] == 0 else "Molnigt" if w_res['weather_code'] in [1,2,3] else "Regn"
            
            return {
                "spot": current['spot_moms'], "total": current['total_p'], "area": area, "current_time": current['time'],
                "avg_today": round(avg_today, 1), "diff": round(((current['total_p'] - avg_today)/avg_today)*100, 1),
                "cheap_p": round(cheapest_h_avg, 1), "cheap_t": cheapest_h_time,
                "w_temp": round(w_res['temperature_2m']), "w_wind": round(w_res['wind_speed_10m']), "w_desc": w_desc,
                "stad": self.settings["stad"]
            }
        except: return None

    def refresh_once(self):
        data = self.get_data()
        if data: self.root.after(0, self.update_display, data)

    def refresh_loop(self):
        while True:
            time.sleep(300)
            self.refresh_once()

    def update_display(self, d):
        # 1. Börspris
        self.cards[0]['price'].config(text=f"{d['spot']:.0f}")
        self.cards[0]['unit'].config(text=f"Kvart: {d['current_time']}")
        self.cards[0]['extra'].config(text="öre/kWh (+moms)")

        # 2. Total
        color = "#059669" if d['diff'] < -5 else "#b91c1c" if d['diff'] > 5 else "#334155"
        self.cards[1]['frame'].config(bg=color)
        for w in self.cards[1]['frame'].winfo_children(): w.config(bg=color)
        self.cards[1]['price'].config(text=f"{d['total']:.0f}")
        self.cards[1]['unit'].config(text=f"{d['diff']}% mot snitt")
        self.cards[1]['extra'].config(text="öre/kWh (inkl allt)")

        # 3. Billigaste
        self.cards[2]['price'].config(text=f"{d['cheap_p']:.0f}")
        self.cards[2]['unit'].config(text="Bästa fönster (1h):")
        self.cards[2]['extra'].config(text=f"{d['cheap_t']}")

        # 4. Snitt
        self.cards[3]['price'].config(text=f"{d['avg_today']:.0f}")
        self.cards[3]['unit'].config(text="öre/kWh (snitt)")
        self.cards[3]['extra'].config(text="Hela dygnet")

        # 5. Väder
        self.cards[4]['frame'].winfo_children()[0].config(text=d['stad'].upper())
        self.cards[4]['price'].config(text=f"{d['w_temp']}°")
        self.cards[4]['unit'].config(text=d['w_desc'])
        self.cards[4]['extra'].config(text=f"Vind: {d['w_wind']} m/s\nUppd: {datetime.now().strftime('%H:%M')}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ElprisApp(root)
    root.mainloop()