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
 account = {}   
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text
    print('hi')
    if text.startswith("記帳"):
        # 假設格式為 "記帳 XXX 元"
        try:
            amount = int(text.split(" ")[1])
            if user_id in accounts:
                accounts[user_id].append(amount)
            else:
                accounts[user_id] = [amount]
            reply_text = f"已記錄：{amount} 元"
        except (IndexError, ValueError):
            reply_text = "格式錯誤！請使用 '記帳 XXX 元'"
    elif text == "查看帳本":
        if user_id in accounts:
            total = sum(accounts[user_id])
            reply_text = f"目前總計：{total} 元"
        else:
            reply_text = "目前無任何記錄"
    else:
        reply_text = "請使用 '記帳 XXX 元' 來記錄消費，或使用 '查看帳本' 來查看總計"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
        
        
import os
if __name__ == "__main__":
    # port = int(os.environ.get('PORT', 5000))
    app.run(debug = True, host='0.0.0.0', port=80)
