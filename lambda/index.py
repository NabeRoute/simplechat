# lambda/index.py
import json
import os
import urllib.request
import urllib.parse
import re
from botocore.exceptions import ClientError

# ローカルAPIのエンドポイント
LOCAL_API_ENDPOINT = "https://3c13-35-194-174-91.ngrok-free.app"

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # 会話履歴を使用
        messages = conversation_history.copy()
        
        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })
        
        # ローカルAPI用のリクエストペイロードを構築
        request_payload = {
            "prompt": message,
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }
        
        # リクエストヘッダーの設定
        headers = {
            'Content-Type': 'application/json'
        }
        
        # リクエストの作成
        req = urllib.request.Request(
            f"{LOCAL_API_ENDPOINT}/generate",
            data=json.dumps(request_payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        print("Calling local API with payload:", json.dumps(request_payload))
        
        # APIを呼び出し
        with urllib.request.urlopen(req) as response:
            response_body = json.loads(response.read().decode('utf-8'))
            print("Local API response:", json.dumps(response_body))
            
            # 応答の検証
            if not response_body.get('generated_text'):
                raise Exception("No response content from the model")
            
            # アシスタントの応答を取得
            assistant_response = response_body['generated_text']
            
            # アシスタントの応答を会話履歴に追加
            messages.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            # 成功レスポンスの返却
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
                "body": json.dumps({
                    "success": True,
                    "response": assistant_response,
                    "conversationHistory": messages
                })
            }
            
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
