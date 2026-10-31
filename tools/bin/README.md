# 재빌드용 라이선스 도구

두 실행 파일만 원본 크기와 SHA-256을 고정해 포함한다. 도구와 게임 자료는 구분하며 원본 게임·완성 ISO·세이브를 포함하지 않는다.

- `armips.exe`: Kingcom/armips 커밋 `62adab4ef30da765f5cf22a451eb08a59c54dc8b`, Release x64, MSVC19.44.35228로 빌드한 기존 도구. MIT 라이선스 원문 `armips_MIT.txt`와 `armips_BUILD.json`을 포함한다. [소스](https://github.com/Kingcom/armips/tree/62adab4ef30da765f5cf22a451eb08a59c54dc8b). 실행 파일의 재컴파일 해시 재현이나 전체 ISA 검증을 주장하지 않는다.
- `xdelta3.exe`: 기존 v1.0 패키지와 같은 jmacd/xdelta 3.2.0 공식 Windows 도구. Apache2.0, 정적 의존성 liblzma5.8.3(0BSD)/BLAKE3 1.8.5의 원문 라이선스를 함께 포함한다. [소스와 릴리즈](https://github.com/jmacd/xdelta/releases/tag/v3.2.0).

각 정확 해시는 `inputs/BUILD_INPUT_RECOVERY.json`의 `licensed_tools`에서 검사한다. 다른 EXE/DLL/게임 이미지/세이브는 공개 감사가 허용하지 않는다.
