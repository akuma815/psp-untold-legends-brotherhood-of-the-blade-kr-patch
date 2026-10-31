# 개발 빌드 입력과 검증

Python 3.12 기준의 개발자 재빌드 절차입니다. 배포 ZIP을 원본 ISO에 적용하려면 [패치 적용 안내](../PATCH_GUIDE.txt)를 확인하세요. 해당 배포 패치에는 Python 설치가 필요하지 않습니다.

```powershell
python -m pip install -r requirements-rebuild.txt
python -B tools/prepare_public_inputs.py
python -B tools/check_inputs.py
```

준비 도구는 저장소에 포함된 재현 메타데이터와 OFL 글꼴을 기존 빌더가 기대하는 로컬 경로에 복사합니다. 기존 내용이 다르면 덮어쓰지 않습니다. 입력 검사는 누락/해시 차이를 경로별로 보고합니다. 공개 소스 자체의 무결성 검사는 다음과 같습니다.

```powershell
python -B tools/check_inputs.py --public-only
```

게임 원본은 저장소에 넣거나 커밋하지 않습니다. 소유한 등록 ISO 경로를 명시해 추출합니다.

```powershell
python -B scripts/survey.py --source "D:/OwnedGames/UntoldLegends.iso" --extract
python -B tools/prepare_public_inputs.py --extract-text
```

`--extract-text`는 추출된 원본 locale로부터 분석 텍스트를 재생성합니다. 원본 크기와 SHA가 다르면 원본 조사기가 거절합니다.

**아직 공개된 소스만으로 전체 빌드를 완성할 수 없습니다.** `inputs/PUBLIC_INPUTS.json`의 `required_local_inputs`에는 원본 유래/중간 그래픽 입력과 기존 빌더가 고정한 외부 어셈블러가 있습니다. 이 자료는 공개에 포함하지 않았습니다. 각 경로에 정확한 크기/해시의 입력이 별도로 있어야 합니다. 도구 버전이나 이미지가 다르면 빌드는 중단하며, 여기서는 그 입력을 내려받거나 대체하지 않습니다.

전체 입력이 준비된 개발 환경에서 검사한 뒤 기존 빌더를 사용합니다.

```powershell
python -B tools/check_inputs.py
python -B scripts/build_map_crisp27_20261030.py --variant unicode_hangul_alias_fallback --name map_crisp27_20261030 --diagnostic-config config/development_map_crisp27_20261030.json
```

결과가 이미 있는 경우 새로 덮어쓰지 말고 검증 모드를 사용합니다.

```powershell
python -B scripts/build_map_crisp27_20261030.py --variant unicode_hangul_alias_fallback --name map_crisp27_20261030 --diagnostic-config config/development_map_crisp27_20261030.json --verify
```

빌드는 원본에서 폴더 형식 결과를 만듭니다. ISO를 만들 필요는 없습니다. 원본·결과 80파일 및 Expected-Write 검사가 성공해야 하며 실제 PPSSPP 실행 검증과는 별개입니다. 기존 상태 저장에는 옛 자산이 남을 수 있으므로 새 결과를 확인할 때는 완전히 재실행한 뒤 일반 불러오기를 사용합니다.
