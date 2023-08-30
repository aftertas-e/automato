# automato

## 파일 별 상세 설명

- /darknet-workspace: task에 맞춰 백본(darknet)을 학습하고, yolov4에 적용하는 워크스페이스
  - 세부 사항은 https://github.com/AlexeyAB/darknet#how-to-improve-object-detection 참조
- /darknet2trt: 학습완료된 백본(darknet)을 onnx로, 그리고 trt로 변환하는 워크스페이스(torch의 경우 onnx의 중간거침이 필요하기 때문)
- final-files: 학습완료후 최종파일
  - yolov4_1_3_416_416_static.onnx: 학습완료된 백본의 onnx 변환 파일(pth2onnx)
  - automato_y4tiny_jetson.engine: 학습완료된 백본의 trt 변환 파일(onnx2engine)
- Automato.py: 제안 시스템의 구현 소스코드(플로우)
- **Github에 등재되지 않은 파일들은 드라이브(https://drive.google.com/drive/folders/1LXH3k1agTR910rDE_ZnqBUIAj_FNHb3z?usp=sharing)를 참조해주세요(파일 용량문제로 별도 업로드).**

---

## YOLOv4 -tiny (다크넷) 커맨드 모음

Requirements :
https://github.com/AlexeyAB/darknet#how-to-improve-object-detection의 요구사항

0. Needed files

- About model training
- custom.data # classes 개수, train data, valid data, names, backup 경로 설정
- yolov4-tiny-custom.cfg # YOLOv4-tiny의 Custom Training을 위한 configure file (모델 구성정보 파일)
- yolov4-tiny.conv.29 # Pre-trained Weight


-> About model testing

- custom.data # 위와 동일
- yolov4-tiny-custom_test.cfg # testing을 위한 모델 구성 정보 파일, yolov4-tiny-custom.cfg와 width, height size 외엔 변동사항 없음.
- yolov4-tiny-custom_final.weights / 학습한 모델의 가중치 파일로, 매우 중요.


상위 항목은 Fruit data에 맞게 모두 지정돼있으며, 아래 커맨드만 입력하면 됩니다.

1. Model Training

Command :
./darknet detector train custom/custom.data custom/yolov4-tiny-custom.cfg yolov4-tiny.conv.29 -map

2. Model Test

Command :

# test.sh 생성

./darknet detector test custom/custom.data custom/yolov4-tiny-custom_test.cfg backup/yolov4-tiny-custom_final.weights
./data/sample.jpg # 로컬에 저장된 이미지를 입력 하면됩니다. (사과, 바나나, 오렌지를 다운받아 테스트 가능)

# test.sh 실행

./?.sh # 배쉬파일 실행, 위 생성 옵션에서 이미지를 출력할 수 있습니다. (패스)

---

## TensorRT Setting for YOLOv4

(FILE의 필요한 부분만 가져다가 쓸 것!)

Frameworks :
Darknet (or Pytorch) -> ONNX -> TensorRT(engine) -> inference(use)

참조 링크 : https://github.com/Tianxiaomo/pytorch-YOLOv4

1. Darknet to Onnx (ONNX 변환)
   -> 반드시 제공된 파일로 수정 : (tool/utils.py)

> onnxruntime 필요 (pip install onnxruntime)

> 아래 명령어 실행 :
> python demo_darknet2onnx.py <cfgFile> <namesFile> <weightFile> <imageFile> <batchSize>

e.g., python demo_darknet2onnx.py custom/yolov4-tiny-custom.cfg custom/custom.names yolov4-tiny-custom.weights data/apple.jpg 1

> onnx file : yolov4_1_3_416_416_static.onnx이 생성
> -> demo_darknet2onnx.py(정확히는 tool/utils.py)에서 에러가 발생할 수 있는데, 자료형 변환으로 해결 가능할 수 있음(해당 이슈는 구글링 가능).


2. ONNX to TensorRT

2-1. TensorRT 설치
우선 TensorRT를 실행하기위한 환경은 두 가지로 나뉨
(가). 로컬에 TensorRT 설치 -> 진행 : 버전 의존성이 짙어서 비추
(나). nvidia-docker 사용 -> 필요한 버전에 유동적으로 설치 가능(추천)

> 필자의 경우 (나) 방식으로 engine을 제작했습니다.

- nvidia-docker를 이용한 trt 환경 구축
  (i). docker 설치 (구글링) : https://blog.dalso.org/linux/ubuntu-20-04-lts/13118 참조 (portainer 전까지 하면 됨)
  (ii). nvidia-docker 설정 :
  https://catalog.ngc.nvidia.com/orgs/nvidia/containers/tensorrt 링크 접속
  (iii). 터미널에 아래 명령어 입력 :
  sudo docker run --gpus all -it -v local_dir:/workspace nvcr.io/nvidia/tensorrt:21.12-py3
  -> 시간 소요 후 설치 및 docker가 실행 될 것입니다.

2-2. 로컬에 있는 파일을 도커로 저장
(i). sudo docker ps 후 현재 nvidia-docker의 NAMES를 확인
(ii). https://itholic.github.io/docker-copy/의 명령어를 참조하여 /workspace/tensorrt 에 위치시킴
-> 복사할 파일은 pytorch-YOLOv4-workspace 폴더 전체를 하는 걸 권장합니다. (onnx 파일은 반드시 카피해야함)

2-3. ONNX 모델 단순화

> onnx-simplifier 필요 (pip install onnx-simplifier)
> -> onnx 모델의 구조가 복잡하면 engine 변환 시 에러가 발생하기 때문

ONNX 모델을 아래 명령어로 단순화 시킴 :
python3 -m onnxsim <original onnx file> <output onnx file>

e.g., python3 -m onnxsim yolov4_1_3_416_416_static.onnx y4_simple.onnx

2-4. tensorrt 실행을 위한 사전 컴파일이 필요함. 
아래 명령어 입력 및 컴파일 진행
/opt/tensorrt/python/python_setup.sh # tensorrt를 위한 의존라이브러리 설치 (쫌 걸리는데 하는게 좋아보여서 했어요)
cd /workspace/tensorrt/samples
make -j4 # 이때 -j는 코어의 개수, cpu 코어에 따라 유동적으로 설정
cd ../bin
./sample_mnist # tensorrt가 잘 빌드됐는지 확인 (예제 파일 같은 것임, 텍스트 @@@ 꼴로 숫자 뜨면 잘 된 것)

2-5. trtexec 실행 및 engine 생성 
cd /workspace/tensorrt/pytorch-YOLOv4-workspace 후 아래 명령어 입력 :
trtexec --onnx=<onnx_file> --explicitBatch --saveEngine=<tensorRT_engine_file> --workspace=<size_in_megabytes> --fp16

e.g., trtexec --onnx=y4_simple.onnx --explicitBatch --saveEngine=automato_y4tiny.engine --workspace=2048 --fp16
"정적이냐 동적이냐, 옵션은 뭐로 할 거냐에 따라 명령어 다르므로 맨 상위 링크 (https://github.com/Tianxiaomo/pytorch-YOLOv4)의 표기된 명령어 참조 바랍니다."

-> 여기서 에러가 발생할 수 있는데, 워크스페이스 크기 문제일 수도 있고, 본인은 경험상 "tensorrt 버전 호환성"이 가장 컸음. 도커를 권장하는 이유는 바로 이 것 때문입니다.
-> 에러 없이 잘 성공하면 마지막에 "PASSED"가 출력이 되고 내가 지정한 이름으로 engine이 생성될 것입니다.
-> 에러 뜨면 애도를.. (FAILED가 안뜨길..!)

2-6. engine을 통한 inference
-> 반드시 제공된 파일로 수정 : (demo_trt.py, cfg.py)
데모 실행은 다음 명령어를 사용 :

e.g., python demo_trt.py automato_y4tiny.engine data/apple.jpg 416 416

-> 우리가 모델 학습시 사용한 이미지 크기는 416x416임 ! 따라서 416 416을 입력합니다.
-> "반드시" 짚고 넘어가야 할 것이, demo_trt.py에서의 class 개수를 우리의 학습 데이터셋 기준에 맞게 "변*경" 해줘야 합니다. 80->6, 박스 수도 변경했음.
-> 또한 cfg.py도 우리 모델에 맞게 "수*정" 해야합니다. demo_trt.py와 cfg.py는 데이터셋에 맞게 수정된 파일을 제가 이곳에서 제공합니다. (천사 지석훈)

이제 끝!이며, 인퍼런스 속도와 결과 파일, 정확도를 비교해보면 됩니다.
정확도는 아주 살짝 떨어진 반면에 속도는(기존 건 안재봤지만) 빨라(졌을)것입니다(..^^)

*참고로, 도커에서 로컬로 파일을 복사하면 권한 문제가 발생하는데,
sudo chown -R {username:username} {directory_name} 으로 권한 변경하면 됩니다.

e.g., sudo chown -R kan:kan pytorch-YOLOv4-workspace/

