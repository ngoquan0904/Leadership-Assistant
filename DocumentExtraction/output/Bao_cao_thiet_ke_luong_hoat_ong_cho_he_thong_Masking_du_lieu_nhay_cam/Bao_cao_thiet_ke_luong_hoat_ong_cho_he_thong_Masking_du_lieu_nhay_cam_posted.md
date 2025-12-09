# Báo cáo thiết kế luồng hoạt động cho hệ thống Masking dữ liệu nhạy cảm - Đảm bảo ATTT khi sử dụng AI của Viettel

## 1. Giới thiệu tổng quan

### 1.1 Bối cảnh và lý do hình thành

Trong bối cảnh chuyển đổi số diễn ra mạnh mẽ, Tập đoàn Viettel đang quản lý và xử lý khối lượng dữ liệu khổng lồ mang tính chiến lược và bảo mật cao, bao gồm dữ liệu nhân sự, thông tin khách hàng, dữ liệu kinh doanh, dữ liệu hạ tầng viễn thông, cùng các hoạt động của các Tổng công ty thuộc tập đoàn Viettel. Việc chia sẻ hoặc khai thác các mô hình AI trên những dữ liệu này tiềm ẩn nguy cơ rò rỉ thông tin nhạy cảm, có thể ảnh hưởng nghiêm trọng đến an ninh, uy tín và lợi ích quốc gia.

Từ thực tiễn đó, việc xây dựng một hệ thống có khả năng tự động **masking** dữ liệu nhạy cảm trước khi đưa vào khai thác bằng các công cụ AI trở nên cấp thiết. Hệ thống này không chỉ giúp đảm bảo an toàn và bảo mật thông tin, mà còn góp phần tuân thủ chặt chẽ các quy định nội bộ của Viettel, VTNet cũng như các quy định của pháp luật hiện hành.

### 1.2 Khái niệm và mục tiêu của hệ thống

Data Masking là kỹ thuật biến đổi các dữ liệu nhạy cảm (ví dụ như thông tin Văn bản, Hợp đồng, dữ liệu kỹ thuật, thông tin nhân sự) thành dạng không thể nhận diện được, nhưng vẫn giữ nguyên cấu trúc, định dạng và tính toàn vẹn của dữ liệu. Nhờ đó, dữ liệu có thể được sử dụng an toàn trong các hoạt động như thử nghiệm, huấn luyện mô hình AI hoặc phân tích thống kê, mà không làm lộ thông tin thật hay vi phạm quy định bảo mật.

#### Mục tiêu của hệ thống

Hệ thống Data Masking được xây dựng nhằm đáp ứng yêu cầu đảm bảo an toàn thông tin (ATTT) trong quá trình ứng dụng các công cụ trí tuệ nhân tạo (AI) để khai thác và phân tích dữ liệu nội bộ của Tập đoàn Viettel. Hệ thống hướng tới các mục tiêu chính sau:

1. Tự động phát hiện và phân loại dữ liệu nhạy cảm trong các tài liệu, báo cáo hoặc tập dữ liệu nội bộ. Hệ thống hỗ trợ xử lý nhiều định dạng tệp khác nhau như .pdf, .docx, .txt, giúp nhận diện và bảo vệ thông tin nhạy cảm trong đa dạng nguồn dữ liệu.
2. Xây dựng cơ chế Masking đa tầng, bao gồm:
3. **Keyword Masking** : thực hiện che giấu các mẫu dữ liệu được định nghĩa sẵn (pattern, phrase) như mã định danh trạm, mã thao tác trạm, tọa độ trạm, hoặc các từ/cụm từ thuộc danh sách nhạy cảm không được phép để lộ ra ngoài.
4. **Semantic Masking** : ứng dụng các kỹ thuật xử lý ngôn ngữ tự nhiên (NLP) và mô hình ngôn ngữ lớn (LLM) để phát hiện và che phủ các thông tin ngữ nghĩa nhạy cảm chưa được định nghĩa có cấu trúc trong từ điển hoặc danh sách quy tắc cố định.
3. Cho phép mở rộng linh hoạt, hỗ trợ bổ sung và cập nhật động các loại dữ liệu nhạy cảm mới tùy theo yêu cầu nghiệp vụ, thay đổi chính sách bảo mật hoặc quy định nội bộ của Viettel.

## 2. Cơ sở lý thuyết và phương pháp ẩn dữ liệu

### 2.1 Khái niệm và phạm vi dữ liệu nhạy cảm

Dữ liệu nhạy cảm là thông tin mà việc **công bố hoặc chia sẻ trái phép có thể gây tổn hại nghiêm trọng** đến Tập đoàn Viettel, khách hàng, đối tác, hoặc vi phạm pháp luật và quy định nội bộ. Trong phạm vi hệ thống, dữ liệu nhạy cảm được phân loại theo mức độ bảo mật của Viettel:

- Dữ liệu **Nội bộ** (Cấp độ 2): Cần được biến đổi để không xác định được là dữ liệu của Viettel trước khi đưa ra khỏi phạm vi quản lý.
- Dữ liệu **Trọng yếu** (Cấp độ 3): Bao gồm dữ liệu cá nhân, khách hàng, tài chính, kinh doanh, mạng lưới. Phải thực hiện Masking hoặc mã hóa.
- Dữ liệu **Mật** (Cấp độ 4): Bao gồm bí mật nhà nước, dữ liệu thuộc Bộ Quốc phòng, bí mật kinh doanh. Tuyệt đối không được công bố.

Hệ thống Data Masking tập trung vào việc che giấu các thông tin thuộc **Cấp độ 2 và Cấp độ 3** trên nhiều định dạng tệp khác nhau. Các nhóm dữ liệu chính bao gồm:

- Dữ liệu **Cá nhân &amp; Khách hàng** : Họ tên, số điện thoại, CMND/CCCD, địa chỉ, vị trí (CellID), lịch sử giao dịch.
- Dữ liệu **Kinh doanh &amp; Tài chính** : Tên/Số/Giá trị hợp đồng, tên đối tác (ví dụ: Huawei, ZTE), báo cáo tài chính/quản trị chưa công bố.
- Dữ liệu **Mạng lưới &amp; Công nghệ** : Mã trạm (HNIxxxx, HCMxxxx), mã thiết bị, sơ đồ mạng lưới, mã nguồn (Source Code).
- Dữ liệu **Nhận dạng &amp; Nội bộ** : Thông tin nhân sự (lương, bậc hay), quy hoạch cán bộ, các từ khóa nhận diện thương hiệu (Viettel, VTNet).

### 2.2 Phương pháp ẩn dữ liệu

Hệ thống Data Masking áp dụng phương pháp **Masking Đa Tầng** (Multi-Layer Masking), kết hợp giữa kỹ thuật dựa trên quy tắc (Rule-Based Masking) và kỹ thuật dựa trên ngữ cảnh/ngữ nghĩa (Semantic-Based Masking) để đạt hiệu quả che giấu toàn diện. Quá trình này được chia thành hai pha chính, xử lý theo từng khối dữ liệu (CHUNK\_SIZE ~1200 ký tự) để tối ưu hóa việc gọi API/LLM:

#### 2.2.1 Keyword Masking

Pha này sử dụng các mẫu biểu thức chính quy (Regex) và từ điển cố định để phát hiện và thay thế các dữ liệu có cấu trúc, bao gồm:

- **Pattern Masking** : Sử dụng danh sách Regex (pattern.txt) để tìm và che giấu các định danh có cấu trúc cụ thể (ví dụ: mã trạm HNIxxxx, số điện thoại, định dạng IP, định dạng tiền tệ,...) bằng placeholder &lt;pattern\_private\_N&gt;.
- **Phrase Masking** : Dựa trên từ điển cụm từ nhạy cảm (Combined\_Unique\_Dictionary.csv) để xử lý các khối văn bản lớn, cụ thể:
    - **Che giấu khối Bảng:** Nếu cụm từ nhạy cảm nằm trong khối &lt;table&gt;...&lt;/table&gt;, che giấu **toàn bộ khối bảng** bằng placeholder &lt;table\_private\_N&gt;.
    - **Che giấu Phần còn lại của Câu:** Nếu cụm từ nhạy cảm nằm trong câu nhưng không phải trong bảng, che giấu **phần câu từ vị trí tiếp theo** của cụm từ đó đến hết câu bằng placeholder &lt;sentence\_private\_N&gt;.

#### 2.2.2 Semantic Masking

Pha này giải quyết thách thức của dữ liệu phi cấu trúc, sử dụng mô hình ngôn ngữ lớn (LLM) để phân tích ngữ cảnh, phát hiện các thực thể nhạy cảm chưa được định nghĩa trong từ điển hoặc có cấu trúc không cố định:

- **Kỹ thuật Phát hiện:** LLM được giao nhiệm vụ (SYSTEM prompt) để phân tích nội dung văn bản sau khi đã thực hiện Keyword Masking, nhằm tìm kiếm các thuật ngữ nhạy cảm theo nhóm:
1. Danh từ riêng (PROPER\_NOUNS).
2. Từ khóa kỹ thuật, tài chính (TECH\_FINANCE\_KEYWORDS).
3. Định danh (IDENTIFIERS).
4. Dữ liệu kỹ thuật (TECHNICAL\_DATA).
- **Kỹ thuật Che giấu:** Các từ khóa nhạy cảm được LLM trả về dưới dạng JSON sẽ được thay thế trong văn bản bằng placeholder &lt;semantic\_private\_N&gt;. Quá trình này được thực hiện lặp lại cho từng loại prompt và hợp nhất kết quả.

## 3. Thiết kế luồng hoạt động chung của hệ thống