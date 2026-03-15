# iPIXEL LED Display - Bluetooth Connection Test

## מבחן חיבור Bluetooth ל-iPIXEL

### מטרה
פרוטוטייפ Python פשוט לבדיקת חיבור ישיר למסך LED iPIXEL דרך Bluetooth.
המטרה היא לבדוק את החיבור הבסיסי ולאבחן את הבעיה "NO SERVICE".

### דרישות מערכת

1. **Python 3.7+**
2. **Bluetooth מופעל במחשב**
3. **מסך iPIXEL דלוק וזמין**

### התקנה

#### Windows
```bash
# התקן Python (אם לא מותקן)
# הורד מ: https://www.python.org/downloads/

# התקן את הספריה הנדרשת
pip install -r requirements.txt
```

#### Linux
```bash
sudo apt-get install python3-pip bluez
pip3 install -r requirements.txt
```

#### macOS
```bash
pip3 install -r requirements.txt
```

### הרצת הבדיקה

```bash
python bluetooth_test.py
```

### מה הסקריפט בודק?

1. **סריקת התקנים** - מחפש את כל התקני הבלוטות' הזמינים
2. **זיהוי iPIXEL** - מחפש התקנים עם שמות רלוונטיים (pixel, dot, matrix)
3. **חיבור** - מתחבר להתקן באמצעות Bleak
4. **גילוי שירותים** - מנסה לקבל את רשימת השירותים של GATT
5. **בדיקת UUID** - מוודא שקיים השירות של iPIXEL
6. **בדיקת כתיבה** - מנסה לשלוח פקודה פשוטה

### פלט צפוי

```
============================================================
iPIXEL Bluetooth Connection Test
============================================================

🔍 Scanning for Bluetooth devices...

📱 Found X devices:
1. Device Name - AA:BB:CC:DD:EE:FF
2. ...

🔎 Looking for iPIXEL/iDotMatrix devices...

🎯 Found potential iPIXEL device(s):
   iPIXEL-XXXX - AA:BB:CC:DD:EE:FF

🔌 Attempting to connect to AA:BB:CC:DD:EE:FF...
✅ Connected: True

📋 Discovering services...

🎯 Found X services:

Service: 0000fa01-0000-1000-8000-00805f9b34fb
  Description: Unknown
  └─ Characteristic: 0000fa02-0000-1000-8000-00805f9b34fb
     Properties: write, write-without-response
  └─ Characteristic: 0000fa03-0000-1000-8000-00805f9b34fb
     Properties: notify

🎉 iPIXEL Service found: 0000fa01-0000-1000-8000-00805f9b34fb

✏️  Testing write capability...
✅ Write successful!
```

### בעיות אפשריות ופתרונות

#### "No devices found"
- ודא שהבלוטות' פועל במחשב
- ודא שמסך ה-iPIXEL דלוק
- נסה לעבור למסך ההגדרות של iPIXEL ולוודא שהוא במצב זמין

#### "Connection error: BleakError"
- נסה לכבות ולהדליק את המסך
- נסה להתנתק ממכשירים אחרים המחוברים למסך
- נסה להפעיל מחדש את שירות הבלוטות' במחשב

#### "iPIXEL Service NOT found"
- זו הבעיה שאנחנו מנסים לפתור!
- הסקריפט יציג את כל השירותים הזמינים
- נשתמש במידע הזה כדי לאבחן מדוע השירות לא נמצא

### קבצים בפרויקט

- `bluetooth_test.py` - סקריפט הבדיקה הראשי
- `requirements.txt` - רשימת ספריות Python נדרשות
- `diagnostic.html` - כלי אבחון Web Bluetooth (לא עבד)
- `index.html` - דף בית
- `ledsign_controller.py` - בקר Python מלא (בפיתוח)

### UUIDs של iPIXEL

```python
SERVICE_UUID = "0000fa01-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "0000fa02-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fa03-0000-1000-8000-00805f9b34fb"
```

### מקורות

- [iPIXEL Protocol Docs](https://github.com/derkalle4/python3-idotmatrix-client)
- [Bleak Documentation](https://bleak.readthedocs.io/)
- [Web Bluetooth API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API)

---

**הערה**: זהו כלי אבחון בלבד. לאחר פתרון בעיית החיבור, נשתמש ב-`ledsign_controller.py` לשליטה מלאה במסך.
