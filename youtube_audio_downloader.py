#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 채널 영상 MP3 다운로더
채널명을 입력하면 최신 영상 목록을 보여주고, 선택한 영상을 MP3로 다운로드합니다.
"""

import os
import sys
import subprocess
from typing import List, Dict
import json

try:
    from yt_dlp import YoutubeDL
except ImportError:
    print("yt-dlp가 설치되어 있지 않습니다. 'pip install yt-dlp'를 실행해주세요.")
    sys.exit(1)


class YouTubeAudioDownloader:
    def __init__(self, download_dir: str = "downloads"):
        """
        초기화
        
        Args:
            download_dir: 다운로드 파일을 저장할 디렉토리
        """
        self.download_dir = download_dir
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        # yt-dlp 옵션 설정
        # FFmpeg 경로 설정
        ffmpeg_path = r"C:\ffmpeg\bin"
        if os.path.exists(os.path.join(ffmpeg_path, "ffmpeg.exe")):
            ffmpeg_location = ffmpeg_path
        else:
            # PATH에서 찾기 시도
            ffmpeg_location = None
        
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            # 기본 진행 표시를 끄고, 커스텀 진행 표시를 사용
            'quiet': True,
            'no_warnings': False,
            'noprogress': True,
            'progress_hooks': [],
            'postprocessor_hooks': [],
        }
        
        # FFmpeg 경로가 있으면 추가
        if ffmpeg_location:
            self.ydl_opts['ffmpeg_location'] = ffmpeg_location

        # 진행 표시 훅 연결
        self.ydl_opts['progress_hooks'].append(self._progress_hook)
        self.ydl_opts['postprocessor_hooks'].append(self._postprocessor_hook)

    def _print_inline(self, text: str):
        """한 줄 진행상황을 덮어쓰며 출력"""
        try:
            print(f"\r{text}", end='', flush=True)
        except Exception:
            print(text)

    def _progress_hook(self, status_dict: Dict):
        """다운로드 진행상황 표시 훅"""
        status = status_dict.get('status')
        if status == 'downloading':
            downloaded = status_dict.get('downloaded_bytes') or 0
            total = status_dict.get('total_bytes') or status_dict.get('total_bytes_estimate') or 0
            percent = (downloaded / total * 100) if total else 0.0
            speed = status_dict.get('speed')
            eta = status_dict.get('eta')
            speed_str = f"{speed/1024/1024:.2f}MiB/s" if speed else "-"
            eta_str = f"{int(eta)}s" if eta else "-"
            self._print_inline(f"다운로드 중: {percent:5.1f}%  속도: {speed_str}  남은시간: {eta_str}   ")
        elif status == 'finished':
            print("\n다운로드 완료. 오디오 변환을 시작합니다...")
        elif status == 'error':
            print("\n다운로드 중 오류가 발생했습니다.")

    def _postprocessor_hook(self, pp_dict: Dict):
        """후처리(오디오 변환) 진행 힌트 표시 훅"""
        status = pp_dict.get('status')
        pp = pp_dict.get('postprocessor')
        if status == 'started' and pp == 'FFmpegExtractAudio':
            self._print_inline("오디오 변환 중...  ")
        elif status == 'finished' and pp == 'FFmpegExtractAudio':
            print("\n오디오 변환 완료.")
    
    def get_channel_videos(self, channel_name: str, max_results: int = 20) -> List[Dict]:
        """
        채널명으로 최신 영상 목록 가져오기
        
        Args:
            channel_name: 유튜브 채널명
            max_results: 가져올 최대 영상 수
        
        Returns:
            영상 정보 리스트
        """
        print(f"\n'{channel_name}' 채널의 최신 영상을 검색 중...")
        
        search_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        try:
            with YoutubeDL(search_opts) as ydl:
                # 방법 1: 채널명으로 검색하여 채널 URL 찾기
                try:
                    search_query = f"ytsearch1:{channel_name}"
                    info = ydl.extract_info(search_query, download=False)
                    
                    if info and 'entries' in info and len(info['entries']) > 0:
                        first_result = info['entries'][0]
                        channel_id = first_result.get('channel_id') or first_result.get('channel')
                        channel_name_found = first_result.get('channel')
                        
                        if channel_id or channel_name_found:
                            # 채널 URL 구성
                            if channel_id:
                                if channel_id.startswith('@') or channel_id.startswith('UC'):
                                    if channel_id.startswith('@'):
                                        channel_url = f"https://www.youtube.com/{channel_id}/videos"
                                    else:
                                        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
                                else:
                                    # 채널 ID인 경우
                                    channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
                            elif channel_name_found:
                                # 채널명으로 시도
                                channel_url = f"https://www.youtube.com/c/{channel_name_found}/videos"
                            else:
                                channel_url = None
                            
                            if channel_url:
                                print(f"채널 URL: {channel_url}")
                                return self._get_videos_from_url(channel_url, max_results)
                except Exception as e:
                    print(f"채널 검색 시도 1 실패: {e}")
                
                # 방법 2: 직접 채널 URL 시도
                possible_urls = [
                    f"https://www.youtube.com/@{channel_name}/videos",
                    f"https://www.youtube.com/c/{channel_name}/videos",
                    f"https://www.youtube.com/user/{channel_name}/videos",
                    f"https://www.youtube.com/channel/{channel_name}/videos",
                ]
                
                for url in possible_urls:
                    try:
                        print(f"URL 시도: {url}")
                        videos = self._get_videos_from_url(url, max_results)
                        if videos:
                            return videos
                    except Exception as e:
                        continue
                
                print(f"\n채널을 찾을 수 없습니다. 채널 URL을 직접 입력해주세요.")
                print("예: https://www.youtube.com/@channelname/videos")
                return []
                
        except Exception as e:
            print(f"오류 발생: {e}")
            return []
    
    def _get_videos_from_url(self, channel_url: str, max_results: int = 20) -> List[Dict]:
        """채널 URL로부터 영상 목록 가져오기"""
        channel_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        try:
            with YoutubeDL(channel_opts) as ydl:
                channel_info = ydl.extract_info(channel_url, download=False)
                
                if channel_info and 'entries' in channel_info:
                    videos = []
                    for i, entry in enumerate(channel_info['entries'][:max_results], 1):
                        video_id = entry.get('id')
                        if not video_id:
                            continue
                        title = entry.get('title', '제목 없음')
                        url = entry.get('url') or f"https://www.youtube.com/watch?v={video_id}"
                        duration = entry.get('duration', 0)
                        
                        videos.append({
                            'index': i,
                            'title': title,
                            'url': url,
                            'id': video_id,
                            'duration': duration
                        })
                    
                    return videos if videos else None
        except Exception as e:
            raise Exception(f"URL에서 영상 목록 가져오기 실패: {e}")
    
    def format_duration(self, seconds) -> str:
        """초를 시간:분:초 형식으로 변환"""
        if not seconds:
            return "알 수 없음"
        
        # float를 int로 변환
        seconds = int(float(seconds))
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def display_videos(self, videos: List[Dict]):
        """영상 목록 출력"""
        if not videos:
            print("\n영상을 찾을 수 없습니다.")
            return
        
        print(f"\n{'='*80}")
        print(f"총 {len(videos)}개의 영상을 찾았습니다:")
        print(f"{'='*80}\n")
        
        for video in videos:
            duration_str = self.format_duration(video.get('duration', 0))
            print(f"[{video['index']}] {video['title']}")
            print(f"     길이: {duration_str}")
            print(f"     URL: {video['url']}")
            print()
    
    def download_video(self, video_url: str, video_title: str = ""):
        """
        영상을 MP3로 다운로드
        
        Args:
            video_url: 다운로드할 영상 URL
            video_title: 영상 제목 (로그용)
        """
        print(f"\n다운로드 중: {video_title if video_title else video_url}")
        
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([video_url])
            print(f"✓ 다운로드 완료: {video_title}")
        except Exception as e:
            print(f"✗ 다운로드 실패: {e}")
    
    def run(self):
        """메인 실행 함수"""
        print("="*80)
        print("유튜브 채널 영상 MP3 다운로더")
        print("="*80)
        
        # 채널명 입력
        channel_name = input("\n유튜브 채널명 또는 채널 URL을 입력하세요: ").strip()
        
        if not channel_name:
            print("채널명이 입력되지 않았습니다.")
            return
        
        # 채널 URL인 경우 직접 사용
        if channel_name.startswith('http'):
            print("\n채널 URL로부터 영상 목록을 가져오는 중...")
            videos = self._get_videos_from_url(channel_name, max_results=20)
            
            if not videos:
                print("영상을 찾을 수 없습니다. 채널 URL을 확인해주세요.")
                return
            
            self.display_videos(videos)
        else:
            # 채널명으로 검색
            videos = self.get_channel_videos(channel_name, max_results=20)
            
            if not videos:
                print("\n영상을 찾을 수 없습니다. 채널명을 확인하거나 채널 URL을 직접 입력해주세요.")
                print("예: https://www.youtube.com/@channelname/videos")
                return
            
            self.display_videos(videos)
        
        # 영상 선택
        print(f"\n다운로드할 영상을 선택하세요 (숫자 입력, 여러 개는 쉼표로 구분, 예: 1,3,5 또는 'all' 전체 다운로드)")
        print("나가려면 'q'를 입력하세요.")
        
        selection = input("\n선택: ").strip().lower()
        
        if selection == 'q':
            print("프로그램을 종료합니다.")
            return
        
        if selection == 'all':
            selected_indices = list(range(1, len(videos) + 1))
        else:
            try:
                selected_indices = [int(x.strip()) for x in selection.split(',')]
            except ValueError:
                print("잘못된 입력입니다.")
                return
        
        # 선택된 영상 다운로드
        selected_videos = [v for v in videos if v['index'] in selected_indices]
        
        if not selected_videos:
            print("선택한 영상이 없습니다.")
            return
        
        print(f"\n{len(selected_videos)}개의 영상을 다운로드합니다...")
        
        for video in selected_videos:
            self.download_video(video['url'], video['title'])
        
        print(f"\n모든 다운로드가 완료되었습니다!")
        print(f"파일은 '{self.download_dir}' 폴더에 저장되었습니다.")


def main():
    """메인 함수"""
    downloader = YouTubeAudioDownloader()
    
    try:
        downloader.run()
    except KeyboardInterrupt:
        print("\n\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

