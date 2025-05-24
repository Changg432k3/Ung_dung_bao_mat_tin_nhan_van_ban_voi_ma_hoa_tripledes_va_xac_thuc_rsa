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

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Cho phép tái sử dụng địa chỉ
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.client_socket = None
        self.running = True

        self.bob_private_key, self.bob_public_key = crypto.generate_rsa_keys()
        self.alice_public_key = None
        self.decrypted_3des_key = None
        self.iv = None

        self.setup_gui()
        self.start_listening()

    def setup_gui(self):
        self.root = Tk()
        self.root.title("Bob's Secure Chat (Server)")
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
        style.map('TEntry', fieldbackground=[('focus', '#5E81AC')]) # Change color on focus
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
        self.status_label = ttk.Label(main_frame, text=f"Listening on {self.host}:{self.port}...", anchor=W, font=self.log_font)
        self.status_label.grid(row=2, column=0, columnspan=2, sticky=(E, W), pady=(10, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log_message(self, sender, message, color="#88C0D0"): # Default color for system/info messages
        self.chat_log.config(state='normal')
        
        # Add tag for specific sender colors
        if sender == "Alice":
            self.chat_log.insert(END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {sender}: ", "alice_tag")
            self.chat_log.insert(END, f"{message}\n", "alice_msg_tag")
        elif sender == "Bob (Sent)":
            self.chat_log.insert(END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] You: ", "self_tag")
            self.chat_log.insert(END, f"{message}\n", "self_msg_tag")
        else: # System messages, Handshake, Verification, Error
            self.chat_log.insert(END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {sender}: {message}\n", "info_tag")
        
        # Configure tags for colors and alignment
        self.chat_log.tag_config("alice_tag", foreground="#A3BE8C", font=self.message_font, justify='left') # Greenish for Alice name
        self.chat_log.tag_config("alice_msg_tag", foreground="#ECEFF4", background="#3B4252", font=self.message_font, justify='left') # Light text on dark background
        self.chat_log.tag_config("self_tag", foreground="#81A1C1", font=self.message_font, justify='right') # Blueish for 'You' name
        self.chat_log.tag_config("self_msg_tag", foreground="#ECEFF4", background="#4C566A", font=self.message_font, justify='right') # Darker background for own messages
        self.chat_log.tag_config("info_tag", foreground="#BF616A", font=self.log_font, justify='left') # Redish for info/error

        self.chat_log.config(state='disabled')
        self.chat_log.yview(END)

    def start_listening(self):
        threading.Thread(target=self._listen_for_connection, daemon=True).start()

    def _listen_for_connection(self):
        try:
            self.log_message("System", "Waiting for Alice to connect...")
            self.client_socket, client_address = self.server_socket.accept()
            self.log_message("System", f"Alice connected from {client_address}")
            threading.Thread(target=self._handle_client, daemon=True).start()
        except Exception as e:
            if self.running:
                self.log_message("Error", f"Error listening for connection: {e}")
            self.running = False
            self.root.quit()

    def _handle_client(self):
        try:
            # 1. Nhận gói tin Handshake và khóa công khai của Alice
            handshake_data_json = self.client_socket.recv(4096).decode('utf-8')
            handshake_data = json.loads(handshake_data_json)
            self.alice_public_key = crypto.deserialize_public_key(handshake_data["alice_public_key"])
            self.log_message("Handshake", "Received Alice's Public Key.")

            # 2. Gửi khóa công khai của Bob
            bob_public_key_pem = crypto.serialize_public_key(self.bob_public_key)
            self.client_socket.sendall(bob_public_key_pem.encode('utf-8'))
            self.log_message("Handshake", "Sent Bob's Public Key to Alice.")

            # 3. Nhận gói tin trao đổi khóa
            key_exchange_packet_json = self.client_socket.recv(4096).decode('utf-8')
            key_exchange_packet = json.loads(key_exchange_packet_json)

            signed_info_b64 = key_exchange_packet["signed_info"]
            encrypted_3des_key_b64 = key_exchange_packet["encrypted_3des_key"]
            original_signed_info_str = key_exchange_packet.get("original_signed_info_data", "")
            original_signed_info_bytes = original_signed_info_str.encode('utf-8')

            self.decrypted_3des_key = crypto.decrypt_3des_key(encrypted_3des_key_b64, self.bob_private_key)

            is_valid_key_exchange_signature = crypto.verify_signature(
                original_signed_info_bytes,
                signed_info_b64,
                self.alice_public_key
            )
            self.log_message("Key Exchange", f"3DES Key decrypted. Alice's signature valid: {is_valid_key_exchange_signature}")
            if not is_valid_key_exchange_signature:
                self.log_message("Key Exchange", "Warning: Key exchange signature invalid!")

            self.log_message("System", "Secure channel established. Ready to receive messages.")

            # Vòng lặp nhận tin nhắn
            while self.running:
                encrypted_packet_json = self.client_socket.recv(4096).decode('utf-8')
                if not encrypted_packet_json:
                    break
                
                try:
                    encrypted_packet = json.loads(encrypted_packet_json)

                    iv_b64 = encrypted_packet["iv"]
                    ciphertext_b64 = encrypted_packet["cipher"]
                    message_hash_received = encrypted_packet["hash"]
                    signature_msg_b64 = encrypted_packet["sig"]

                    decrypted_iv_bytes = base64.b64decode(iv_b64)
                    ciphertext_bytes = base64.b64decode(ciphertext_b64)

                    computed_hash = crypto.create_hash_from_iv_ciphertext(decrypted_iv_bytes, ciphertext_bytes)
                    integrity_check = computed_hash == message_hash_received

                    decrypted_message_bytes = crypto.decrypt_message(ciphertext_b64, self.decrypted_3des_key, decrypted_iv_bytes)
                    decrypted_message_str = decrypted_message_bytes.decode('utf-8')

                    is_valid_msg_signature = crypto.verify_signature(
                        decrypted_message_bytes,
                        signature_msg_b64,
                        self.alice_public_key
                    )

                    self.log_message("Alice", f"{decrypted_message_str}")
                    self.log_message("Verification (Bob)", f"  Integrity: {'OK' if integrity_check else 'FAILED'} (Hash: {computed_hash[:10]}... {'!=' if not integrity_check else '=='} {message_hash_received[:10]}...)")
                    self.log_message("Verification (Bob)", f"  Signature: {'OK' if is_valid_msg_signature else 'FAILED'}")

                    if integrity_check and is_valid_msg_signature:
                        self.client_socket.sendall(b"ACK")
                        self.log_message("System", "Sent ACK")
                    else:
                        self.client_socket.sendall(b"NACK")
                        self.log_message("System", "Sent NACK: Message Integrity Compromised or Signature Invalid!")
                except json.JSONDecodeError:
                    self.log_message("Error", "Received non-JSON data or malformed packet.")
                    self.client_socket.sendall(b"NACK")
                except Exception as ex:
                    self.log_message("Error", f"Processing message failed: {ex}")
                    self.client_socket.sendall(b"NACK")

        except Exception as e:
            if self.running:
                self.log_message("Error", f"Error handling client: {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()
                self.log_message("System", "Alice disconnected. Listening for new connection.")
            if self.running:
                self.root.after(100, self.start_listening)

    def send_message_from_gui(self, event=None):
        message = self.msg_entry.get()
        if not message:
            return
        if not self.client_socket:
            self.log_message("Error", "No client connected to send message.")
            return
        
        if self.decrypted_3des_key and self.alice_public_key: # Ensure secure channel is established for two-way secure comms
            try:
                new_iv_bob = os.urandom(8)
                encrypted_msg_bob = crypto.encrypt_message(message.encode('utf-8'), self.decrypted_3des_key, new_iv_bob)
                
                bob_signature_msg = crypto.sign_data(message.encode('utf-8'), self.bob_private_key)
                
                msg_ciphertext_bytes_bob = base64.b64decode(encrypted_msg_bob)
                msg_hash_bob = crypto.create_hash_from_iv_ciphertext(new_iv_bob, msg_ciphertext_bytes_bob)

                packet_to_send = {
                    "iv": base64.b64encode(new_iv_bob).decode('utf-8'),
                    "cipher": encrypted_msg_bob,
                    "hash": msg_hash_bob,
                    "sig": bob_signature_msg
                }
                self.client_socket.sendall(json.dumps(packet_to_send).encode('utf-8'))
                self.log_message("Bob (Sent)", message)
            except Exception as e:
                self.log_message("Error", f"Could not encrypt/send Bob's message securely: {e}")
        else:
            self.log_message("Error", "Secure channel not established yet. Bob cannot send encrypted message.")

        self.msg_entry.delete(0, END)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.running = False
            if self.client_socket:
                self.client_socket.close()
            if self.server_socket:
                self.server_socket.close()
            self.root.destroy()

if __name__ == "__main__":
    HOST = 'localhost'
    PORT = 12345
    server = ChatServer(HOST, PORT)
    server.root.mainloop()