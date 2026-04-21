# Windows DLL and EXE Integration

## 목적
AIA를 Windows 운영 환경에서 DLL 연동과 EXE 패키징까지 포함해 사용하기 위한 구조를 정리합니다.

## 포함 구성
- DLL bridge layer
- PyInstaller spec
- Windows PowerShell build script
- GitHub Actions Windows build workflow

## DLL 연동
- `app/integrations/dll_bridge.py`
- 외부 DLL이 export 하는 함수명을 기준으로 호출
- bool/int/string 반환을 기본 지원

## EXE 패키징
- `build/aia_windows.spec`
- `scripts/build_windows_exe.ps1`
- `.github/workflows/windows-build.yml`

## 운영 판단
- Python 소스 그대로 운영 가능
- Windows 단일 배포가 필요하면 EXE 패키징 사용 가능
- 서버 측 기존 DLL 자산이 있다면 bridge 계층으로 점진 통합 가능

## 중요한 점
이 저장소는 EXE/DLL 빌드 가능한 구성을 포함하지만, 실제 산출물은 대상 환경 또는 GitHub Actions에서 빌드해야 합니다.
즉, 코드/설정/워크플로는 포함되지만 바이너리 산출 자체는 배포 파이프라인에서 수행합니다.
