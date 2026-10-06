# Thanh Nguyen Canh — Academic website

Website tĩnh cho GitHub Pages, gồm About, Research, Publications, Teaching & Mentoring, Funded Projects, Dataset & Code và Open Positions. HTML được tạo sẵn, có thể phục vụ trực tiếp từ thư mục gốc của repository.

Publications có tìm kiếm theo tiêu đề, tác giả, venue và chủ đề; bộ lọc theo năm, loại bài và chủ đề; cùng Abstract/BibTeX. Tìm kiếm toàn website mở bằng biểu tượng trên menu hoặc `Ctrl/⌘ K`. Giao diện hỗ trợ điện thoại, dark mode và nội dung vẫn đọc được khi tắt JavaScript.

## Xem trên máy

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Mở [localhost:8000](http://127.0.0.1:8000/). Không cần cài npm, Jekyll hoặc dependency Python.

## Cập nhật nội dung

- `data/profile.json`: biography, news, teaching, supervision, dự án, scholarships và hoạt động chuyên môn. Các trường `bio_html`, news `html` và `service_html` chứa HTML do chủ website quản lý.
- `data/publications.json`: mỗi bài có `id`, `title`, `authors`, `year`, `type`, `venue`, `status`, `topics`, `abstract`, `image`, `video` và `links`. `type` nhận `journal`, `conference` hoặc `preprint`. Ảnh/video, abstract và link có thể để trống nếu chưa có. Giữ `id` ổn định để các liên kết đến bài tiếp tục hoạt động.
- `stylesheet.css`: giao diện dùng chung; màu và kích thước nằm trong các biến CSS đầu file.
- `assets/site.js`: tìm kiếm, bộ lọc, theme và menu mobile.
- `scripts/build_site.py`: template và cấu trúc trang.

Sau khi sửa dữ liệu hoặc template, chạy:

```bash
python3 scripts/build_site.py
```

Script cập nhật 7 file HTML và `assets/search-index.js`. Commit cả dữ liệu lẫn các file được tạo để GitHub Pages phục vụ nội dung mới. Sửa CSS/JavaScript không cần chạy lại script. Các đường dẫn tương đối hỗ trợ cả website ở domain gốc và GitHub project Pages.

Nội dung được lấy từ website hiện có và CV trong repository. Các bài gửi/submitted và preprints được giữ riêng; không tự chuyển thành bài accepted. Funded Projects phân biệt dự án với học bổng cá nhân. Khi có dataset hoặc vị trí tuyển dụng cụ thể, thêm nội dung thực tế vào phần tương ứng trong script rồi tạo lại trang. Hiện chưa có dataset download hay thông báo tuyển dụng được cung cấp.

## Credits

Website ban đầu dựa trên [Jon Barron](https://jonbarron.info/) và [Thai Duong](https://github.com/thaipduong/thaipduong.github.io). Bố cục mới tham khảo [Teaching của Candy Olivia Mawalim](https://candyolivia.github.io/teaching/), [Publications của Thai Duong](https://thaipduong.github.io/publications/) và [Robot Learning Lab](https://rl.uni-freiburg.de/datasets-code).

Bạn có thể dùng lại code cho website cá nhân; vui lòng giữ credit nguồn gốc.
