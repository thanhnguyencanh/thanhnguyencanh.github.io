#!/usr/bin/env python3
"""Data for the blog post "Visual SLAM datasets" (blog/vslam-datasets/data.js): 21 datasets with their papers.

The facts in each description come from the dataset's own page or paper (read in November 2026). Papers from 2015 on are
looked up by title in the Paper Explorer data (explorer/data, from dblp), so title, authors, venue, year and link come from
there; the older ones, GCPR, TPAMI and arXiv-only papers were checked on Crossref or arXiv.

Run after scripts/make_paper_explorer.py:  python3 scripts/make_blog_vslam_datasets.py   (then python3 scripts/build_site.py)
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "explorer" / "data"
OUT = ROOT / "blog" / "vslam-datasets" / "data.js"

# two classifications: where the data was recorded, and where its reference trajectory comes from
SETTING = [
    ("indoor", "Indoor", "Trong nhà", "Rooms, offices and whole buildings.", "Phòng, văn phòng và cả tòa nhà.",
     [("rooms", "Rooms", "Phòng"), ("buildings", "Whole buildings", "Cả tòa nhà")]),
    ("mixed", "Indoor and outdoor, handheld", "Trong nhà và ngoài trời, cầm tay", "A person carries the sensors through corridors, halls and streets.",
     "Một người mang cảm biến đi qua hành lang, sảnh và đường phố.", [("handheld", "Handheld", "Cầm tay")]),
    ("roads", "Roads", "Đường phố", "Cars driving through cities, suburbs and highways.", "Ô tô chạy qua thành phố, vùng ven đô và đường cao tốc.",
     [("driving", "Driving", "Lái xe")]),
    ("field", "Field", "Hiện trường", "Robots off the road: terrain, mines and tunnels.", "Robot ngoài đường phố: địa hình, hầm mỏ và đường hầm.",
     [("offroad", "Off-road", "Địa hình"), ("underground", "Mines and tunnels", "Hầm mỏ và đường hầm")]),
    ("synthetic", "Synthetic", "Tổng hợp", "Rendered images with exact ground truth.", "Ảnh kết xuất với ground truth chính xác tuyệt đối.",
     [("rendered", "Rendered rooms", "Phòng kết xuất"), ("simworlds", "Simulated worlds", "Thế giới mô phỏng")]),
]
TRUTH = [
    ("tracked", "External tracking", "Theo dõi từ bên ngoài", "A motion-capture system tracks markers on the sensor rig.",
     "Một hệ bắt chuyển động theo dõi các điểm đánh dấu trên giá cảm biến.", [("mocap", "Motion capture", "Hệ bắt chuyển động")]),
    ("global", "Satellite positioning", "Định vị vệ tinh", "GNSS and inertial sensors, alone or fused with vision.",
     "GNSS và cảm biến quán tính, dùng riêng hoặc hợp nhất với thị giác.",
     [("gnss", "GNSS/INS", "GNSS/INS"), ("sfmgps", "Structure from motion with GPS", "Cấu trúc từ chuyển động kèm GPS")]),
    ("laser", "LiDAR and laser scans", "LiDAR và quét laser", "Poses from LiDAR SLAM, or registered to a laser-scanned model.",
     "Tư thế từ LiDAR SLAM, hoặc đăng ký vào mô hình quét laser.",
     [("lidarslam", "LiDAR SLAM", "LiDAR SLAM"), ("laserreg", "Registered to a laser scan", "Đăng ký vào bản quét laser")]),
    ("self", "From the data itself", "Từ chính dữ liệu", "Poses from the dataset's own reconstruction or odometry: a reference, not an independent truth.",
     "Tư thế từ chính bản tái tạo hoặc đo hành trình của bộ dữ liệu: là tham chiếu, không phải sự thật độc lập.",
     [("recon", "RGB-D reconstruction", "Tái tạo RGB-D"), ("viopgo", "Odometry and loop closures", "Đo hành trình và đóng vòng")]),
    ("partial", "Drift only", "Chỉ đo sai số trôi", "The path starts and ends at the same place; only the accumulated drift is measured.",
     "Quỹ đạo bắt đầu và kết thúc tại cùng một chỗ; chỉ đo sai số trôi tích lũy.", [("drift", "Start equals end", "Điểm đầu trùng điểm cuối")]),
    ("exact", "Exact", "Chính xác", "Synthetic data: the rendering camera is known exactly.", "Dữ liệu tổng hợp: camera kết xuất được biết chính xác.",
     [("rendered-gt", "Rendered", "Kết xuất")]),
    ("none", "No trajectories", "Không có quỹ đạo", "Labels for perception, no reference trajectory.", "Nhãn cho tri giác, không có quỹ đạo tham chiếu.",
     [("labels", "Labels only", "Chỉ có nhãn")]),
]
# features for the comparison table
FEATURES = ["mono", "stereo", "rgbd", "imu", "lidar", "indoor", "outdoor", "field", "synth", "dyn", "light", "long", "large", "sem"]

# (id, name, setting leaf, truth leaf, dataset page, features, explorer title prefix or None, description en, description vi)
DATASETS = [
    ("tum-rgbd", "TUM RGB-D", "rooms", "mocap", "https://cvg.cit.tum.de/data/datasets/rgbd-dataset", "rgbd indoor dyn", None,
     "Kinect color and depth at 640×480 and 30 Hz, with the camera tracked by an eight-camera motion-capture system at 100 Hz. 47 sequences with public ground truth in six groups, from handheld and robot SLAM to texture tests and moving people, plus 33 validation sequences scored online. CC BY 4.0.",
     "Ảnh màu và độ sâu từ Kinect ở 640×480 và 30 Hz, camera được theo dõi bằng hệ bắt chuyển động tám camera ở 100 Hz. 47 chuỗi có ground truth công khai, chia thành sáu nhóm, từ SLAM cầm tay và trên robot đến thử nghiệm kết cấu và người di chuyển, cùng 33 chuỗi kiểm định được chấm điểm trực tuyến. Giấy phép CC BY 4.0."),
    ("tum-mono", "TUM monoVO", "handheld", "drift", "https://cvg.cit.tum.de/data/datasets/mono-dataset", "mono indoor outdoor", None,
     "50 monocular sequences, more than 100 minutes, from narrow corridors to wide outdoor scenes. Each starts and ends at the same place, so accuracy is the drift accumulated in between. All sequences are photometrically calibrated: exposure times, camera response and lens attenuation (vignetting). CC BY 4.0.",
     "50 chuỗi đơn camera, hơn 100 phút, từ hành lang hẹp đến cảnh ngoài trời rộng. Mỗi chuỗi bắt đầu và kết thúc tại cùng một chỗ, nên độ chính xác là sai số trôi tích lũy ở giữa. Mọi chuỗi đều được hiệu chuẩn trắc quang: thời gian phơi sáng, hàm đáp ứng của camera và độ suy giảm ống kính (vignetting). Giấy phép CC BY 4.0."),
    ("tum-vi", "TUM VI", "handheld", "mocap", "https://cvg.cit.tum.de/data/datasets/visual-inertial-dataset", "stereo imu indoor outdoor light", "The TUM VI Benchmark for Evaluating Visual-Inertial",
     "Stereo images at 1024×1024 and 20 Hz with high dynamic range and photometric calibration, and an IMU at 200 Hz, synchronized in hardware. 28 sequences in rooms, corridors, a large hall, outdoors and a dark slide tube. Motion capture at 120 Hz covers the whole trajectory in the room sequences, and only the start and end elsewhere. CC BY 4.0.",
     "Ảnh stereo 1024×1024 ở 20 Hz với dải động cao và hiệu chuẩn trắc quang, cùng IMU 200 Hz, đồng bộ bằng phần cứng. 28 chuỗi trong phòng, hành lang, sảnh lớn, ngoài trời và trong một ống trượt tối. Hệ bắt chuyển động 120 Hz phủ toàn bộ quỹ đạo ở các chuỗi trong phòng, và chỉ phần đầu, phần cuối ở các chuỗi khác. Giấy phép CC BY 4.0."),
    ("4seasons", "4Seasons", "driving", "gnss", "https://cvg.cit.tum.de/data/datasets/4seasons-dataset", "stereo imu outdoor light long large", None,
     "More than 350 km of stereo and IMU driving in nine environments, from a multi-level parking garage to city streets, tunnels, countryside and highway, across seasons, weather, day and night. Reference poses fuse stereo visual-inertial odometry with RTK-GNSS, with up to centimetre accuracy. CC BY-NC-SA 4.0.",
     "Hơn 350 km dữ liệu lái xe với stereo và IMU trong chín môi trường, từ bãi đỗ xe nhiều tầng đến phố thị, đường hầm, nông thôn và đường cao tốc, qua các mùa, thời tiết, ngày và đêm. Tư thế tham chiếu hợp nhất đo hành trình thị giác-quán tính stereo với RTK-GNSS, chính xác tới cỡ centimet. Giấy phép CC BY-NC-SA 4.0."),
    ("kitti", "KITTI odometry", "driving", "gnss", "https://www.cvlibs.net/datasets/kitti/eval_odometry.php", "stereo lidar outdoor large", None,
     "22 stereo sequences from a car, with Velodyne laser scans: 11 with ground truth for training (00–10) and 11 held out for the online benchmark (11–21). Ground truth comes from a GPS/IMU unit (OXTS). Methods are ranked by the average translation and rotation error over all subsequences of 100 to 800 m.",
     "22 chuỗi stereo thu từ ô tô, kèm quét laser Velodyne: 11 chuỗi có ground truth để huấn luyện (00–10) và 11 chuỗi được giữ lại cho bảng xếp hạng trực tuyến (11–21). Ground truth lấy từ thiết bị GPS/IMU (OXTS). Các phương pháp được xếp hạng theo sai số tịnh tiến và quay trung bình trên mọi đoạn con dài 100 đến 800 m."),
    ("semantickitti", "SemanticKITTI", "driving", "gnss", "https://semantic-kitti.org/", "stereo lidar outdoor dyn large sem", "SemanticKITTI: A Dataset for Semantic Scene Understanding",
     "Point-wise semantic labels for every LiDAR scan of all 22 KITTI odometry sequences, over the full 360° view at 10 Hz, with separate classes for moving and parked cars, people and cyclists. Benchmarks cover semantic and panoptic segmentation, moving-object segmentation and semantic scene completion; trajectories are those of KITTI odometry.",
     "Nhãn ngữ nghĩa theo từng điểm cho mọi lần quét LiDAR của cả 22 chuỗi KITTI odometry, phủ toàn bộ 360° ở 10 Hz, với lớp riêng cho xe, người và xe đạp đang di chuyển hay đứng yên. Các bảng xếp hạng gồm phân đoạn ngữ nghĩa và toàn cảnh (panoptic), phân đoạn vật thể chuyển động và hoàn thiện cảnh ngữ nghĩa; quỹ đạo là của KITTI odometry."),
    ("kitti360", "KITTI-360", "driving", "sfmgps", "https://www.cvlibs.net/datasets/kitti-360/", "stereo imu lidar outdoor large sem", None,
     "73.7 km of suburban driving in Karlsruhe with a front stereo camera, two 180° fisheye cameras, a Velodyne and a pushbroom laser scanner, and GPS/IMU. Camera poses are estimated by structure from motion regularized by GPS, with LiDAR loop closures. Dense 2D and 3D semantic and instance labels, and a semantic SLAM benchmark. CC BY-NC-SA 3.0.",
     "73,7 km lái xe ở vùng ven đô Karlsruhe với camera stereo phía trước, hai camera mắt cá 180°, một LiDAR Velodyne và một máy quét laser kiểu pushbroom, cùng GPS/IMU. Tư thế camera được ước lượng bằng cấu trúc từ chuyển động có ràng buộc theo GPS, kèm các vòng lặp từ LiDAR. Có nhãn ngữ nghĩa và thực thể dày đặc cả 2D lẫn 3D, và một bảng xếp hạng SLAM ngữ nghĩa. Giấy phép CC BY-NC-SA 3.0."),
    ("scannet", "ScanNet", "rooms", "recon", "http://www.scan-net.org/", "rgbd indoor sem", "ScanNet: Richly-Annotated 3D Reconstructions",
     "2.5 million RGB-D views in 1,513 scans of indoor scenes, captured with a Structure sensor on an iPad. Camera poses come from the dataset's own reconstruction (BundleFusion), not from an external system; with surface reconstructions and instance-level semantic labels. ScanNet Terms of Use.",
     "2,5 triệu khung hình RGB-D trong 1.513 lần quét cảnh trong nhà, thu bằng cảm biến Structure gắn trên iPad. Tư thế camera lấy từ chính bản tái tạo của bộ dữ liệu (BundleFusion), không phải từ hệ đo bên ngoài; kèm bề mặt tái tạo và nhãn ngữ nghĩa theo từng vật thể. Theo điều khoản sử dụng của ScanNet."),
    ("scannetpp", "ScanNet++", "rooms", "laserreg", "https://scannetpp.mlsg.cit.tum.de/scannetpp/", "rgbd indoor sem", "ScanNet++: A High-Fidelity Dataset",
     "Each scene is scanned by a Faro laser scanner at sub-millimetre resolution, photographed with a 33-megapixel DSLR and recorded as iPhone RGB-D video, all registered together. 460 scenes at publication, extended since. Semantic labels and benchmarks for novel view synthesis and 3D segmentation. Non-commercial research use under signed terms.",
     "Mỗi cảnh được quét bằng máy quét laser Faro với độ phân giải dưới milimet, chụp bằng máy ảnh DSLR 33 megapixel và quay video RGB-D bằng iPhone, tất cả được đăng ký vào cùng một hệ tọa độ. 460 cảnh khi công bố, sau đó được mở rộng thêm. Có nhãn ngữ nghĩa và các bảng xếp hạng tổng hợp góc nhìn mới và phân đoạn 3D. Chỉ dùng cho nghiên cứu phi thương mại, theo điều khoản có chữ ký."),
    ("iclnuim", "ICL-NUIM", "rendered", "rendered-gt", "https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html", "rgbd indoor synth", None,
     "Synthetic RGB-D sequences of a living room and an office, rendered along handheld trajectories taken from real data, with exact poses and optional sensor noise. The living room also has its 3D surface model, so reconstructions can be scored too. Eight sequences of 30 to 51 seconds at 30 Hz, in TUM RGB-D format.",
     "Các chuỗi RGB-D tổng hợp của một phòng khách và một văn phòng, được kết xuất theo quỹ đạo cầm tay lấy từ dữ liệu thật, với tư thế chính xác tuyệt đối và tùy chọn thêm nhiễu cảm biến. Phòng khách còn có mô hình bề mặt 3D, nên có thể chấm điểm cả bản tái tạo. Tám chuỗi dài 30 đến 51 giây ở 30 Hz, theo định dạng TUM RGB-D."),
    ("openloris", "OpenLORIS-Scene", "buildings", "lidarslam", "https://lifelong-robotic-vision.github.io/dataset/scene.html", "rgbd stereo imu lidar indoor dyn light long", "Are We Ready for Service Robots",
     "A wheeled robot revisits real offices, corridors, homes, a café and a market several times, so each scene changes between runs: people, moved objects, day and night. RealSense D435i RGB-D and T265 fisheye stereo, both with IMU, plus wheel odometry and laser scans. Ground truth from motion capture in the office and from offline LiDAR SLAM elsewhere. Robustness and accuracy are scored separately.",
     "Một robot bánh xe đi lại nhiều lần trong văn phòng, hành lang, nhà ở, quán cà phê và một khu chợ thật, nên mỗi cảnh thay đổi giữa các lần chạy: con người, đồ vật bị dời chỗ, ngày và đêm. Có RGB-D từ RealSense D435i và stereo mắt cá từ T265, cả hai kèm IMU, cùng đo hành trình bánh xe và quét laser. Ground truth từ hệ bắt chuyển động trong văn phòng và từ LiDAR SLAM ngoại tuyến ở các cảnh khác. Độ bền vững và độ chính xác được chấm riêng."),
    ("rgbdscenes2", "RGB-D Scenes v2", "rooms", "recon", "https://rgbd-dataset.cs.washington.edu/dataset/rgbd-scenes-v2/", "rgbd indoor sem", None,
     "14 indoor scenes with furniture and tabletop objects (bowls, caps, cereal boxes, mugs, soda cans). Each scene is a point cloud built by aligning its video frames (Patch Volumes mapping), with object labels and the camera poses of that reconstruction. Better suited to object-level and semantic mapping than to trajectory accuracy.",
     "14 cảnh trong nhà có đồ nội thất và đồ vật trên bàn (bát, mũ, hộp ngũ cốc, cốc, lon nước ngọt). Mỗi cảnh là một đám mây điểm dựng bằng cách căn chỉnh các khung hình video (Patch Volumes), kèm nhãn vật thể và tư thế camera của chính bản tái tạo đó. Phù hợp với lập bản đồ theo vật thể và ngữ nghĩa hơn là đo độ chính xác quỹ đạo."),
    ("bonn", "Bonn RGB-D Dynamic", "rooms", "mocap", "https://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/index.html", "rgbd indoor dyn", "ReFusion: 3D Reconstruction in Dynamic Environments",
     "24 highly dynamic RGB-D sequences, with people moving boxes or playing with balloons, plus 2 static ones. Camera ground truth from an OptiTrack motion-capture system, and a ground-truth point cloud of the static room from a Leica BLK360 laser scanner, so both trajectories and maps can be scored. Same format as TUM RGB-D.",
     "24 chuỗi RGB-D có nhiều vật chuyển động, với người khuân hộp hoặc chơi bóng bay, cùng 2 chuỗi tĩnh. Ground truth của camera từ hệ bắt chuyển động OptiTrack, và một đám mây điểm chuẩn của căn phòng tĩnh từ máy quét laser Leica BLK360, nên chấm điểm được cả quỹ đạo lẫn bản đồ. Cùng định dạng với TUM RGB-D."),
    ("autosense", "AutoSense", "buildings", "lidarslam", "https://snt-arg.github.io/vsgraphs-results/", "rgbd lidar indoor sem", "vS-Graphs: Tightly Coupling Visual SLAM",
     "The in-house dataset of vS-Graphs: 6 indoor sequences, about 44 minutes and 620 m in total, from single rooms to suites of rooms linked by corridors. A custom device (SMapper), also mounted on a legged robot, records RGB-D video and LiDAR. Ground truth comes from LiDAR poses and point clouds (S-Graphs), and the walls, rooms and floors of each sequence are counted for scene-graph evaluation.",
     "Bộ dữ liệu nội bộ của vS-Graphs: 6 chuỗi trong nhà, tổng cộng khoảng 44 phút và 620 m, từ một phòng đơn đến dãy phòng nối với nhau bằng hành lang. Một thiết bị tự chế (SMapper), có lúc gắn trên robot bốn chân, ghi video RGB-D và LiDAR. Ground truth lấy từ tư thế và đám mây điểm LiDAR (S-Graphs), và số tường, phòng và tầng trong mỗi chuỗi được đếm để đánh giá đồ thị cảnh."),
    ("rellis3d", "RELLIS-3D", "offroad", "lidarslam", "https://github.com/unmannedlab/RELLIS-3D", "stereo imu lidar field sem", "RELLIS-3D Dataset",
     "Off-road driving on the Rellis campus of Texas A&M with two LiDARs (Ouster 64-beam, Velodyne 32-beam), a stereo camera, an RGB camera and a GNSS/INS. 13,556 LiDAR scans and 6,235 images have semantic labels. Scan poses come from a LiDAR SLAM with loop closure, because the INS alone left the map inconsistent. CC BY-NC-SA 3.0.",
     "Lái xe địa hình trong khuôn viên Rellis của Texas A&M với hai LiDAR (Ouster 64 tia, Velodyne 32 tia), một camera stereo, một camera RGB và một GNSS/INS. 13.556 lần quét LiDAR và 6.235 ảnh có nhãn ngữ nghĩa. Tư thế mỗi lần quét lấy từ LiDAR SLAM có đóng vòng, vì riêng INS vẫn để lại bản đồ không nhất quán. Giấy phép CC BY-NC-SA 3.0."),
    ("rugd", "RUGD", "offroad", "labels", "http://rugd.vision/", "mono field sem", "A RUGD Dataset for Autonomous Navigation",
     "Video from the camera of a small, rugged ground robot driving through unstructured outdoor terrain. 18 sequences with dense pixel labels on every fifth frame, 24 classes including 8 terrain types. Frames and labels only, without trajectories: a dataset for off-road perception rather than for scoring SLAM.",
     "Video từ camera của một robot mặt đất nhỏ, chắc chắn, di chuyển trên địa hình ngoài trời không có cấu trúc. 18 chuỗi với nhãn dày đặc theo điểm ảnh trên mỗi khung thứ năm, 24 lớp trong đó có 8 loại địa hình. Chỉ có khung hình và nhãn, không có quỹ đạo: bộ dữ liệu cho tri giác địa hình hơn là để chấm điểm SLAM."),
    ("oivio", "OIVIO", "underground", "drift", "https://web.archive.org/web/20220524051651/https://arpg.github.io/oivio/", "stereo imu field light", "A Benchmark for Visual-Inertial Odometry Systems Employing Onboard",
     "36 stereo-inertial sequences, over 145 minutes, in mines, tunnels and other dark places, lit only by an onboard LED of about 1,350, 4,500 or 9,000 lumens; each trajectory was recorded three times at different light levels. RealSense D435i grayscale stereo at 1280×720 and 30 Hz, IMU at 100 Hz, geometric and photometric calibration. Three sequences have a total-station track; the others start and end at the same place. The project page is offline; the link is an archived copy.",
     "36 chuỗi stereo-quán tính, hơn 145 phút, trong hầm mỏ, đường hầm và các nơi tối khác, chỉ được chiếu sáng bằng đèn LED gắn trên thiết bị, khoảng 1.350, 4.500 hoặc 9.000 lumen; mỗi quỹ đạo được thu ba lần ở ba mức sáng. Stereo xám RealSense D435i 1280×720 ở 30 Hz, IMU 100 Hz, có hiệu chuẩn hình học và trắc quang. Ba chuỗi có quỹ đạo đo bằng máy toàn đạc; các chuỗi khác bắt đầu và kết thúc tại cùng một chỗ. Trang dự án đã ngừng hoạt động; liên kết dẫn đến bản lưu trữ."),
    ("eth3d", "ETH3D SLAM", "rooms", "mocap", "https://www.eth3d.net/slam_overview", "stereo rgbd imu indoor", "BAD SLAM",
     "Recorded with a custom rig of synchronized global-shutter cameras and accurate calibration, for visual-inertial monocular, stereo and RGB-D SLAM. 56 training and 35 test sequences inside a motion-capture system, plus 5 training sequences outside it with ground truth from structure from motion. Test results are scored on the online benchmark.",
     "Thu bằng một giá camera tự chế gồm các camera màn trập toàn cục được đồng bộ và hiệu chuẩn chính xác, dành cho SLAM thị giác-quán tính đơn camera, stereo và RGB-D. 56 chuỗi huấn luyện và 35 chuỗi kiểm tra trong vùng của hệ bắt chuyển động, cùng 5 chuỗi huấn luyện bên ngoài có ground truth từ cấu trúc từ chuyển động. Kết quả trên tập kiểm tra được chấm qua bảng xếp hạng trực tuyến."),
    ("tartanair", "TartanAir", "simworlds", "rendered-gt", "https://tartanair.org/", "stereo rgbd imu lidar synth dyn light sem", "TartanAir: A Dataset to Push",
     "Photo-realistic simulation in Unreal Engine with AirSim: 30 environments in the first release, indoor and outdoor, with changing light, weather, moving objects and aggressive motion. Stereo images, depth, segmentation, optical flow, LiDAR and exact poses. TartanAir V2 adds IMU, event cameras and any camera model (pinhole, fisheye, panoramic). CC BY 4.0.",
     "Mô phỏng chân thực bằng Unreal Engine và AirSim: 30 môi trường trong bản đầu, cả trong nhà lẫn ngoài trời, với ánh sáng, thời tiết thay đổi, vật thể chuyển động và chuyển động mạnh. Có ảnh stereo, độ sâu, phân đoạn, luồng quang học, LiDAR và tư thế chính xác tuyệt đối. TartanAir V2 bổ sung IMU, camera sự kiện và mọi mô hình camera (lỗ kim, mắt cá, toàn cảnh). Giấy phép CC BY 4.0."),
    ("stone", "STONE", "offroad", "labels", "https://konyul.github.io/STONE-dataset/", "mono imu lidar field light sem", "STONE Dataset",
     "Off-road robot data from grasslands, farmland, construction sites and lakes, by day and night, with a 128-beam LiDAR, six surround-view cameras, three 4D imaging radars, an RTK GNSS/INS and an IMU. 43 sequences, 50,878 frames. The labels are 3D traversability maps generated automatically from the robot's trajectories: a dataset for off-road perception, with sensors that also suit multi-modal SLAM.",
     "Dữ liệu robot địa hình ở đồng cỏ, ruộng, công trường và ven hồ, cả ngày và đêm, với LiDAR 128 tia, sáu camera nhìn quanh, ba radar ảnh 4D, một GNSS/INS RTK và một IMU. 43 chuỗi, 50.878 khung. Nhãn là bản đồ khả năng di chuyển 3D, tạo tự động từ quỹ đạo của robot: bộ dữ liệu cho tri giác địa hình, với các cảm biến cũng phù hợp cho SLAM đa phương thức."),
    ("scalemaster", "ScaleMaster", "buildings", "viopgo", "https://scalemaster-dataset.github.io/", "rgbd imu lidar indoor dyn light large", "Have We Mastered Scale",
     "A benchmark for the scale consistency of monocular SLAM in large indoor spaces: 25 sequences, more than 3.8 km, in libraries, large halls, parking areas, stairs, a station and rooms, with multi-floor routes, repetitive views, glass, night and low light. An iPhone 14 Pro records RGB, depth and IMU; trajectories are ARKit odometry corrected with manually verified loop closures and pose-graph optimization. 7 sequences also have dense LiDAR maps (Livox HAP) for map-to-map scores such as the Chamfer distance.",
     "Bảng đánh giá độ nhất quán tỉ lệ của SLAM đơn camera trong không gian trong nhà rộng lớn: 25 chuỗi, hơn 3,8 km, trong thư viện, sảnh lớn, bãi đỗ xe, cầu thang, nhà ga và các phòng, gồm cả lộ trình nhiều tầng, cảnh lặp lại, kính, ban đêm và thiếu sáng. iPhone 14 Pro ghi RGB, độ sâu và IMU; quỹ đạo là đo hành trình ARKit được hiệu chỉnh bằng các vòng lặp kiểm tra thủ công và tối ưu đồ thị tư thế. 7 chuỗi còn có bản đồ LiDAR dày đặc (Livox HAP) để chấm điểm bản đồ với bản đồ, ví dụ bằng khoảng cách Chamfer."),
]

# papers before 2015, or outside the Paper Explorer venues: checked on Crossref (DOI) or arXiv
MANUAL = {
    "tum-rgbd": {"year": 2012, "venue": "IROS 2012", "title": "A benchmark for the evaluation of RGB-D SLAM systems",
                 "authors": "Jürgen Sturm, Nikolas Engelhard, Felix Endres, Wolfram Burgard, Daniel Cremers", "url": "https://doi.org/10.1109/IROS.2012.6385773"},
    "tum-mono": {"year": 2016, "venue": "arXiv 2016", "title": "A Photometrically Calibrated Benchmark For Monocular Visual Odometry",
                 "authors": "Jakob Engel, Vladyslav Usenko, Daniel Cremers", "url": "https://arxiv.org/abs/1607.02555"},
    "4seasons": {"year": 2020, "venue": "GCPR 2020", "title": "4Seasons: A Cross-Season Dataset for Multi-Weather SLAM in Autonomous Driving",
                 "authors": "Patrick Wenzel, Rui Wang, Nan Yang, Qing Cheng, Qadeer Khan, Lukas von Stumberg, Niclas Zeller, Daniel Cremers", "url": "https://doi.org/10.1007/978-3-030-71278-5_29"},
    "kitti": {"year": 2012, "venue": "CVPR 2012", "title": "Are we ready for autonomous driving? The KITTI vision benchmark suite",
              "authors": "Andreas Geiger, Philip Lenz, Raquel Urtasun", "url": "https://doi.org/10.1109/CVPR.2012.6248074"},
    "kitti360": {"year": 2023, "venue": "TPAMI 2023", "title": "KITTI-360: A Novel Dataset and Benchmarks for Urban Scene Understanding in 2D and 3D",
                 "authors": "Yiyi Liao, Jun Xie, Andreas Geiger", "url": "https://doi.org/10.1109/TPAMI.2022.3179507"},
    "iclnuim": {"year": 2014, "venue": "ICRA 2014", "title": "A benchmark for RGB-D visual odometry, 3D reconstruction and SLAM",
                "authors": "Ankur Handa, Thomas Whelan, John McDonald, Andrew J. Davison", "url": "https://doi.org/10.1109/ICRA.2014.6907054"},
    "rgbdscenes2": {"year": 2014, "venue": "ICRA 2014", "title": "Unsupervised feature learning for 3D scene labeling",
                    "authors": "Kevin Lai, Liefeng Bo, Dieter Fox", "url": "https://doi.org/10.1109/ICRA.2014.6907298"},
}


def expand(link, codes):
    if link.startswith("10."):
        return "https://doi.org/" + link
    for c, t in codes:
        link = link.replace(c, t)
    return link


def tree(spec, tid, en, vi, field):
    nodes = []
    for top, ten, tvi, den, dvi, leaves in spec:
        nodes.append({"id": top, "parent": None, "en": ten, "vi": tvi, "den": den, "dvi": dvi})
        nodes += [{"id": lid, "parent": top, "en": len_, "vi": lvi} for lid, len_, lvi in leaves]
    return {"id": tid, "en": en, "vi": vi, "nodes": nodes, "field": field}, {lid: top for top, *_, leaves in spec for lid, _, _ in leaves}


def main():
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    files = {v["id"]: json.loads((DATA / f'{v["id"]}.json').read_text(encoding="utf-8")) for v in index["venues"]}
    venue = {v["id"]: v for v in index["venues"]}
    t_set, top_set = tree(SETTING, "setting", "Setting", "Bối cảnh", "s")
    t_gt, top_gt = tree(TRUTH, "truth", "Ground truth", "Ground truth", "g")
    items = []
    for did, name, s, g, site, feats, prefix, den, dvi in DATASETS:
        assert s in top_set and g in top_gt, did
        assert set(feats.split()) <= set(FEATURES), did
        if prefix:
            hits = {d["l"][i]: (vid, i) for vid, d in files.items() for i, t in enumerate(d["t"]) if t.lower().startswith(prefix.lower())}
            assert len(hits) == 1, (did, hits)  # one paper (dblp may list it twice under one DOI)
            vid, i = next(iter(hits.values()))
            d = files[vid]
            meta = {"year": d["y"][i], "venue": f'{venue[vid]["short"]} {d["y"][i]}', "title": d["t"][i], "authors": d["a"][i], "url": expand(d["l"][i], index["codes"])}
        else:
            meta = MANUAL[did]
        items.append({"name": name, "key": did, **meta, "s": s, "g": g, "site": site, "f": feats.split(), "den": den, "dvi": dvi,
                      "cite": f'{meta["authors"]}. {meta["title"]}. {meta["venue"]}.'})
    items.sort(key=lambda x: (x["year"], x["name"].lower()))
    for i, it in enumerate(items):
        it["id"] = i
    data = {"root": {"en": "Visual SLAM datasets", "vi": "Bộ dữ liệu SLAM thị giác",
                     "den": f"{len(items)} datasets for visual SLAM and odometry, from indoor RGB-D rooms to off-road robots and simulated worlds.",
                     "dvi": f"{len(items)} bộ dữ liệu cho SLAM và đo hành trình thị giác, từ phòng RGB-D trong nhà đến robot địa hình và thế giới mô phỏng."},
            "trees": [t_set, t_gt], "items": items, "chart": "dots", "features": FEATURES,
            "itemWord": {"en": ["dataset", "datasets"], "vi": ["bộ dữ liệu", "bộ dữ liệu"]}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// Visual SLAM datasets; generated by scripts/make_blog_vslam_datasets.py.\n"
                   "window.FAMILY = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(OUT, len(items), "datasets;", dict(Counter(top_set[it["s"]] for it in items)), dict(Counter(top_gt[it["g"]] for it in items)),
          items[0]["year"], "-", items[-1]["year"])
    for it in items:
        print(f'  {it["year"]} {it["name"]:20} {it["venue"]:11} {it["url"]}')
    import blog_cover
    blog_cover.tree_cover(t_set["nodes"], items, "s", OUT.parent / "cover.svg", OUT.parent / "cover-dark.svg")
    blog_cover.png(OUT.parent / "cover.svg", OUT.parent / "cover.png")


if __name__ == "__main__":
    main()
