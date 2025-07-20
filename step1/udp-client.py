import socket
import threading
import os
import sys

SERVER_HOST = '127.0.0.1' # サーバーのIPアドレス
SERVER_PORT = 9999       # サーバーのポート番号

MAX_MESSAGE_SIZE = 4096 # メッセージの最大サイズ (バイト)

def receive_messages(sock):
    """サーバーからのメッセージを受信するスレッド関数"""
    while True:
        try:
            data, _ = sock.recvfrom(MAX_MESSAGE_SIZE)
            message = data.decode('utf-8')
            # 受信したメッセージを新しい行で表示し、現在の入力行を上書きしないようにする
            sys.stdout.write(f"\r{message}\n{current_prompt}")
            sys.stdout.flush()
        except OSError:
            # ソケットが閉じられた場合のエラーを処理
            break
        except Exception as e:
            print(f"メッセージ受信中にエラーが発生しました: {e}")
            break

current_prompt = "" # 現在のプロンプトを保持するためのグローバル変数

def start_client():
    """UDPクライアントを起動し、メッセージの送受信を行う"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.1) # 非ブロッキング受信のために短いタイムアウトを設定

    username = ""
    while not username:
        username = input("ユーザー名を入力してください (最大255バイト): ")
        if not username.encode('utf-8').__len__() > 255:
            break
        else:
            print("ユーザー名が長すぎます。255バイト以下にしてください。")
            username = ""

    print(f"チャットに参加しました: {username}")
    print("メッセージを入力してください (exitで終了します)")

    # メッセージ受信用のスレッドを開始
    receive_thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receive_thread.start()

    try:
        while True:
            global current_prompt
            current_prompt = f"{username}> "
            message = input(current_prompt)

            if message.lower() == "exit":
                break

            # ユーザー名の長さを最初の1バイトにエンコード
            username_bytes = username.encode('utf-8')
            usernamelen = len(username_bytes)

            if usernamelen > 255:
                print("エラー: ユーザー名が255バイトを超えています。")
                continue

            message_bytes = message.encode('utf-8')

            # メッセージの合計サイズをチェック
            total_message_size = 1 + usernamelen + len(message_bytes)
            if total_message_size > MAX_MESSAGE_SIZE:
                print(f"エラー: メッセージが最大サイズ {MAX_MESSAGE_SIZE} バイトを超えています。({total_message_size}バイト)")
                continue

            # プロトコルに従ってバイトデータを構築
            # bytearrayを使用して可変長のバイトデータを作成
            send_data = bytearray()
            send_data.append(usernamelen) # ユーザー名の長さを1バイトで追加
            send_data.extend(username_bytes) # ユーザー名バイトを追加
            send_data.extend(message_bytes) # メッセージバイトを追加

            sock.sendto(send_data, (SERVER_HOST, SERVER_PORT))

    except KeyboardInterrupt:
        print("\nクライアントを終了します...")
    finally:
        sock.close()
        print("ソケットが閉じられました。")
        sys.exit(0) # クリーンに終了

if __name__ == "__main__":
    start_client()