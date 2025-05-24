# Ung_dung_bao_mat_tin_nhan_van_ban_voi_ma_hoa_tripledes_va_xac_thuc_rsa
ỨNG DỤNG BẢO MẬT TIN NHẮN VĂN BẢN VỚI  MÃ HÓA TRIPLEDES VÀ XÁC THỰC RSA
- Đây là một ứng dụng chat đơn giản được xây dựng bằng Python và thư viện tkinter cho giao diện người dùng, sử dụng các thuật toán mã hóa và xác thực để đảm bảo an toàn cho tin nhắn. Ứng dụng này minh họa việc sử dụng kết hợp các cơ chế bảo mật để đạt được tính bảo mật cao trong giao tiếp.
# Các tính năng chính
- Mã hóa TripleDES (3DES): Tin nhắn được mã hóa bằng thuật toán 3DES với chế độ CBC (Cipher Block Chaining) để đảm bảo tính bảo mật và bí mật của dữ liệu truyền tải.
- Mã hóa khóa RSA: Khóa 3DES được trao đổi một cách an toàn giữa client và server thông qua mã hóa RSA. Điều này đảm bảo rằng khóa phiên (session key) chỉ được biết bởi hai bên tham gia giao tiếp.
- Chữ ký số RSA: Mỗi tin nhắn được ký bằng thuật toán RSA để xác thực nguồn gốc và đảm bảo tính toàn vẹn của tin nhắn. Điều này giúp người nhận xác minh rằng tin nhắn thực sự đến từ người gửi mong muốn và không bị thay đổi trong quá trình truyền tải.
- Kiểm tra toàn vẹn bằng SHA-256: Một hàm băm SHA-256 được tạo từ IV (Initialization Vector) và ciphertext của tin nhắn để kiểm tra tính toàn vẹn. Người nhận có thể so sánh giá trị băm được tính toán với giá trị băm nhận được để phát hiện bất kỳ sự giả mạo nào.
- Giao diện người dùng Tkinter: Ứng dụng cung cấp giao diện người dùng đồ họa (GUI) thân thiện được xây dựng với tkinter, giúp người dùng dễ dàng tương tác.
- Trao đổi khóa an toàn: Quá trình bắt tay (handshake) ban đầu bao gồm việc trao đổi khóa công khai RSA và khóa 3DES được mã hóa để thiết lập một kênh liên lạc an toàn.
- Thông báo trạng thái: Cung cấp thông báo về trạng thái kết nối và quá trình bắt tay để người dùng dễ dàng theo dõi.
# Yêu cầu
- Python 3.x
- Thư viện cryptography
