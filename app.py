# 0528 
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageAction
import sqlite3
import os
from datetime import datetime
import logging
#
app = Flask(__name__)

# 設置 Channel Access Token 和 Channel Secret
# line_bot_api = LineBotApi('')
# handler = WebhookHandler('a8a76843cdb27f5cf9c0f72958cb9e4e')  # 你需要將這個值替換為你的 Channel Secret

# 設置 Channel Access Token 和 Channel Secret
# LINE_CHANNEL_ACCESS_TOKEN = os.getenv('dR8PuPiW2RtOoJiBdPttAWPYH4hLrc0VJZBUGyMh3p2t9ySc+ktRH91CbyBc62kXEJJbCM4QyFZQm6HhatTLZlCvtDPfF2honnDhtCZLuS8gMkt9rmh+Cc/R+UDPJiYRyXEnJQ2j6uATOaSDGCSSdQdB04t89/1O/w1cDnyilFU=', 'dR8PuPiW2RtOoJiBdPttAWPYH4hLrc0VJZBUGyMh3p2t9ySc+ktRH91CbyBc62kXEJJbCM4QyFZQm6HhatTLZlCvtDPfF2honnDhtCZLuS8gMkt9rmh+Cc/R+UDPJiYRyXEnJQ2j6uATOaSDGCSSdQdB04t89/1O/w1cDnyilFU=')
# LINE_CHANNEL_SECRET = os.getenv('a8a76843cdb27f5cf9c0f72958cb9e4e', 'a8a76843cdb27f5cf9c0f72958cb9e4e')


# Channel Access Token
# line_bot_api = LineBotApi('dR8PuPiW2RtOoJiBdPttAWPYH4hLrc0VJZBUGyMh3p2t9ySc+ktRH91CbyBc62kXEJJbCM4QyFZQm6HhatTLZlCvtDPfF2honnDhtCZLuS8gMkt9rmh+Cc/R+UDPJiYRyXEnJQ2j6uATOaSDGCSSdQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
# handler = WebhookHandler('a8a76843cdb27f5cf9c0f72958cb9e4e')

# Channel Access Token
line_bot_api = LineBotApi('dR8PuPiW2RtOoJiBdPttAWPYH4hLrc0VJZBUGyMh3p2t9ySc+ktRH91CbyBc62kXEJJbCM4QyFZQm6HhatTLZlCvtDPfF2honnDhtCZLuS8gMkt9rmh+Cc/R+UDPJiYRyXEnJQ2j6uATOaSDGCSSdQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('a8a76843cdb27f5cf9c0f72958cb9e4e'
# 初始化資料庫
def init_db():
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        amount INTEGER NOT NULL,
        date TEXT NOT NULL
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_state (
        user_id TEXT PRIMARY KEY,
        state TEXT,
        category TEXT
    )
    ''')
    conn.commit()
    conn.close()
    logging.info("資料庫初始化完成")

# 插入交易記錄
def insert_transaction(user_id, trans_type, category, amount, date):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('INSERT INTO transactions (user_id, type, category, amount, date) VALUES (?, ?, ?, ?, ?)', (user_id, trans_type, category, amount, date))
    conn.commit()
    conn.close()

# 查詢今天總支出
def query_today_total(user_id, date):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND date = ? AND type = "支出"', (user_id, date))
    total_expense = c.fetchone()[0] or 0
    conn.close()
    return total_expense

# 查詢本月結餘
def query_monthly_balance(user_id, month):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND date LIKE ? AND type = "支出"', (user_id, f'{month}%'))
    total_expense = c.fetchone()[0] or 0
    c.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND date LIKE ? AND type = "收入"', (user_id, f'{month}%'))
    total_income = c.fetchone()[0] or 0
    conn.close()
    balance = total_income - total_expense
    return total_income, total_expense, balance

# 更新用戶狀態
def update_user_state(user_id, state, category=None):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('REPLACE INTO user_state (user_id, state, category) VALUES (?, ?, ?)', (user_id, state, category))
    conn.commit()
    conn.close()

# 獲取用戶狀態
def get_user_state(user_id):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT state, category FROM user_state WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (None, None)

# 清除用戶狀態
def clear_user_state(user_id):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('DELETE FROM user_state WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# 生成模板訊息
def generate_template_message(alt_text, title, text, actions):
    return TemplateSendMessage(
        alt_text=alt_text,
        template=ButtonsTemplate(
            title=title,
            text=text,
            actions=actions
        )
    )

# 配置日誌
logging.basicConfig(level=logging.INFO)

@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logging.info(f'Request body: {body}')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logging.error('Invalid signature. Check your channel access token/channel secret.')
        return 'Signature verification failed', 400

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message = event.message.text
    reply_token = event.reply_token
    
    user_state, category = get_user_state(user_id)
    logging.info(f'User state: {user_state}, Category: {category}, Message: {message}')

    if message == "記帳":
        actions = [
            MessageAction(label="支出", text="支出"),
            MessageAction(label="收入", text="收入")
        ]
        response_message = generate_template_message("記帳", "記帳選單", "請選擇支出或收入", actions)
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "支出":
        update_user_state(user_id, "支出選擇中")
        actions = [
            MessageAction(label="飲食類", text="飲食類"),
            MessageAction(label="日常類", text="日常類"),
            MessageAction(label="娛樂類", text="娛樂類"),
            MessageAction(label="其他", text="其他")
        ]
        response_message = generate_template_message("支出", "支出選單", "請選擇支出類別", actions)
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "收入":
        update_user_state(user_id, "收入輸入中")
        response_message = TextSendMessage(text="請輸入收入金額，例如: 收入 1000 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "查看帳本":
        actions = [
            MessageAction(label="查詢本日累積", text="查詢本日累積"),
            MessageAction(label="統計本月結餘", text="統計本月結餘")
        ]
        response_message = generate_template_message("查看帳本", "查看帳本選單", "請選擇查詢方式", actions)
        line_bot_api.reply_message(reply_token, response_message)
    elif user_state == "支出選擇中" and message in ["飲食類", "日常類", "娛樂類", "其他"]:
        update_user_state(user_id, "支出金額輸入中", message)
        response_message = TextSendMessage(text=f"請輸入 {message} 支出金額，例如: {message} 100 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif user_state == "支出金額輸入中" and category:
        try:
            amount = int(message.replace("元", "").strip())
            date = datetime.now().strftime("%Y-%m-%d")
            insert_transaction(user_id, "支出", category, amount, date)
            response_message = TextSendMessage(text=f"已記錄 {category} 支出 {amount} 元")
            clear_user_state(user_id)
        except ValueError:
            logging.error(f"金額解析失敗: {message}")
            response_message = TextSendMessage(text="請確保金額為有效的整數，例如: 飲食類 100 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif user_state == "收入輸入中":
        try:
            amount = int(message.replace("元", "").strip())
            date = datetime.now().strftime("%Y-%m-%d")
            insert_transaction(user_id, "收入", "收入", amount, date)
            response_message = TextSendMessage(text=f"已記錄收入 {amount} 元")
            clear_user_state(user_id)
        except ValueError:
            logging.error(f"金額解析失敗: {message}")
            response_message = TextSendMessage(text="請確保金額為有效的整數，例如: 收入 1000 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "查詢本日累積":
        date = datetime.now().strftime("%Y-%m-%d")
        total_expense = query_today_total(user_id, date)
        response_message = TextSendMessage(text=f"今日支出總和為 {total_expense} 元" if total_expense > 0 else "目前並無紀錄！")
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "統計本月結餘":
        month = datetime.now().strftime("%Y-%m")
        total_income, total_expense, balance = query_monthly_balance(user_id, month)
        if total_income == 0 and total_expense == 0:
            response_message = TextSendMessage(text="目前並無紀錄！")
        else:
            response_message = TextSendMessage(text=f"本月收入總和為 {total_income} 元，支出總和為 {total_expense} 元，結餘為 {balance} 元")
        line_bot_api.reply_message(reply_token, response_message)
    else:
        response_message = TextSendMessage(text="無效的指令")
        line_bot_api.reply_message(reply_token, response_message)

if __name__ == '__main__':
    init_db()
    app.run(port=5000)
