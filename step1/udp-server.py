import socket
import threading
import time
import os

HOST = '0.0.0.0'  # すべての利用可能なインターフェースをリッスン
PORT = 9999       # 任意のポート番号

# クライアント情報を保存する辞書: { (address, port): last_seen_timestamp }
# UDPはコネクションレスなので、"接続中"のクライアントは最後にメッセージを受信したクライアントと見なします。
clients = {}
CLIENT_TIMEOUT = 600  # クライアントが非アクティブと見なされるまでの秒数 (例: 10分)

def clean_old_clients():
    """一定期間メッセージがないクライアントをリストから削除する"""
    while True:
        current_time = time.time()
        clients_to_remove = []

        # clients辞書の中の各要素を一つずつ順番に取り出します
        for addr, last_seen in clients.items():
            # 取り出した要素が、非アクティブという条件を満たしているかチェックします
            if current_time - last_seen > CLIENT_TIMEOUT:
                clients_to_remove.append(addr)

        for addr in clients_to_remove:
            print(f"クライアント {addr} が非アクティブのため削除されました。")
            del clients[addr]
        time.sleep(60) # 1分ごとにクリーンアップチェックを実行

def handle_message(data, address, server_socket):
    """受信したメッセージを処理し、他のクライアントにリレーする"""
    try:
        # メッセージプロトコルの解析

        # 最初の1バイトがユーザー名の長さ
        usernamelen = data[0]
        # ユーザー名とメッセージを抽出
        username_bytes = data[1 : 1 + usernamelen]
        message_bytes = data[1 + usernamelen :]

        username = username_bytes.decode('utf-8')
        message = message_bytes.decode('utf-8')

        print(f"[{time.strftime('%H:%M:%S')}] {username} ({address[0]}:{address[1]}): {message}")

        # クライアント情報を更新
        clients[address] = time.time()

        # 全ての接続中のクライアントにメッセージをリレー
        for client_addr in list(clients.keys()): # ループ処理中にクライアント情報が変更される可能性があるのでlist()でコピー
            if client_addr != address: # 送信元以外のクライアントに送る
                try:
                    # リレーするメッセージは 'ユーザー名: メッセージ' の形式で整形
                    relay_message = f"{username}: {message}".encode('utf-8')
                    # ユーザー名の長さ+ユーザー名+メッセージのプロトコルに合わせる必要はない
                    # 単純なチャットメッセージとして送る
                    server_socket.sendto(relay_message, client_addr)
                except Exception as e:
                    print(f"クライアント {client_addr} へのリレー中にエラーが発生しました: {e}")
                    # エラーが発生したクライアントはリストから削除を検討
                    if client_addr in clients:
                        del clients[client_addr]
    except IndexError:
        print(f"不正なメッセージ形式を受信しました ({len(data)}バイト): {data} from {address}")
    except UnicodeDecodeError:
        print(f"UTF-8デコードエラーが発生しました from {address}: {data}")
    except Exception as e:
        print(f"メッセージ処理中に不明なエラーが発生しました from {address}: {e}")

def start_server():
    """UDPサーバーを起動し、着信接続を待ち受ける"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))
    print(f"サーバーが {HOST}:{PORT} で起動し、着信接続を待ち受け中です。")
    print("チャットサービスが稼働しています。")

    # クライアントのクリーンアップをバックグラウンドスレッドで開始
    cleanup_thread = threading.Thread(target=clean_old_clients, daemon=True)
    cleanup_thread.start()

    try:
        while True:
            # 最大4096バイトのデータを受信
            data, address = server_socket.recvfrom(4096)
            # 新しいスレッドでメッセージを処理
            message_thread = threading.Thread(target=handle_message, args=(data, address, server_socket))
            message_thread.start()
    except KeyboardInterrupt:
        print("\nサーバーをシャットダウンしています...")
    finally:
        server_socket.close()
        print("サーバーソケットが閉じられました。")

if __name__ == "__main__":
    start_server()