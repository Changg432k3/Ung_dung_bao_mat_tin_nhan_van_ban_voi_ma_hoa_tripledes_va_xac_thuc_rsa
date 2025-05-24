import socket
import threading
import json
import base64
import os
import datetime
from tkinter import *
from tkinter import scrolledtext, messagebox, ttk # Import ttk
from tkinter.font import Font # Import Font để tùy chỉnh font

import crypto_utils as crypto

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True

        self.alice_private_key, self.alice_public_key = crypto.generate_rsa_keys()
        self.bob_public_key = None
        self.plaintext_3des_key = None
        self.iv = None

        self.setup_gui()
        self.connect_to_server()

    def setup_gui(self):
        self.root = Tk()
        self.root.title("Alice's Secure Chat (Client)")
        self.root.geometry("700x600") # Tăng kích thước cửa sổ
        self.root.configure(bg="#2E3440") # Màu nền tối

        # Define custom fonts
        self.title_font = Font(family="Helvetica", size=18, weight="bold")
        self.message_font = Font(family="Segoe UI", size=10)
        self.log_font = Font(family="Consolas", size=9) # Font cho log kỹ thuật
        self.input_font = Font(family="Arial", size=11)

        # Style for ttk widgets
        style = ttk.Style()
        style.theme_use("clam") # Sử dụng theme "clam" hoặc "alt", "default", "vista", "xpnative"
        style.configure("TFrame", background="#3B4252")
        style.configure("TLabel", background="#3B4252", foreground="#ECEFF4", font=self.input_font)
        style.configure("TEntry", fieldbackground="#4C566A", foreground="#ECEFF4", borderwidth=0)
        style.map('TEntry', fieldbackground=[('focus', '#5E81AC')])
        style.configure("TButton", background="#5E81AC", foreground="#ECEFF4", font=self.input_font, borderwidth=0)
        style.map("TButton", background=[('active', '#88C0D0')])

        # Main Frame
        main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        main_frame.grid(row=0, column=0, sticky=(N, S, E, W))
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Chat Log
        self.chat_log_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
        self.chat_log_frame.grid(row=0, column=0, columnspan=2, sticky=(N, S, E, W), pady=(0, 10))
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.chat_log = scrolledtext.ScrolledText(self.chat_log_frame, width=70, height=20, state='disabled',
                                                 bg="#2E3440", fg="#ECEFF4", font=self.message_font,
                                                 insertbackground="#ECEFF4", borderwidth=0, relief="flat")
        self.chat_log.pack(side=LEFT, fill=BOTH, expand=True)

        # Message Input
        input_frame = ttk.Frame(main_frame, padding="5 5 5 5")
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(E, W))
        input_frame.grid_columnconfigure(1, weight=1)

        self.msg_label = ttk.Label(input_frame, text="Message:")
        self.msg_label.grid(row=0, column=0, padx=(0, 5))
        
        self.msg_entry = ttk.Entry(input_frame, width=60, font=self.input_font)
        self.msg_entry.grid(row=0, column=1, sticky=(E, W))
        self.msg_entry.bind("<Return>", self.send_message_from_gui)

        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message_from_gui)
        self.send_button.grid(row=0, column=2, padx=(5, 0))

        # Status Bar
        self.status_label = ttk.Label(main_frame, text="Connecting...", anchor=W, font=self.log_font)
        self.status_label.grid(row=2, column=0, columnspan=2, sticky=(E, W), pady=(10, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log_message(self, sender, message, color="#88C0D0"):
        self.chat_log.config(state='normal')
        
        if sender == "Bob":
            self.chat_log.insert(END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {sender}: ", "bob_tag")
            self.chat_log.insert(END, f"{message}\n", "bob_msg_tag")
        elif sender == "Alice (Sent)":
            self.chat_log.insert(END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] You: ", "self_tag")
            self.chat_log.insert(END, f"{message}\n", "self_msg_tag")
        else: # System messages, Handshake, Verification, Error
            self.chat_log.insert(END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {sender}: {message}\n", "info_tag")
        
        self.chat_log.tag_config("bob_tag", foreground="#A3BE8C", font=self.message_font, justify='left')
        self.chat_log.tag_config("bob_msg_tag", foreground="#ECEFF4", background="#3B4252", font=self.message_font, justify='left')
        self.chat_log.tag_config("self_tag", foreground="#81A1C1", font=self.message_font, justify='right')
        self.chat_log.tag_config("self_msg_tag", foreground="#ECEFF4", background="#4C566A", font=self.message_font, justify='right')
        self.chat_log.tag_config("info_tag", foreground="#BF616A", font=self.log_font, justify='left')

        self.chat_log.config(state='disabled')
        self.chat_log.yview(END)

    def connect_to_server(self):
        threading.Thread(target=self._connect_and_handshake, daemon=True).start()

    def _connect_and_handshake(self):
        try:
            self.log_message("System", f"Attempting to connect to {self.host}:{self.port}...")
            self.client_socket.connect((self.host, self.port))
            self.status_label.config(text="Connected to Server. Performing Handshake...")
            self.log_message("System", "Connected to Bob.")

            # 1. Gửi khóa công khai của Alice
            alice_public_key_pem = crypto.serialize_public_key(self.alice_public_key)
            handshake_data = {"alice_public_key": alice_public_key_pem}
            self.client_socket.sendall(json.dumps(handshake_data).encode('utf-8'))
            self.log_message("Handshake", "Sent Alice's Public Key.")

            # 2. Nhận khóa công khai của Bob
            bob_public_key_pem = self.client_socket.recv(4096).decode('utf-8')
            self.bob_public_key = crypto.deserialize_public_key(bob_public_key_pem)
            self.log_message("Handshake", "Received Bob's Public Key.")

            # 3. Tạo và gửi gói tin trao đổi khóa
            self.plaintext_3des_key = os.urandom(24)
            self.iv = os.urandom(8)
            encrypted_3des_key = crypto.encrypt_3des_key(self.plaintext_3des_key, self.bob_public_key)

            current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            signed_info = f"Alice_{current_time_str}".encode('utf-8')
            signature = crypto.sign_data(signed_info, self.alice_private_key)

            key_exchange_packet = {
                "original_signed_info_data": signed_info.decode('utf-8'),
                "signed_info": signature,
                "encrypted_3des_key": encrypted_3des_key
            }
            self.client_socket.sendall(json.dumps(key_exchange_packet).encode('utf-8'))
            self.log_message("Key Exchange", "Sent Key Exchange Packet.")
            self.status_label.config(text="Handshake complete. Ready to send messages.")

            # Vòng lặp nhận phản hồi và tin nhắn từ Bob
            threading.Thread(target=self._receive_messages, daemon=True).start()

        except ConnectionRefusedError:
            self.log_message("Error", "Connection refused. Is Bob's server running?")
            self.status_label.config(text="Connection Failed. Restart to retry.")
            self.running = False
        except Exception as e:
            self.log_message("Error", f"Error during connection/handshake: {e}")
            self.running = False
        if not self.running:
            self.root.quit()

    def _receive_messages(self):
        while self.running:
            try:
                response = self.client_socket.recv(4096).decode('utf-8')
                if not response:
                    break
                
                try:
                    # Check if it's an ACK/NACK or an encrypted message from Bob
                    if response in ["ACK", "NACK"]:
                        self.log_message("Bob (Response)", response)
                    else:
                        encrypted_packet = json.loads(response)
                        iv_b64 = encrypted_packet["iv"]
                        ciphertext_b64 = encrypted_packet["cipher"]
                        message_hash_received = encrypted_packet["hash"]
                        signature_msg_b64 = encrypted_packet["sig"]

                        decrypted_iv_bytes = base64.b64decode(iv_b64)
                        ciphertext_bytes = base64.b64decode(ciphertext_b64)

                        computed_hash = crypto.create_hash_from_iv_ciphertext(decrypted_iv_bytes, ciphertext_bytes)
                        integrity_check = computed_hash == message_hash_received

                        decrypted_message_bytes = crypto.decrypt_message(ciphertext_b64, self.plaintext_3des_key, decrypted_iv_bytes)
                        decrypted_message_str = decrypted_message_bytes.decode('utf-8')
                        
                        is_valid_msg_signature = crypto.verify_signature(
                            decrypted_message_bytes,
                            signature_msg_b64,
                            self.bob_public_key
                        )

                        self.log_message("Bob", f"{decrypted_message_str}")
                        self.log_message("Verification (Alice)", f"  Integrity: {'OK' if integrity_check else 'FAILED'} (Hash: {computed_hash[:10]}... {'!=' if not integrity_check else '=='} {message_hash_received[:10]}...)")
                        self.log_message("Verification (Alice)", f"  Signature: {'OK' if is_valid_msg_signature else 'FAILED'}")

                except json.JSONDecodeError:
                    self.log_message("Error", "Received non-JSON data or malformed packet from Bob.")
                except Exception as ex:
                    self.log_message("Error", f"Processing Bob's message failed: {ex}")

            except Exception as e:
                if self.running:
                    self.log_message("Error", f"Error receiving response: {e}")
                break
        self.log_message("System", "Disconnected from server. Please restart.")
        if self.running:
             self.status_label.config(text="Disconnected. Please restart.")


    def send_message_from_gui(self, event=None):
        message = self.msg_entry.get()
        if not message:
            return
        if not self.client_socket:
            self.log_message("Error", "Not connected to server.")
            return
        if not self.plaintext_3des_key or not self.iv or not self.bob_public_key:
            self.log_message("Error", "Secure channel not established yet. Please wait for handshake.")
            return

        try:
            ciphertext = crypto.encrypt_message(message.encode('utf-8'), self.plaintext_3des_key, self.iv)
            
            iv_bytes = self.iv
            ciphertext_bytes = base64.b64decode(ciphertext)
            message_hash = crypto.create_hash_from_iv_ciphertext(iv_bytes, ciphertext_bytes)
            
            signature_msg = crypto.sign_data(message.encode('utf-8'), self.alice_private_key)

            encrypted_packet = {
                "iv": base64.b64encode(self.iv).decode('utf-8'),
                "cipher": ciphertext,
                "hash": message_hash,
                "sig": signature_msg
            }
            self.client_socket.sendall(json.dumps(encrypted_packet).encode('utf-8'))
            self.log_message("Alice (Sent)", message)
            self.msg_entry.delete(0, END)

        except Exception as e:
            self.log_message("Error", f"Error sending message: {e}")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.running = False
            if self.client_socket:
                self.client_socket.close()
            self.root.destroy()

if __name__ == "__main__":
    HOST = 'localhost'
    PORT = 12345
    client = ChatClient(HOST, PORT)
    client.root.mainloop()