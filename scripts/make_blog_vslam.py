#!/usr/bin/env python3
"""Data for the blog post "Feature-based and direct visual SLAM" (blog/visual-slam-feature-vs-direct/data.js).

A hand-picked list of influential visual SLAM and odometry systems, grouped by how their front-end measures the image.
Titles, venues, years and DOIs were checked against dblp (2015 on) and Crossref (earlier and T-PAMI papers).
Also a table of the most cited recent visual SLAM and odometry systems in T-RO, RA-L and IJRR (2019 on): candidates from
the Paper Explorer data (explorer/data, dblp), citation counts from OpenAlex (fetched when this script runs).

Run: python3 scripts/make_blog_vslam.py   (then python3 scripts/build_site.py)
"""
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "blog" / "visual-slam-feature-vs-direct" / "data.js"

# (id, en, vi, den, dvi, [(branch id, en, vi)])
TREE = [
    ("feature", "Feature-based (indirect)", "Dựa trên đặc trưng (gián tiếp)",
     "Detect keypoints, match them by descriptors, and minimize the reprojection error in pixels.",
     "Phát hiện điểm đặc trưng, so khớp bằng bộ mô tả và tối thiểu sai số chiếu lại tính bằng điểm ảnh.",
     [("f-filter", "Filtering", "Lọc (EKF)"), ("f-ba", "Keyframes & bundle adjustment", "Khung hình khóa và tối ưu bó"),
      ("f-lines", "Points & lines", "Điểm và đường thẳng"), ("f-vi", "Visual-inertial optimization", "Tối ưu thị giác-quán tính"),
      ("f-learned", "Learned keypoints & descriptors", "Điểm đặc trưng và bộ mô tả học được")]),
    ("direct", "Direct", "Trực tiếp",
     "Compare pixel intensities between images and minimize the photometric error, without keypoints or descriptors.",
     "So sánh cường độ điểm ảnh giữa các ảnh và tối thiểu sai số trắc quang, không cần điểm đặc trưng hay bộ mô tả.",
     [("d-dense", "Dense", "Dày đặc"), ("d-semi", "Semi-dense", "Bán dày đặc"), ("d-sparse", "Sparse", "Thưa"),
      ("d-vi", "Visual-inertial & LiDAR-visual", "Thị giác-quán tính và LiDAR-thị giác"), ("d-event", "Event cameras", "Camera sự kiện")]),
    ("semi", "Semi-direct & hybrid", "Bán trực tiếp và lai",
     "Direct alignment of small patches for speed, then feature-style reprojection error for accuracy.",
     "Căn chỉnh trực tiếp các mảnh ảnh nhỏ để nhanh, rồi dùng sai số chiếu lại kiểu đặc trưng để chính xác.",
     [("s-svo", "Semi-direct odometry", "Đo hành trình bán trực tiếp")]),
    ("learned", "Learning-based", "Dựa trên học sâu",
     "Networks predict motion, depth or correspondences; most recent systems still finish with geometric optimization.",
     "Mạng nơ-ron dự đoán chuyển động, độ sâu hoặc tương ứng điểm; phần lớn hệ thống gần đây vẫn kết thúc bằng tối ưu hình học.",
     [("l-e2e", "End-to-end pose", "Ước lượng tư thế đầu-cuối"), ("l-prior", "Learned priors in classic pipelines", "Tiền nghiệm học được trong hệ cổ điển"),
      ("l-flow", "Learned correspondence + bundle adjustment", "Tương ứng học được và tối ưu bó"), ("l-3d", "3D foundation models", "Mô hình nền tảng 3D")]),
]

# (name, year, branch, authors, venue, full title, url, description en, description vi)
SYSTEMS = [
    ("MonoSLAM", 2007, "f-filter", "Davison, Reid, Molton, Stasse", "T-PAMI", "MonoSLAM: Real-Time Single Camera SLAM",
     "https://doi.org/10.1109/TPAMI.2007.1049",
     "Real-time monocular SLAM with an extended Kalman filter over a sparse map of image features.",
     "SLAM một camera thời gian thực dùng bộ lọc Kalman mở rộng trên bản đồ thưa gồm các đặc trưng ảnh."),
    ("MSCKF", 2007, "f-filter", "Mourikis, Roumeliotis", "ICRA", "A Multi-State Constraint Kalman Filter for Vision-aided Inertial Navigation",
     "https://doi.org/10.1109/ROBOT.2007.364024",
     "A visual-inertial filter that uses feature tracks as constraints between camera poses, without keeping the 3D points in the state.",
     "Bộ lọc thị giác-quán tính dùng các vết đặc trưng làm ràng buộc giữa các tư thế camera, không giữ điểm 3D trong trạng thái."),
    ("PTAM", 2007, "f-ba", "Klein, Murray", "ISMAR", "Parallel Tracking and Mapping for Small AR Workspaces",
     "https://doi.org/10.1109/ISMAR.2007.4538852",
     "Split tracking and mapping into two parallel threads, with bundle adjustment over keyframes: the template for later keyframe SLAM.",
     "Tách theo dõi và lập bản đồ thành hai luồng song song, tối ưu bó trên khung hình khóa: khuôn mẫu cho các hệ SLAM khung hình khóa về sau."),
    ("ORB-SLAM", 2015, "f-ba", "Mur-Artal, Montiel, Tardós", "T-RO", "ORB-SLAM: A Versatile and Accurate Monocular SLAM System",
     "https://doi.org/10.1109/TRO.2015.2463671",
     "ORB features for tracking, mapping, relocalization and loop closing, with a covisibility graph and bag-of-words place recognition.",
     "Dùng đặc trưng ORB cho theo dõi, lập bản đồ, tái định vị và đóng vòng, với đồ thị đồng quan sát và nhận dạng địa điểm bằng túi từ."),
    ("ORB-SLAM2", 2017, "f-ba", "Mur-Artal, Tardós", "T-RO", "ORB-SLAM2: An Open-Source SLAM System for Monocular, Stereo, and RGB-D Cameras",
     "https://doi.org/10.1109/TRO.2017.2705103",
     "Extended ORB-SLAM to stereo and RGB-D cameras.", "Mở rộng ORB-SLAM cho camera stereo và RGB-D."),
    ("ORB-SLAM3", 2021, "f-ba", "Campos, Elvira, Gómez Rodríguez, Montiel, Tardós", "T-RO",
     "ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial, and Multimap SLAM", "https://doi.org/10.1109/TRO.2021.3075644",
     "Adds visual-inertial SLAM based on maximum-a-posteriori estimation, and several maps that can be merged (Atlas).",
     "Bổ sung SLAM thị giác-quán tính dựa trên ước lượng hậu nghiệm cực đại (MAP), cùng nhiều bản đồ có thể hợp nhất (Atlas)."),
    ("PL-SLAM (mono)", 2017, "f-lines", "Pumarola, Vakhitov, Agudo, Sanfeliu, Moreno-Noguer", "ICRA", "PL-SLAM: Real-time monocular visual SLAM with points and lines",
     "https://doi.org/10.1109/ICRA.2017.7989522",
     "Adds line segments to ORB-SLAM-style point features, which helps in scenes with few corners.",
     "Bổ sung các đoạn thẳng vào đặc trưng điểm kiểu ORB-SLAM, giúp ích ở những cảnh có ít góc."),
    ("OKVIS", 2015, "f-vi", "Leutenegger, Lynen, Bosse, Siegwart, Furgale", "IJRR", "Keyframe-based visual-inertial odometry using nonlinear optimization",
     "https://doi.org/10.1177/0278364914554813",
     "Keyframe visual-inertial odometry that jointly optimizes reprojection and IMU errors in a sliding window.",
     "Đo hành trình thị giác-quán tính dựa trên khung hình khóa, tối ưu đồng thời sai số chiếu lại và sai số IMU trong cửa sổ trượt."),
    ("VINS-Mono", 2018, "f-vi", "Qin, Li, Shen", "T-RO", "VINS-Mono: A Robust and Versatile Monocular Visual-Inertial State Estimator",
     "https://doi.org/10.1109/TRO.2018.2853729",
     "Monocular visual-inertial estimation with tightly coupled sliding-window optimization, IMU pre-integration, loop closure and relocalization.",
     "Ước lượng thị giác-quán tính một camera với tối ưu cửa sổ trượt kết hợp chặt, tiền tích phân IMU, đóng vòng và tái định vị."),
    ("DTAM", 2011, "d-dense", "Newcombe, Lovegrove, Davison", "ICCV", "DTAM: Dense Tracking and Mapping in Real-Time",
     "https://doi.org/10.1109/ICCV.2011.6126513",
     "Dense per-pixel depth maps and whole-image alignment for tracking, on a GPU.",
     "Bản đồ độ sâu dày đặc theo từng điểm ảnh và căn chỉnh toàn ảnh để theo dõi, chạy trên GPU."),
    ("DVO-SLAM", 2013, "d-dense", "Kerl, Sturm, Cremers", "IROS", "Dense Visual SLAM for RGB-D Cameras",
     "https://doi.org/10.1109/IROS.2013.6696650",
     "RGB-D SLAM that minimizes photometric and depth errors over all pixels, with keyframes and pose-graph optimization.",
     "SLAM RGB-D tối thiểu sai số trắc quang và sai số độ sâu trên mọi điểm ảnh, với khung hình khóa và tối ưu đồ thị tư thế."),
    ("LSD-SLAM", 2014, "d-semi", "Engel, Schöps, Cremers", "ECCV", "LSD-SLAM: Large-Scale Direct Monocular SLAM",
     "https://doi.org/10.1007/978-3-319-10605-2_54",
     "Semi-dense depth on high-gradient pixels and direct image alignment on Sim(3), for large-scale monocular SLAM.",
     "Độ sâu bán dày đặc trên các điểm ảnh có gradient cao và căn chỉnh ảnh trực tiếp trên Sim(3), cho SLAM một camera quy mô lớn."),
    ("DSO", 2018, "d-sparse", "Engel, Koltun, Cremers", "T-PAMI", "Direct Sparse Odometry", "https://doi.org/10.1109/TPAMI.2017.2658577",
     "Jointly optimizes poses, sparse point depths and affine brightness in a sliding window, with full photometric calibration.",
     "Tối ưu đồng thời tư thế, độ sâu của các điểm thưa và tham số độ sáng affine trong cửa sổ trượt, với hiệu chuẩn trắc quang đầy đủ."),
    ("Stereo DSO", 2017, "d-sparse", "Wang, Schwörer, Cremers", "ICCV", "Stereo DSO: Large-Scale Direct Sparse Visual Odometry with Stereo Cameras",
     "https://doi.org/10.1109/ICCV.2017.421",
     "Stereo version of DSO: static stereo gives metric scale and a better initialization.",
     "Phiên bản stereo của DSO: stereo tĩnh cho tỷ lệ thực (mét) và khởi tạo tốt hơn."),
    ("LDSO", 2018, "d-sparse", "Gao, Wang, Demmel, Cremers", "IROS", "LDSO: Direct Sparse Odometry with Loop Closure",
     "https://doi.org/10.1109/IROS.2018.8593376",
     "Adds loop closure to DSO: descriptors on selected points give bag-of-words place recognition, followed by pose-graph optimization.",
     "Bổ sung đóng vòng cho DSO: bộ mô tả trên các điểm được chọn cho phép nhận dạng địa điểm bằng túi từ, sau đó tối ưu đồ thị tư thế."),
    ("DSM", 2020, "d-sparse", "Zubizarreta, Aguinaga, Montiel", "T-RO", "Direct Sparse Mapping", "https://doi.org/10.1109/TRO.2020.2991614",
     "Direct monocular SLAM that keeps a persistent map and re-observes old points with photometric bundle adjustment.",
     "SLAM trực tiếp một camera giữ bản đồ lâu dài và quan sát lại các điểm cũ bằng tối ưu bó trắc quang."),
    ("Con-DSO", 2026, "d-sparse", "Zhang, Nguyen Canh, Li, Gao, Jiang, Chong", "Preprint",
     "Con-DSO: Learning Short-Horizon Consistency Priors for RGB-D Direct Sparse Odometry", "https://thanhnguyencanh.github.io/Con-DSO/",
     "Learns short-horizon consistency priors for RGB-D direct sparse odometry (PAIRS Lab, under review).",
     "Học các tiền nghiệm nhất quán ngắn hạn cho đo hành trình trực tiếp thưa RGB-D (PAIRS Lab, đang được phản biện)."),
    ("ROVIO", 2015, "d-vi", "Blösch, Omari, Hutter, Siegwart", "IROS", "Robust visual inertial odometry using a direct EKF-based approach",
     "https://doi.org/10.1109/IROS.2015.7353389",
     "EKF visual-inertial odometry that uses the photometric error of image patches directly as the filter innovation.",
     "Đo hành trình thị giác-quán tính dùng EKF, lấy trực tiếp sai số trắc quang của các mảnh ảnh làm phần đổi mới của bộ lọc."),
    ("VI-DSO", 2018, "d-vi", "von Stumberg, Usenko, Cremers", "ICRA", "Direct Sparse Visual-Inertial Odometry Using Dynamic Marginalization",
     "https://doi.org/10.1109/ICRA.2018.8462905",
     "Visual-inertial DSO with dynamic marginalization, so the scale can be initialized and refined online.",
     "DSO thị giác-quán tính với biên hóa động, giúp khởi tạo và tinh chỉnh tỷ lệ ngay trong lúc chạy."),
    ("SVO", 2014, "s-svo", "Forster, Pizzoli, Scaramuzza", "ICRA", "SVO: Fast Semi-Direct Monocular Visual Odometry",
     "https://doi.org/10.1109/ICRA.2014.6906584",
     "Tracks sparse patches by direct image alignment, then refines their positions and optimizes poses and points with reprojection error; very fast.",
     "Theo dõi các mảnh ảnh thưa bằng căn chỉnh trực tiếp, rồi tinh chỉnh vị trí của chúng và tối ưu tư thế, điểm theo sai số chiếu lại; rất nhanh."),
    ("SVO 2", 2017, "s-svo", "Forster, Zhang, Gassner, Werlberger, Scaramuzza", "T-RO", "SVO: Semidirect Visual Odometry for Monocular and Multicamera Systems",
     "https://doi.org/10.1109/TRO.2016.2623335",
     "Extends SVO to multi-camera rigs, edgelets and wide-angle (fisheye and catadioptric) cameras.",
     "Mở rộng SVO cho hệ nhiều camera, edgelet và camera góc rộng (mắt cá và gương cầu)."),
    ("DeepVO", 2017, "l-e2e", "Wang, Clark, Wen, Trigoni", "ICRA", "DeepVO: Towards End-to-End Visual Odometry with Deep Recurrent Convolutional Neural Networks",
     "https://doi.org/10.1109/ICRA.2017.7989236",
     "A recurrent convolutional network that regresses camera motion directly from image sequences.",
     "Mạng tích chập hồi quy (recurrent) ước lượng chuyển động camera trực tiếp từ chuỗi ảnh."),
    ("CodeSLAM", 2018, "l-prior", "Bloesch, Czarnowski, Clark, Leutenegger, Davison", "CVPR",
     "CodeSLAM: Learning a Compact, Optimisable Representation for Dense Visual SLAM", "https://doi.org/10.1109/CVPR.2018.00271",
     "Represents dense depth with a compact learned code that is optimized together with the poses.",
     "Biểu diễn độ sâu dày đặc bằng một mã nén học được, tối ưu cùng với tư thế."),
    ("D3VO", 2020, "l-prior", "Yang, von Stumberg, Wang, Cremers", "CVPR", "D3VO: Deep Depth, Deep Pose and Deep Uncertainty for Monocular Visual Odometry",
     "https://doi.org/10.1109/CVPR42600.2020.00136",
     "Feeds learned depth, pose and photometric uncertainty into a DSO-style direct pipeline.",
     "Đưa độ sâu, tư thế và độ bất định trắc quang học được vào một hệ trực tiếp kiểu DSO."),
    ("DROID-SLAM", 2021, "l-flow", "Teed, Deng", "NeurIPS", "DROID-SLAM: Deep Visual SLAM for Monocular, Stereo, and RGB-D Cameras",
     "https://proceedings.neurips.cc/paper/2021/hash/89fcd07f20b6785b92134bd6c1d0fa42-Abstract.html",
     "Recurrent updates of dense optical flow, coupled with a differentiable dense bundle adjustment layer.",
     "Cập nhật lặp dòng quang học dày đặc, kết hợp với một lớp tối ưu bó dày đặc khả vi."),
    ("DPVO", 2023, "l-flow", "Teed, Lipson, Deng", "NeurIPS", "Deep Patch Visual Odometry",
     "https://papers.nips.cc/paper_files/paper/2023/hash/7ac484b0f1a1719ad5be9aa8c8455fbb-Abstract-Conference.html",
     "A sparse, patch-based version of the DROID idea that is faster and needs less memory.",
     "Phiên bản thưa dựa trên mảnh ảnh của ý tưởng DROID, nhanh hơn và cần ít bộ nhớ hơn."),
    # recent systems, picked from the most cited visual SLAM papers of 2019-2026 in the Paper Explorer venues
    ("OpenVINS", 2020, "f-filter", "Geneva, Eckenhoff, Lee, Yang, Huang", "ICRA", "OpenVINS: A Research Platform for Visual-Inertial Estimation",
     "https://doi.org/10.1109/ICRA40945.2020.9196524",
     "Open MSCKF-based visual-inertial estimation platform with sliding-window filtering, online calibration and evaluation tools.",
     "Nền tảng ước lượng thị giác-quán tính mã nguồn mở dựa trên MSCKF, với bộ lọc cửa sổ trượt, hiệu chuẩn trực tuyến và công cụ đánh giá."),
    ("OV²SLAM", 2021, "f-ba", "Ferrera, Eudes, Moras, Sanfourche, Le Besnerais", "RA-L",
     "OV²SLAM: A Fully Online and Versatile Visual SLAM for Real-Time Applications", "https://doi.org/10.1109/LRA.2021.3058069",
     "Fully online keyframe SLAM for monocular and stereo cameras, tracking with optical flow and closing loops with an online bag of words.",
     "SLAM khung hình khóa hoàn toàn trực tuyến cho camera một mắt và stereo, theo dõi bằng dòng quang học và đóng vòng bằng túi từ trực tuyến."),
    ("PL-SLAM (stereo)", 2019, "f-lines", "Gomez-Ojeda, Moreno, Zuñiga-Noël, Scaramuzza, Gonzalez-Jimenez", "T-RO",
     "PL-SLAM: A Stereo SLAM System Through the Combination of Points and Line Segments", "https://doi.org/10.1109/TRO.2019.2899783",
     "Stereo SLAM that combines points and line segments in tracking, mapping and loop closure.",
     "SLAM stereo kết hợp điểm và đoạn thẳng trong theo dõi, lập bản đồ và đóng vòng."),
    ("Basalt", 2020, "f-vi", "Usenko, Demmel, Schubert, Stückler, Cremers", "RA-L", "Visual-Inertial Mapping With Non-Linear Factor Recovery",
     "https://doi.org/10.1109/LRA.2019.2961227",
     "Visual-inertial odometry with patch tracking by optical flow, plus global mapping that recovers non-linear factors from the odometry.",
     "Đo hành trình thị giác-quán tính theo dõi mảnh ảnh bằng dòng quang học, cùng lập bản đồ toàn cục khôi phục các nhân tử phi tuyến từ phần đo hành trình."),
    ("DXSLAM", 2020, "f-learned", "Li, Shi, Long, Liu, Yang, Wang, Wei, Qiao", "IROS", "DXSLAM: A Robust and Efficient Visual SLAM System with Deep Features",
     "https://doi.org/10.1109/IROS45743.2020.9340907",
     "Replaces hand-crafted ORB features with deep CNN keypoints and descriptors, also for place recognition.",
     "Thay đặc trưng ORB thủ công bằng điểm đặc trưng và bộ mô tả từ mạng CNN, dùng cả cho nhận dạng địa điểm."),
    ("AirSLAM", 2025, "f-learned", "Xu, Hao, Yuan, Wang, Xie", "T-RO", "AirSLAM: An Efficient and Illumination-Robust Point-Line Visual SLAM System",
     "https://doi.org/10.1109/TRO.2025.3539171",
     "Point-line visual SLAM with a learned joint detector for points and lines, built to stay robust when illumination changes.",
     "SLAM thị giác điểm-đường với bộ phát hiện học được cho cả điểm và đường thẳng, giữ vững khi ánh sáng thay đổi."),
    ("BAD SLAM", 2019, "d-dense", "Schöps, Sattler, Pollefeys", "CVPR", "BAD SLAM: Bundle Adjusted Direct RGB-D SLAM",
     "https://doi.org/10.1109/CVPR.2019.00022",
     "RGB-D SLAM with direct bundle adjustment over surfels, jointly optimizing photometric and geometric residuals.",
     "SLAM RGB-D với tối ưu bó trực tiếp trên các surfel, tối ưu đồng thời phần dư trắc quang và hình học."),
    ("DM-VIO", 2022, "d-vi", "von Stumberg, Cremers", "RA-L", "DM-VIO: Delayed Marginalization Visual-Inertial Odometry",
     "https://doi.org/10.1109/LRA.2021.3140129",
     "Direct visual-inertial odometry built on DSO, with delayed marginalization and a pose-graph bundle adjustment for IMU initialization.",
     "Đo hành trình thị giác-quán tính trực tiếp xây dựng trên DSO, với biên hóa trễ và tối ưu bó đồ thị tư thế để khởi tạo IMU."),
    ("FAST-LIVO2", 2025, "d-vi", "Zheng, Xu, Zou, Hua, Yuan, He, Zhou, Liu, Lin, Zhu, Ren, Wang, Wang, Lin, Zhang", "T-RO",
     "FAST-LIVO2: Fast, Direct LiDAR-Inertial-Visual Odometry", "https://doi.org/10.1109/TRO.2024.3502198",
     "Fuses LiDAR, IMU and camera; its visual part aligns image patches on LiDAR map points by their photometric error.",
     "Kết hợp LiDAR, IMU và camera; phần thị giác căn chỉnh các mảnh ảnh trên điểm bản đồ LiDAR theo sai số trắc quang."),
    ("ESVO", 2021, "d-event", "Zhou, Gallego, Shen", "T-RO", "Event-Based Stereo Visual Odometry", "https://doi.org/10.1109/TRO.2021.3062252",
     "Stereo event-camera odometry: semi-dense depth from time surfaces for mapping, and tracking by aligning new events to them.",
     "Đo hành trình bằng cặp camera sự kiện: độ sâu bán dày đặc từ các mặt thời gian để lập bản đồ, và theo dõi bằng cách căn chỉnh sự kiện mới vào đó."),
    ("EDS", 2022, "d-event", "Hidalgo-Carrió, Gallego, Scaramuzza", "CVPR", "Event-aided Direct Sparse Odometry",
     "https://doi.org/10.1109/CVPR52688.2022.00569",
     "Direct sparse odometry that tracks with events and maps with frames, using a model of how events are generated.",
     "Đo hành trình trực tiếp thưa theo dõi bằng sự kiện và lập bản đồ bằng khung hình, dùng mô hình về cách sự kiện được sinh ra."),
    ("ESVO2", 2025, "d-event", "Niu, Zhong, Lu, Shen, Gallego, Zhou", "T-RO", "ESVO2: Direct Visual-Inertial Odometry With Stereo Event Cameras",
     "https://doi.org/10.1109/TRO.2025.3548523",
     "Adds an IMU and faster mapping to ESVO: direct visual-inertial odometry with stereo event cameras.",
     "Bổ sung IMU và lập bản đồ nhanh hơn cho ESVO: đo hành trình thị giác-quán tính trực tiếp với cặp camera sự kiện."),
    ("DF-VO", 2020, "l-prior", "Zhan, Weerasekera, Bian, Reid", "ICRA", "Visual Odometry Revisited: What Should Be Learnt?",
     "https://doi.org/10.1109/ICRA40945.2020.9197374",
     "Learns depth and optical flow, but computes the camera motion with classical geometry (essential matrix and PnP).",
     "Học độ sâu và dòng quang học, nhưng tính chuyển động camera bằng hình học cổ điển (ma trận thiết yếu và PnP)."),
    ("DeepFactors", 2020, "l-prior", "Czarnowski, Laidlow, Clark, Davison", "RA-L", "DeepFactors: Real-Time Probabilistic Dense Monocular SLAM",
     "https://doi.org/10.1109/LRA.2020.2965415",
     "Dense monocular SLAM that optimizes learned compact depth codes in a factor graph with photometric, reprojection and geometric factors.",
     "SLAM dày đặc một camera tối ưu các mã độ sâu nén học được trong đồ thị nhân tử với các nhân tử trắc quang, chiếu lại và hình học."),
    ("DPV-SLAM", 2024, "l-flow", "Lipson, Teed, Deng", "ECCV", "Deep Patch Visual SLAM", "https://doi.org/10.1007/978-3-031-72627-9_24",
     "Adds loop closure and global optimization to DPVO while keeping it efficient.",
     "Bổ sung đóng vòng và tối ưu toàn cục cho DPVO mà vẫn giữ được hiệu quả."),
    ("MAC-VO", 2025, "l-flow", "Qiu, Chen, Zhang, Wang, Scherer", "ICRA", "MAC-VO: Metrics-Aware Covariance for Learning-Based Stereo Visual Odometry",
     "https://doi.org/10.1109/ICRA55743.2025.11128482",
     "Learned stereo odometry that predicts the uncertainty of each match and uses it to select keypoints and weight the optimization.",
     "Đo hành trình stereo dựa trên học sâu, dự đoán độ bất định của từng phép so khớp để chọn điểm và đặt trọng số cho tối ưu."),
    ("SLAM3R", 2025, "l-3d", "Liu, Dong, Wang, Yin, Yang, Fan, Chen", "CVPR", "SLAM3R: Real-Time Dense Scene Reconstruction from Monocular RGB Videos",
     "https://doi.org/10.1109/CVPR52734.2025.01552",
     "Regresses dense 3D points from short video clips with feed-forward networks and merges them into one scene, in real time.",
     "Hồi quy trực tiếp điểm 3D dày đặc từ các đoạn video ngắn bằng mạng truyền thẳng rồi ghép thành một cảnh, theo thời gian thực."),
    ("VGGT-SLAM", 2025, "l-3d", "Maggio, Lim, Carlone", "NeurIPS", "VGGT-SLAM: Dense RGB SLAM Optimized on the SL(4) Manifold",
     "https://papers.nips.cc/paper_files/paper/2025/hash/bc65ab11abfbad890171109686233f4e-Abstract-Conference.html",
     "Dense RGB SLAM that aligns VGGT reconstructions of sub-maps with optimization on the SL(4) manifold.",
     "SLAM RGB dày đặc ghép các tái tạo VGGT của từng bản đồ con bằng tối ưu trên đa tạp SL(4)."),
    ("MASt3R-SLAM", 2025, "l-3d", "Murai, Dexheimer, Davison", "CVPR", "MASt3R-SLAM: Real-Time Dense SLAM with 3D Reconstruction Priors",
     "https://doi.org/10.1109/CVPR52734.2025.01556",
     "Dense real-time SLAM built on the two-view 3D reconstruction priors of MASt3R.",
     "SLAM dày đặc thời gian thực xây dựng trên tiền nghiệm tái tạo 3D hai góc nhìn của MASt3R."),
]


# most cited recent systems in the robotics journals: candidates from the explorer data, citations from OpenAlex
JOURNALS = {"tro": "T-RO", "ral": "RA-L", "ijrr": "IJRR"}
CAMERA = re.compile(r"(?i)\b(visual|vision|monocular|stereo|rgb-?d|camera|image|event|photometric)")
METHOD = re.compile(r"(?i)\b(direct|feature|point[- ]line|patch)")  # count only without LiDAR: "direct LiDAR odometry" uses raw points
SLAM = re.compile(r"(?i)\b(slam|odometry|vio|visual[- ]inertial|localization and mapping|bundle adjustment)")
SKIP = re.compile(r"(?i)\b(review|survey|comparison|benchmark|dataset|gnss|uwb|swarm|sonar|acoustic|underwater|radar|wheel|semantic|object|dynamic|"
                  r"collaborative|multi-robot|place recognition|neural radiance|nerf|gaussian splatting|depth completion)")
# family of each system that reached the table (others show "-")
FAMILY = {"10.1109/tro.2021.3075644": ("ORB-SLAM3", "Feature-based", "Dựa trên đặc trưng"),
          "10.1109/tro.2024.3502198": ("FAST-LIVO2", "Direct, LiDAR + camera", "Trực tiếp, LiDAR + camera"),
          "10.1109/tro.2019.2899783": ("PL-SLAM (stereo)", "Feature-based, points & lines", "Đặc trưng, điểm và đường"),
          "10.1109/tro.2025.3539171": ("AirSLAM", "Feature-based, learned points & lines", "Đặc trưng, điểm và đường học được"),
          "10.1109/tro.2021.3062252": ("ESVO", "Event camera", "Camera sự kiện"),
          "10.1109/lra.2021.3140129": ("DM-VIO", "Direct, visual-inertial", "Trực tiếp, thị giác-quán tính"),
          "10.1109/lra.2019.2961227": ("Basalt", "Feature-based, visual-inertial", "Đặc trưng, thị giác-quán tính"),
          "10.1109/lra.2020.2965415": ("DeepFactors", "Learning-based", "Dựa trên học sâu"),
          "10.1109/tro.2025.3548523": ("ESVO2", "Event camera, direct visual-inertial", "Camera sự kiện, trực tiếp thị giác-quán tính"),
          "10.1109/lra.2025.3575644": (None, "Feature-based, learned keypoints", "Đặc trưng, điểm học được"),
          "10.1109/lra.2024.3421792": ("Switch-SLAM", "LiDAR + camera", "LiDAR + camera"),
          "10.1109/lra.2023.3269950": ("ESVIO", "Event camera, visual-inertial", "Camera sự kiện, thị giác-quán tính"),
          "10.1109/tro.2024.3378443": ("CMax-SLAM", "Event camera", "Camera sự kiện"),
          "10.1109/lra.2020.3015456": ("Structure-SLAM", "Feature-based, structural lines", "Đặc trưng, đường cấu trúc"),
          "10.1109/lra.2022.3231983": ("EPLF-VINS", "Feature-based, points & lines", "Đặc trưng, điểm và đường"),
          "10.1109/tro.2022.3193788": ("VILENS", "Multi-sensor: camera, IMU, LiDAR, legs", "Đa cảm biến: camera, IMU, LiDAR, chân"),
          "10.1109/lra.2021.3056380": ("Multi-modal landmark tracking (Wisth et al.)", "Multi-sensor: camera, IMU, LiDAR", "Đa cảm biến: camera, IMU, LiDAR")}


def citation_table(top=12):
    data = ROOT / "explorer" / "data"
    cands = []
    for vid, name in JOURNALS.items():
        d = json.loads((data / f"{vid}.json").read_text(encoding="utf-8"))
        for t, y, l in zip(d["t"], d["y"], d["l"]):
            visual = CAMERA.search(t) or (METHOD.search(t) and not re.search(r"(?i)lidar", t))
            if y >= 2019 and l.startswith("10.") and SLAM.search(t) and visual and not SKIP.search(t):
                cands.append({"title": t, "venue": name, "year": y, "doi": l.lower()})
    cites = {}
    for i in range(0, len(cands), 50):
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
            {"filter": "doi:" + "|".join(c["doi"] for c in cands[i:i + 50]), "per-page": 50, "select": "doi,cited_by_count"})
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (blog data script)"})
        for w in json.load(urllib.request.urlopen(req, timeout=60))["results"]:
            cites[(w.get("doi") or "").lower().replace("https://doi.org/", "")] = w["cited_by_count"]
        time.sleep(0.5)
    today = date.today()
    now = today.year + (today.timetuple().tm_yday - 1) / 365
    rows = []
    for c in cands:
        if c["doi"] in cites:
            fam = FAMILY.get(c["doi"], (None, "-", "-"))
            rows.append({"name": fam[0] or c["title"], "title": c["title"], "venue": c["venue"], "year": c["year"], "cites": cites[c["doi"]],
                         "rate": round(cites[c["doi"]] / max(0.75, now - c["year"]), 1), "en": fam[1], "vi": fam[2], "url": "https://doi.org/" + c["doi"]})
    rows.sort(key=lambda r: -r["rate"])
    print(len(cands), "journal candidates;", len(rows), "with citations")
    return {"date": today.isoformat(), "candidates": len(cands), "rows": rows[:top]}


def main():
    nodes = []
    for tid, en, vi, den, dvi, branches in TREE:
        nodes.append({"id": tid, "parent": None, "en": en, "vi": vi, "den": den, "dvi": dvi})
        for bid, ben, bvi in branches:
            nodes.append({"id": bid, "parent": tid, "en": ben, "vi": bvi})
    branch_ids = {n["id"] for n in nodes if n["parent"]}
    top = {n["id"]: n["parent"] for n in nodes if n["parent"]}
    items = []
    for name, year, node, authors, venue, title, url, den, dvi in sorted(SYSTEMS, key=lambda s: (s[1], s[0].lower())):
        assert node in branch_ids, name
        items.append({"name": name, "year": year, "node": node, "lineage": top[node], "authors": authors, "venue": f"{venue} {year}",
                      "cite": f"{authors}. {title}. {venue}, {year}.", "url": url, "den": den, "dvi": dvi})
    for i, it in enumerate(items):
        it["id"] = i
    data = {"root": {"en": "Visual SLAM systems", "vi": "Các hệ SLAM thị giác",
                     "den": f"{len(items)} influential systems, grouped by what their front-end measures in an image.",
                     "dvi": f"{len(items)} hệ thống tiêu biểu, nhóm theo thứ mà phần front-end đo trên ảnh."},
            "trees": [{"id": "family", "en": "Family", "vi": "Họ", "nodes": nodes, "field": "node"}],
            "items": items, "chart": "dots", "itemWord": {"en": ["system", "systems"], "vi": ["hệ thống", "hệ thống"]},
            "sota": citation_table()}
    for r in data["sota"]["rows"]:
        print(f'   {r["cites"]:5} {r["rate"]:6}/yr {r["venue"]} {r["year"]} {r["name"][:40]} [{r["en"]}]' + ("  " + r["url"] if r["en"] == "-" else ""))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// Influential visual SLAM systems (hand-picked, references checked); generated by scripts/make_blog_vslam.py.\n"
                   "window.FAMILY = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(OUT, len(items), "systems,", items[0]["year"], "-", items[-1]["year"])
    import blog_cover
    blog_cover.tree_cover(nodes, items, "node", OUT.parent / "cover.svg", OUT.parent / "cover-dark.svg")
    blog_cover.png(OUT.parent / "cover.svg", OUT.parent / "cover.png")


if __name__ == "__main__":
    main()
