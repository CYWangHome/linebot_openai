from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
import traceback
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
# openai.api_key = os.getenv('OPENAI_API_KEY')


def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="gpt-3.5-turbo-instruct", prompt=text, temperature=0.5, max_tokens=500)
    print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','')
    return answer


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # 獲取請求體
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 處理 webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'
pos_acc = {}
neg_acc = {}
user_states = {}

def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()  # 去除前后的空格

    # 获取用户当前状态
    user_state = user_states.get(user_id, "INIT")

    if user_state == "INIT":
        if text == "記帳":
            reply_text = "請輸入「支出」或「收入」"
            user_states[user_id] = "WAITING_FOR_TYPE"
        elif text == "查看帳本":
            reply_text = get_account_summary(user_id)
        else:
            reply_text = "請使用「記帳」或「查看帳本」"
    elif user_state == "WAITING_FOR_TYPE":
        if text == "收入":
            reply_text = "請輸入'收入 XXX'"
            user_states[user_id] = "WAITING_FOR_AMOUNT_INCOME"
        elif text == "支出":
            reply_text = "請輸入'支出 XXX'"
            user_states[user_id] = "WAITING_FOR_AMOUNT_EXPENSE"
        else:
            reply_text = "格式錯誤！請輸入「支出」或「收入」"
    elif user_state == "WAITING_FOR_AMOUNT_INCOME":
        if text.startswith("收入 "):
            try:
                amount = int(text.split(" ")[1])
                if user_id in pos_acc:
                    pos_acc[user_id].append(amount)
                else:
                    pos_acc[user_id] = [amount]
                reply_text = f"已紀錄收入：{amount} 元"
                user_states[user_id] = "INIT"
            except (IndexError, ValueError):
                reply_text = "格式錯誤！請輸入'收入 XXX'"
        else:
            reply_text = "格式錯誤！請輸入'收入 XXX'"
    elif user_state == "WAITING_FOR_AMOUNT_EXPENSE":
        if text.startswith("支出 "):
            try:
                amount = int(text.split(" ")[1])
                if user_id in neg_acc:
                    neg_acc[user_id].append(amount)
                else:
                    neg_acc[user_id] = [amount]
                reply_text = f"已紀錄支出：{amount} 元"
                user_states[user_id] = "INIT"
            except (IndexError, ValueError):
                reply_text = "格式錯誤！請輸入'支出 XXX'"
        else:
            reply_text = "格式錯誤！請輸入'支出 XXX'"
    else:
        reply_text = "請使用「記帳」或「查看帳本」"

    return reply_text

def get_account_summary(user_id):
    if user_id in pos_acc or user_id in neg_acc:
        pos_total = sum(pos_acc.get(user_id, []))
        neg_total = sum(neg_acc.get(user_id, []))
        total = pos_total - neg_total
        if total > 0:
            return f"目前淨收入：{total} 元"
        elif total == 0:
            return "目前收支平衡"
        else:
            return f"目前透支：{-total} 元"
    else:
        return "目前無任何記錄"
        
        
import os
if __name__ == "__main__":
    # port = int(os.environ.get('PORT', 5000))
    app.run(debug = True, host='0.0.0.0', port=80)
