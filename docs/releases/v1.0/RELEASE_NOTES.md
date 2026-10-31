v1.0 정식 배포 · 2026-10-31

## 변경 내용

- 대사·일지·아이템·능력·메뉴 등 확정 문안 **3,571개**를 반영했습니다.
- 게임 지도 25타일과 실제 로딩 문구 1개를 한글화했습니다.
- Windows 패처에서 지원 원본 ISO를 선택하면 새 한글 ISO를 생성합니다. Python이나 별도 패처 설치가 필요 없습니다.
- 검증된 게임 내용·11개 차분·패치 EXE는 기존 준비본과 같습니다. 정식 배포 안내와 PPSSPP 설정 안내를 갱신했습니다.

## 주의사항

- 한국판 `ULKS46015` / 디스크 버전 `1.01`, 아래 해시와 일치하는 원본 ISO 전용입니다.
- 사용처 미확인 문구 404개·별도 그래픽 13개·타이틀 배경 지도명·제작진은 원문을 유지합니다. 캐릭터 이름 입력은 원래 문자 범위입니다.
- 전체 본문 배치·후기·전투·엔딩·모든 저장 경로/직업·실기·다른 버전의 검증은 완료하지 않았습니다.
- 기존 저장은 삭제하거나 변환하지 않습니다. 옛 상태저장보다 새 실행에서 일반 ‘불러오기’를 사용하세요.
- 원본 ISO·패치 완료 ISO·BIOS·세이브·개인 PPSSPP 설정은 포함하지 않습니다.

## 패치 적용 방법

1. 아래 해시와 일치하는 원본 ISO를 직접 준비합니다.
2. **Assets(첨부 파일)**의 `UntoldLegends_KR_v1.0_Windows.zip`을 받아 새 폴더에 모두 압축 해제합니다.
3. `UntoldLegends_KR_Patcher.exe`를 실행하고 원본 ISO와 새 한글 ISO 출력 경로를 선택합니다. 동봉 `data`·`tools` 등의 파일을 함께 유지하세요.
4. 완료 후 결과 해시를 확인하고 PPSSPP에서 생성된 ISO를 직접 엽니다. 원본과 기존 출력 파일은 덮어쓰지 않습니다.

**저장 선택 후 화면만 어두워지면 이 게임의 그래픽 설정에서 ‘버퍼 효과 건너뛰기’를 끄고 게임을 다시 실행하세요.** 게임별 설정을 사용하면 다른 게임의 전역 설정을 유지할 수 있습니다. 사용자 확인에서 저장창이 정상 표시됐고, 분리 GUI 검증에서는 저장 완료까지 확인했습니다. 이동 입력 이상은 사용자가 PPSSPP 설정 문제였다고 확인했습니다.

## SHA-256

| 구분 | SHA-256 |
| --- | --- |
| 원본 ISO (407,601,152바이트) | `27bdf09512f138ed40f76f4c575fd9d373a95026355e6c8d97e300c2d4a0c621` |
| 한글 ISO (410,986,496바이트) | `d12edc5bac1d71bfa9ef6aa78eab4991749b4aa09022106a93c0957a1711faf8` |
| 배포 ZIP (11,809,865바이트) | `9aa5fbaa3410a9cee274e4476a9b93af8758f4b1e59c04416e3fcdab19f29aa3` |

## 검증 범위

실제 독립 EXE의 ISO 적용·결과 검사와 오류 입력 거부, 결과 80파일 비교, ISO 디렉터리·경로 테이블·원본 여백 보존을 확인했습니다. 한글 ISO의 콜드 부팅·프롤로그·타이틀과 선별 장면 표시, 별도 GUI에서 일반 불러오기 및 복사 저장의 저장 완료를 확인했습니다. 패처 GUI 실제 클릭 검수나 전체 완주 검증으로 확대하지 않습니다.

[상세 적용 안내](https://github.com/akuma815/psp-untold-legends-brotherhood-of-the-blade-kr-patch/blob/main/docs/PATCH_GUIDE.txt) · [검증 범위](https://github.com/akuma815/psp-untold-legends-brotherhood-of-the-blade-kr-patch/blob/main/docs/VALIDATION.md) · [문제 제보](https://github.com/akuma815/psp-untold-legends-brotherhood-of-the-blade-kr-patch/issues)
