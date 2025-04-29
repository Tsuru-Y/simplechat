# lambda/index.py
import json
import os
import urllib.request
import re  # 正規表現モジュールをインポート

# Lambda コンテキストからリージョンを抽出する関数（必要に応じて使用）
def extract_region_from_arn(arn):
   # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
   match = re.search('arn:aws:lambda:([^:]+):', arn)
   if match:
       return match.group(1)
   return "us-east-1"  # デフォルト値

# 外部APIのURL（Google Colabで立てたFast APIのエンドポイント）
# 注意：動作確認後はAPIを停止するため、このURLは動作しなくなります
API_URL = "https://f8ab-35-225-117-190.ngrok-free.app/"  # ← ここに実際のngrokのURLを入力

def lambda_handler(event, context):
   try:
       print("Received event:", json.dumps(event))
       
       # Cognitoで認証されたユーザー情報を取得（元のコードを継承）
       user_info = None
       if 'requestContext' in event and 'authorizer' in event['requestContext']:
           user_info = event['requestContext']['authorizer']['claims']
           print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
       
       # リクエストボディの解析
       body = json.loads(event['body'])
       message = body['message']
       conversation_history = body.get('conversationHistory', [])
       
       print("Processing message:", message)
       
       # シンプルな実装：メッセージをそのまま外部APIに送信
       request_data = {
           "message": message
       }
       
       # APIリクエストを準備
       request_headers = {
           "Content-Type": "application/json"
       }
       
       request_body = json.dumps(request_data).encode('utf-8')
       
       # urllib.requestを使ってAPIを呼び出す
       req = urllib.request.Request(
           API_URL, 
           data=request_body,
           headers=request_headers,
           method="POST"
       )
       
       print("Calling external API with payload:", json.dumps(request_data))
       
       # APIを呼び出して応答を取得
       try:
           with urllib.request.urlopen(req) as response:
               api_response = json.loads(response.read().decode('utf-8'))
               print("API response:", json.dumps(api_response))
               
               # APIからの応答を取得
               assistant_response = api_response.get('response', 'No response from external API')
       except urllib.error.URLError as e:
           print(f"API call failed: {str(e)}")
           raise Exception(f"Failed to call external API: {str(e)}")
       
       # 会話履歴の更新（元のコードの形式を維持）
       messages = conversation_history.copy()
       
       # ユーザーメッセージを追加
       messages.append({
           "role": "user",
           "content": message
       })
       
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
