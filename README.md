# 유튜브 채널 영상 MP3 다운로더

유튜브 채널명을 입력하면 최신 영상 목록을 보여주고, 선택한 영상을 MP3 오디오 파일로 다운로드하는 프로그램입니다.

## 필수 요구사항

1. **Python 3.7 이상**
2. **FFmpeg** (오디오 변환용)
   - Windows: [FFmpeg 다운로드](https://ffmpeg.org/download.html)
   - 설치 후 PATH 환경변수에 추가하거나 실행 파일이 있는 폴더를 PATH에 추가해야 합니다.

## 설치 방법

1. 프로젝트 폴더로 이동:
```bash
cd youtube_audio
```

2. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

## 사용 방법

1. 프로그램 실행:
```bash
python youtube_audio_downloader.py
```

2. 채널명 또는 채널 URL 입력:
   - 예: `테드` 또는 `TEDx Talks`
   - 또는 채널 URL: `https://www.youtube.com/@channelname/videos`

3. 나타난 영상 목록에서 다운로드할 영상 선택:
   - 단일 선택: `1`
   - 여러 선택: `1,3,5`
   - 전체 선택: `all`

4. 다운로드 완료 후 `downloads` 폴더에서 MP3 파일 확인

## 주요 기능

- ✅ 채널명 또는 채널 URL로 최신 영상 목록 가져오기
- ✅ 영상 목록 표시 (제목, 길이, URL)
- ✅ 여러 영상 선택 및 일괄 다운로드
- ✅ 자동 MP3 변환 (192kbps)
- ✅ 한국어 인터페이스

## 다운로드 폴더

기본적으로 `downloads` 폴더에 MP3 파일이 저장됩니다.

## 문제 해결

### FFmpeg 오류가 발생하는 경우:
1. FFmpeg가 설치되어 있는지 확인하세요
2. FFmpeg가 PATH 환경변수에 포함되어 있는지 확인하세요
3. Windows의 경우 FFmpeg 실행 파일 경로를 확인하세요

### 채널을 찾을 수 없는 경우:
- 채널 URL을 직접 입력해보세요:
  - `https://www.youtube.com/@channelname/videos`
  - `https://www.youtube.com/c/channelname/videos`
  - `https://www.youtube.com/channel/CHANNEL_ID/videos`

## 라이선스

이 프로그램은 교육 및 개인 사용 목적으로 제작되었습니다. 유튜브의 이용약관을 준수하여 사용하세요.

