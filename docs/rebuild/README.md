# 개발 소스 빌드와 xdelta 재생성

Windows/Python3.12 기준입니다. 소유한 등록 원본 ISO와 Git 파일로 현재 v1.0을 재생성합니다. 공식 배포 ZIP 적용만 필요하면 [적용 안내](../PATCH_GUIDE.txt)를 확인하세요. 배포 패처에는 Python이 필요 없습니다.

## 한 번에 xdelta 생성

새 Git 복제본의 현재 main에서 아래 명령을 실행합니다. 원본은 한국판 ULKS46015 v1.01, 407601152바이트, SHA256 `27bdf09512f138ed40f76f4c575fd9d373a95026355e6c8d97e300c2d4a0c621`입니다. 원본 ISO는 Git에 포함하지 않습니다.

```powershell
python -m pip install -r requirements-rebuild.txt
python -B tools/check_inputs.py --public-only
python -B tools/build_v1_xdelta.py --source "D:/OwnedGames/UntoldLegends.iso" --output "D:/Patches/UntoldLegends_KR_v1.0.xdelta"
```

출력 디렉터리는 먼저 만들고 새 파일명을 지정합니다. 원본/기존 패치/기존 보고서는 덮어쓰지 않습니다. 위 도구는 원본 추출→Git의 그래픽 입력 복구→기존 원고 기반 소스 빌드→동결80파일 대조→동일v1.0 ISO 생성→xdelta 인코딩→패치 재적용 ISO 해시 대조를 실행합니다. 비공개 입력 ZIP, 옛 작업 폴더, 기존 릴리즈의 게임 차분은 사용하지 않습니다.

고정 버전 xdelta3의 파일명 헤더를 꺼 경로에 의존하지 않는 패치를 생성합니다. 임시 ISO는 검증 후 정리하고 `.xdelta`와 `.xdelta.json` 보고서만 남깁니다. 게임 폴더는 Git에서 제외되는 `workspace/runtime/git_v1_source_rebuild`에 생성합니다. 이미 같은 결과 폴더가 있으면 검증 모드를 사용합니다.

## 입력 복구와 개별 폴더 빌드

```powershell
python -B tools/prepare_public_inputs.py
python -B scripts/survey.py --source "D:/OwnedGames/UntoldLegends.iso" --extract
python -B tools/prepare_public_inputs.py --extract-text
python -B tools/prepare_build_inputs.py
python -B tools/check_inputs.py
python -B scripts/build_map_crisp27_20261030.py --variant unicode_hangul_alias_fallback --name regenerated_v1 --diagnostic-config config/development_map_crisp27_20261030.json
```

이전 누락 입력11개는 이제 Git에 있는 원본 상대 그래픽 차분10개와 라이선스 도구1개로 복원합니다. 기존515개 입력의 크기·해시는 유지하며 다른 이미지나 임의 도구로 대체하지 않습니다. 완전한 게임 PNG·게임 바이너리·세이브는 공개하지 않습니다. 도구는 [출처·라이선스](../../tools/bin/README.md)를 따릅니다.

결과 ISO는 410986496바이트/SHA256 `d12edc5bac1d71bfa9ef6aa78eab4991749b4aa09022106a93c0957a1711faf8`입니다. 기존 v1.0 공식 릴리즈와 태그는 변경하지 않았습니다. 이번 보완은 main의 복구 도구/재현 자산 변경이며 게임 내용 변경이 아닙니다. 이전 v1.0 태그에는 이 복구 보완이 없으므로 현재 main의 명령을 사용하세요.

전체 플레이/실기/다른 버전 검증이나 과거 개인 저장·상태·관찰 기록의 Git 복구를 뜻하지 않습니다. 상세 기계 결과는 [소스 복구 검증](GIT_SOURCE_RECOVERY_20261031.json)을 확인하세요.
