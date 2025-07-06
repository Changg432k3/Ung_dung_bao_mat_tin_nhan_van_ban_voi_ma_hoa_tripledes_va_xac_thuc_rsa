# Ung_dung_bao_mat_tin_nhan_van_ban_voi_ma_hoa_tripledes_va_xac_thuc_rsa
ỨNG DỤNG BẢO MẬT TIN NHẮN VĂN BẢN VỚI  MÃ HÓA TRIPLEDES VÀ XÁC THỰC RSA
Kho lưu trữ này chứa một ứng dụng trò chuyện bảo mật minh họa các nguyên tắc mật mã để liên lạc an toàn giữa hai bên, "Alice" (máy khách) và "Bob" (máy chủ). Ứng dụng sử dụng kết hợp RSA để trao đổi khóa và chữ ký số, cùng với TripleDES (3DES) để mã hóa tin nhắn đối xứng.

## Mục lục
- [Giới thiệu](#giới-thiệu)
- [Tính năng](#tính-năng)
- [Tổng quan kỹ thuật](#tổng-quan-kỹ-thuật)
  - [Tạo khóa](#tạo-khóa)
  - [Bắt tay và Trao đổi khóa](#bắt-tay-và-trao-đổi-khóa)
  - [Mã hóa và Toàn vẹn tin nhắn](#mã-hóa-và-toàn-vẹn-tin-nhắn)
  - [Chữ ký số](#chữ-ký-số)
- [Kết quả đạt được](#kết-quả-đạt-được).
- [Yêu cầu](#yêu-cầu)

## Giới thiệu
Trong thời đại mà giao tiếp kỹ thuật số là tối quan trọng, việc đảm bảo tính bảo mật, toàn vẹn và xác thực của tin nhắn là rất cần thiết. Dự án này triển khai một hệ thống trò chuyện bảo mật cơ bản, lấy cảm hứng từ các ví dụ mật mã kinh điển liên quan đến Alice và Bob, để minh họa cách các nguyên tắc mật mã hiện đại có thể được sử dụng để thiết lập một kênh an toàn trên một mạng không an toàn.
Ứng dụng sử dụng kiến trúc client-server. Bob hoạt động như máy chủ, lắng nghe các kết nối đến, trong khi Alice hoạt động như máy khách, khởi tạo kết nối. Một quá trình bắt tay an toàn được thực hiện trước khi bất kỳ tin nhắn nào được trao đổi, đảm bảo rằng cả hai bên đã chia sẻ các khóa đối xứng và xác minh khóa công khai của nhau.

## Tính năng
* **Tạo cặp khóa RSA:** Mỗi bên tự tạo cặp khóa công khai và khóa riêng tư RSA của riêng mình.
* **Trao đổi khóa an toàn:** Khóa TripleDES đối xứng được trao đổi một cách an toàn bằng cách sử dụng mã hóa RSA.
* **Mã hóa TripleDES:** Tin nhắn được mã hóa bằng thuật toán TripleDES ở chế độ CBC.
* **Băm SHA-256 để đảm bảo tính toàn vẹn:** Tính toàn vẹn của tin nhắn được xác minh bằng cách sử dụng băm SHA-256.
* **Chữ ký số RSA:** Tin nhắn được ký số bằng RSA để đảm bảo tính xác thực và không thể chối bỏ.
* **Giao diện người dùng đồ họa (GUI):** Một GUI đơn giản dựa trên Tkinter để trò chuyện tương tác.

## Tổng quan kỹ thuật
Các chức năng mật mã cốt lõi được đóng gói trong `crypto_utils.py`, trong khi `chat_client.py` (Alice) và `chat_server.py` (Bob) triển khai luồng giao tiếp và tích hợp với GUI.

### Tạo khóa
Cả Alice và Bob đều tạo cặp khóa RSA 2048-bit của riêng họ khi khởi động ứng dụng. Các khóa này là nền tảng để thiết lập niềm tin và trao đổi khóa đối xứng một cách an toàn.

### Bắt tay và Trao đổi khóa
Quá trình bắt tay là rất quan trọng để thiết lập một kênh liên lạc an toàn:
* **Alice gửi khóa công khai:** Alice kết nối với Bob và gửi khóa công khai RSA của cô ấy cho Bob.
* **Bob gửi khóa công khai:** Bob nhận khóa công khai của Alice và sau đó gửi khóa công khai RSA của anh ấy cho Alice.
* **Alice tạo và mã hóa khóa 3DES:** Alice tạo một khóa TripleDES 24 byte ngẫu nhiên và một Vector khởi tạo (IV) 8 byte. Cô ấy sau đó mã hóa khóa TripleDES này bằng khóa công khai RSA của Bob.
* **Alice ký thông tin bắt tay:** Alice tạo một phần thông tin đã ký (ví dụ: danh tính và dấu thời gian của cô ấy) và ký nó bằng khóa riêng tư RSA của cô ấy. Điều này là để chứng minh danh tính của cô ấy với Bob.
* **Alice gửi gói trao đổi khóa:** Alice gửi một gói chứa khóa 3DES được mã hóa RSA, thông tin đã ký của cô ấy và chữ ký số cho Bob.
* **Bob giải mã khóa 3DES và xác minh chữ ký:** Bob nhận gói trao đổi khóa, giải mã khóa 3DES bằng khóa riêng tư RSA của anh ấy, và xác minh chữ ký của Alice bằng khóa công khai RSA của Alice.

### Mã hóa và Toàn vẹn tin nhắn
Sau khi thiết lập khóa 3DES đối xứng, mọi tin nhắn được mã hóa bằng TripleDES ở chế độ CBC, với một IV được tạo động cho mỗi tin nhắn (mặc dù code hiện tại tái sử dụng IV ban đầu). Để đảm bảo tính toàn vẹn, một hàm băm SHA-256 được tính toán từ IV và bản mã (IV || ciphertext) và được gửi kèm theo tin nhắn. Bên nhận sẽ giải mã tin nhắn, sau đó tính toán lại băm từ IV và bản mã để so sánh với băm nhận được, từ đó xác minh tin nhắn có bị thay đổi hay không.

### Chữ ký số
Để đảm bảo tính xác thực và không thể chối bỏ, mỗi tin nhắn trước khi mã hóa sẽ được ký số bằng khóa riêng tư RSA của người gửi, sử dụng đệm PSS và băm SHA-256. Chữ ký số này được gửi kèm trong gói tin nhắn đã mã hóa. Khi nhận được, bên nhận sẽ giải mã tin nhắn và xác minh chữ ký bằng cách sử dụng khóa công khai RSA của người gửi và tin nhắn văn bản thuần túy đã giải mã. Việc xác minh chữ ký thành công chứng minh rằng tin nhắn đến từ người gửi đã tuyên bố và không bị giả mạo.

## Kết quả đạt được
![image](https://github.com/user-attachments/assets/19da9ca6-3b98-4a11-b5d6-b1dda93348dd)
![image](https://github.com/user-attachments/assets/ee40d2a2-77b0-460c-98cd-4f868a974472)


## Yêu cầu
- Python 3.x
- Thư viện cryptography
- tkinter (thư viện GUI tiêu chuẩn của Python)
