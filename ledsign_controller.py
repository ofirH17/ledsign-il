#!/usr/bin/env python3
"""
LED Sign Controller - Windows Desktop Application
שולח טקסט למסך LED באמצעות Bluetooth

התקנה:
pip install bleak pillow

הפעלה:
python ledsign_controller.py
"""

import asyncio
import struct
import zlib
from io import BytesIO
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw, ImageFont
from bleak import BleakClient, BleakScanner

# הגדרות המסך
DEVICE_NAME = "LED_BLE_e03ab2ab"
DEVICE_ADDRESS = None  # נמצא אוטומטית

# UUIDs לפי הפרוטוקול של iPIXEL
UUID_WRITE = "0000ffe1-0000-1000-8000-00805f9b34fb"

class LEDSignController:
    def __init__(self, root):
        self.root = root
        self.root.title("LED Sign Controller")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        self.client = None
        self.device_address = None
        
        self.create_gui()
        
    def create_gui(self):
        # כותרת
        title = tk.Label(self.root, text="🚦 שליטה במסך LED", 
                        font=("Arial", 20, "bold"), fg="#4fc3f7")
        title.pack(pady=20)
        
        # מסגרת עבור קלט טקסט
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(input_frame, text="טקסט להצגה:", font=("Arial", 12)).pack(anchor="e")
        
        self.text_entry = tk.Entry(input_frame, font=("Arial", 14), width=30)
        self.text_entry.insert(0, "נהג חדש")
        self.text_entry.pack(pady=5)
        
        # תצוגה מקדימה
        preview_frame = tk.Frame(self.root, bg="#ffff00", height=80)
        preview_frame.pack(pady=10, padx=20, fill="x")
        preview_frame.pack_propagate(False)
        
        self.preview_label = tk.Label(preview_frame, text="נהג חדש",
                                     font=("Arial", 24, "bold"),
                                     bg="#ffff00", fg="#000000")
        self.preview_label.pack(expand=True)
        
        # עדכון תצוגה מקדימה בזמן אמת
        self.text_entry.bind("<KeyRelease>", self.update_preview)
        
        # כפתורים
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        self.connect_btn = tk.Button(btn_frame, text="🔍 חפש וחבר למסך",
                                     font=("Arial", 12, "bold"),
                                     bg="#4fc3f7", fg="white",
                                     width=20, height=2,
                                     command=self.connect_device)
        self.connect_btn.pack(pady=5)
        
        self.send_btn = tk.Button(btn_frame, text="📤 שלח למסך",
                                 font=("Arial", 12, "bold"),
                                 bg="#4caf50", fg="white",
                                 width=20, height=2,
                                 command=self.send_to_display,
                                 state="disabled")
        self.send_btn.pack(pady=5)
        
        # סטטוס
        self.status_label = tk.Label(self.root, text="מחכה לחיבור...",
                                     font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=10)
        
    def update_preview(self, event=None):
        text = self.text_entry.get() or "טקסט"
        self.preview_label.config(text=text)
        
    def set_status(self, message, color="gray"):
        self.status_label.config(text=message, fg=color)
        self.root.update()
        
    def connect_device(self):
        """חיבור למסך LED"""
        self.connect_btn.config(state="disabled")
        self.set_status("מחפש מסך LED...", "blue")
        asyncio.run(self._connect_async())
        
    async def _connect_async(self):
        try:
            # סריקת מכשירים
            devices = await BleakScanner.discover(timeout=10.0)
            
            # חיפוש המסך
            target_device = None
            for d in devices:
                if d.name and ("LED_BLE" in d.name or d.name == DEVICE_NAME):
                    target_device = d
                    break
            
            if not target_device:
                raise Exception("לא נמצא מסך LED. ודא שהמסך דולק ובטווח.")
            
            self.device_address = target_device.address
            self.set_status(f"נמצא: {target_device.name}", "blue")
            
            # חיבור
            self.client = BleakClient(self.device_address)
            await self.client.connect()
            
            if self.client.is_connected:
                self.set_status(f"✅ מחובר ל-{target_device.name}", "green")
                self.send_btn.config(state="normal")
                self.connect_btn.config(text="✅ מחובר")
            else:
                raise Exception("נכשל בחיבור")
                
        except Exception as e:
            self.set_status(f"❌ שגיאה: {str(e)}", "red")
            messagebox.showerror("שגיאת חיבור", str(e))
            self.connect_btn.config(state="normal")
        
    def send_to_display(self):
        """שליחת טקסט למסך"""
        if not self.client or not self.client.is_connected:
            messagebox.showerror("שגיאה", "לא מחובר למסך")
            return
            
        self.send_btn.config(state="disabled")
        text = self.text_entry.get()
        self.set_status(f"שולח: '{text}'...", "blue")
        asyncio.run(self._send_async(text))
        
    async def _send_async(self, text):
        try:
            # יצירת תמונה PNG
            png_data = self.create_text_png(text, 128, 32)
            
            # שליחת פקודות
            await self.send_command([0x05, 0x00, 0x07, 0x01, 0x01])  # Power ON
            await asyncio.sleep(0.2)
            
            await self.send_command([0x05, 0x00, 0x04, 0x80, 100])  # Brightness
            await asyncio.sleep(0.2)
            
            await self.send_png(png_data, 1)  # Send PNG to buffer 1
            await asyncio.sleep(0.5)
            
            await self.send_command([0x05, 0x00, 0x07, 0x80, 0x01])  # Select screen 1
            
            self.set_status(f"✅ נשלח בהצלחה: '{text}'", "green")
            messagebox.showinfo("הצלחה", f"הטקסט '{text}' נשלח למסך!")
            
        except Exception as e:
            self.set_status(f"❌ שגיאה בשליחה: {str(e)}", "red")
            messagebox.showerror("שגיאה", f"נכשל בשליחה: {str(e)}")
        finally:
            self.send_btn.config(state="normal")
            
    async def send_command(self, cmd_bytes):
        """שליחת פקודה למסך"""
        await self.client.write_gatt_char(UUID_WRITE, bytearray(cmd_bytes), response=False)
        
    async def send_png(self, png_data, buffer_num):
        """שליחת PNG למסך"""
        size = len(png_data)
        crc = zlib.crc32(png_data) & 0xFFFFFFFF
        
        # בניית הפקודה
        header_size = 15
        total_len = header_size + size
        
        packet = bytearray()
        packet.extend(struct.pack('<H', total_len))  # Length
        packet.extend([0x02, 0x00])  # Command 0x0002 (PNG)
        packet.append(0x00)  # Reserved
        packet.extend(struct.pack('<I', size))  # Size
        packet.extend(struct.pack('<I', crc))  # CRC32
        packet.append(0x00)  # Reserved
        packet.append(buffer_num)  # Buffer number
        packet.extend(png_data)  # PNG data
        
        # שליחה בחלקים של 20 בייט
        chunk_size = 20
        for i in range(0, len(packet), chunk_size):
            chunk = packet[i:i + chunk_size]
            await self.client.write_gatt_char(UUID_WRITE, chunk, response=False)
            await asyncio.sleep(0.05)
            
    def create_text_png(self, text, width, height):
        """יצירת תמונת PNG עם טקסט"""
        # יצירת תמונה
        image = Image.new('RGB', (width, height), color='#FFFF00')  # רקע צהוב
        draw = ImageDraw.Draw(image)
        
        # מציאת גודל פונט מתאים
        font_size = height - 4
        try:
            # ניסיון להשתמש בפונט שתומך בעברית
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # חישוב מיקום הטקסט במרכז
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # התאמת גודל הפונט אם הטקסט רחב מדי
        while text_width > width - 4 and font_size > 8:
            font_size -= 2
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # רישום הטקסט בשחור
        draw.text((x, y), text, font=font, fill='#000000')
        
        # המרה ל-PNG bytes
        output = BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()

def main():
    root = tk.Tk()
    app = LEDSignController(root)
    root.mainloop()

if __name__ == "__main__":
    main()
