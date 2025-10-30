#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 채널 영상 MP3 다운로더 - Streamlit 버전
채널명을 입력하면 최신 영상 목록을 보여주고, 선택한 영상을 MP3로 다운로드합니다.
"""

import os
import streamlit as st
from typing import List, Dict
import time
import io
import unicodedata
import re

try:
    from yt_dlp import YoutubeDL
except ImportError:
    st.error("yt-dlp가 설치되어 있지 않습니다. 'pip install yt-dlp'를 실행해주세요.")
    st.stop()


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
        # Streamlit Cloud에서는 FFmpeg가 PATH에 있을 것으로 예상
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': False,
            'noprogress': True,
            'progress_hooks': [],
            'postprocessor_hooks': [],
        }

        # 진행 표시 훅 연결
        self.ydl_opts['progress_hooks'].append(self._progress_hook)
        self.ydl_opts['postprocessor_hooks'].append(self._postprocessor_hook)
        
        # Streamlit 세션 상태에 진행상황 저장용
        if 'progress' not in st.session_state:
            st.session_state.progress = None

    def _normalize_visible_text(self, text: str) -> str:
        """유니코드 수학 볼드 등 특수 스타일 문자를 일반 문자로 정규화."""
        if not text:
            return ""
        # NFKD 정규화로 호환 분해 후 결합 부호 제거
        decomposed = unicodedata.normalize('NFKD', text)
        without_marks = ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn')
        # 가시성 향상을 위해 공백 정리
        normalized_spaces = re.sub(r"\s+", " ", without_marks).strip()
        return normalized_spaces

    def _make_filesafe_title(self, title: str) -> str:
        """Windows에서도 안전한 파일명으로 변환."""
        base = self._normalize_visible_text(title) or "audio"
        # 금지 문자 제거
        base = re.sub(r"[<>:\\/\\|?*\"]", " ", base)
        # 제어 문자 제거
        base = ''.join(ch for ch in base if ch >= ' ')
        # 앞뒤 공백/점 제거, 연속 공백 축소
        base = re.sub(r"\s+", " ", base).strip().rstrip('.')
        # 길이 제한
        if len(base) > 150:
            base = base[:150].rstrip()
        # 빈 문자열 방지
        return base or "audio"

    def _progress_hook(self, status_dict: Dict):
        """다운로드 진행상황 표시 훅"""
        status = status_dict.get('status')
        if status == 'downloading':
            downloaded = status_dict.get('downloaded_bytes') or 0
            total = status_dict.get('total_bytes') or status_dict.get('total_bytes_estimate') or 0
            percent = (downloaded / total * 100) if total else 0.0
            speed = status_dict.get('speed')
            eta = status_dict.get('eta')
            
            # 세션 상태에 저장
            st.session_state.progress = {
                'percent': percent,
                'speed': speed,
                'eta': eta,
                'downloaded': downloaded,
                'total': total
            }
        elif status == 'finished':
            st.session_state.progress = {'status': 'converting'}
        elif status == 'error':
            st.session_state.progress = {'status': 'error'}

    def _postprocessor_hook(self, pp_dict: Dict):
        """후처리(오디오 변환) 진행 표시 훅"""
        status = pp_dict.get('status')
        pp = pp_dict.get('postprocessor')
        if status == 'started' and pp == 'FFmpegExtractAudio':
            st.session_state.progress = {'status': 'converting'}
        elif status == 'finished' and pp == 'FFmpegExtractAudio':
            st.session_state.progress = {'status': 'completed'}
    
    def get_channel_videos(self, channel_name: str, max_results: int = 10) -> List[Dict]:
        """
        채널명으로 최신 영상 목록 가져오기
        
        Args:
            channel_name: 유튜브 채널명
            max_results: 가져올 최대 영상 수
        
        Returns:
            영상 정보 리스트
        """
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
                                    channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
                            elif channel_name_found:
                                channel_url = f"https://www.youtube.com/c/{channel_name_found}/videos"
                            else:
                                channel_url = None
                            
                            if channel_url:
                                return self._get_videos_from_url(channel_url, max_results)
                except Exception as e:
                    pass
                
                # 방법 2: 직접 채널 URL 시도
                possible_urls = [
                    f"https://www.youtube.com/@{channel_name}/videos",
                    f"https://www.youtube.com/c/{channel_name}/videos",
                    f"https://www.youtube.com/user/{channel_name}/videos",
                    f"https://www.youtube.com/channel/{channel_name}/videos",
                ]
                
                for url in possible_urls:
                    try:
                        videos = self._get_videos_from_url(url, max_results)
                        if videos:
                            return videos
                    except Exception:
                        continue
                
                return []
                
        except Exception as e:
            st.error(f"오류 발생: {e}")
            return []
    
    def _get_videos_from_url(self, channel_url: str, max_results: int = 10) -> List[Dict]:
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
        
        seconds = int(float(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    
    
    def download_video(self, video_url: str, video_title: str = ""):
        """
        영상을 MP3로 다운로드
        
        Args:
            video_url: 다운로드할 영상 URL
            video_title: 영상 제목 (로그용)
        
        Returns:
            다운로드된 파일 경로 (성공 시)
        """
        try:
            st.session_state.progress = {'status': 'downloading', 'percent': 0}
            # 파일명 안전화 적용
            safe_title = self._make_filesafe_title(video_title or "")
            ydl_opts_local = dict(self.ydl_opts)
            ydl_opts_local['outtmpl'] = os.path.join(self.download_dir, f"{safe_title}.%(ext)s")
            with YoutubeDL(ydl_opts_local) as ydl:
                ydl.download([video_url])
            # 예상 경로 우선 반환
            expected_path = os.path.join(self.download_dir, f"{safe_title}.mp3")
            if os.path.exists(expected_path):
                return expected_path
            # 폴백: 가장 최근 mp3 파일
            files = os.listdir(self.download_dir)
            mp3_files = [f for f in files if f.endswith('.mp3')]
            if mp3_files:
                mp3_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)), reverse=True)
                return os.path.join(self.download_dir, mp3_files[0])
            return None
        except Exception as e:
            st.error(f"다운로드 실패: {e}")
            return None


def main():
    """Streamlit 메인 앱"""
    st.set_page_config(
        page_title="유튜브 MP3 다운로더",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 유튜브 채널 영상 MP3 다운로더")
    st.markdown("---")
    
    # 세션 상태 초기화
    if 'videos' not in st.session_state:
        st.session_state.videos = None
    if 'downloader' not in st.session_state:
        st.session_state.downloader = YouTubeAudioDownloader()
    
    downloader = st.session_state.downloader
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        st.info("""
        **사용 방법:**
        1. 채널명 또는 채널 URL 입력
        2. 영상 목록 확인
        3. 다운로드할 영상 선택
        4. 다운로드 버튼 클릭
        """)
        st.markdown("---")
        st.caption("💡 **팁:** 채널 URL을 직접 입력하면 더 정확합니다")
        st.caption("예: `https://www.youtube.com/@channelname/videos`")
    
    # 채널 검색 섹션
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 세션 상태로 입력값 관리
        if 'channel_input_value' not in st.session_state:
            st.session_state.channel_input_value = ""
        if 'input_key' not in st.session_state:
            st.session_state.input_key = 0
        
        channel_input = st.text_input(
            "채널명 또는 채널 URL 입력",
            value=st.session_state.channel_input_value,
            placeholder="예: TED 또는 https://www.youtube.com/@TED/videos",
            key=f"channel_input_{st.session_state.input_key}"
        )
    
    with col2:
        st.write("")  # 간격 맞추기
        search_button = st.button("🔍 검색", type="primary", use_container_width=True)
    
    # 자주 쓰는 채널 빠른 선택 버튼 (URL 사용 - 더 빠름)
    st.markdown("### ⚡ 자주 쓰는 채널")
    quick_channel_epz = st.button("📻 English Podcast Zone", use_container_width=True)
    quick_channel_bob = st.button("📺 Learn English with Bob the Canadian", use_container_width=True)

    # 공통 핸들러
    def quick_search(channel_url: str, fallback_name: str):
        with st.spinner("채널을 검색하는 중..."):
            try:
                videos = downloader._get_videos_from_url(channel_url, max_results=10)
                if not videos:
                    videos = downloader.get_channel_videos(fallback_name, max_results=10)
                if videos:
                    st.session_state.videos = videos
                    st.success(f"✅ {len(videos)}개의 영상을 찾았습니다!")
                    st.session_state.channel_input_value = ""
                    st.session_state.input_key += 1  # 입력창 key 변경으로 강제 재생성
                    st.rerun()
                else:
                    st.error("❌ 영상을 찾을 수 없습니다.")
                    st.session_state.videos = None
                    st.rerun()
            except Exception as e:
                st.error(f"오류 발생: {e}")
                st.session_state.videos = None

    # 빠른 선택 버튼 클릭 시 자동 검색 (URL 직접 사용으로 더 빠름)
    if quick_channel_epz:
        quick_search(
            channel_url="https://www.youtube.com/@EnglishPodcastZone/videos",
            fallback_name="English Podcast Zone",
        )
    if quick_channel_bob:
        quick_search(
            channel_url="https://www.youtube.com/@LearnEnglishwithBobtheCanadian/videos",
            fallback_name="Learn English with Bob the Canadian",
        )
    
    # 영상 검색 실행 (일반 검색 버튼)
    if search_button and channel_input:
        # 검색어 저장
        search_term = channel_input
        
        with st.spinner("채널을 검색하는 중..."):
            try:
                if search_term.startswith('http'):
                    videos = downloader._get_videos_from_url(search_term, max_results=10)
                else:
                    videos = downloader.get_channel_videos(search_term, max_results=10)
                
                # 검색 완료 후 입력창 초기화
                st.session_state.channel_input_value = ""
                st.session_state.input_key += 1  # 입력창 key 변경으로 강제 재생성
                
                if videos:
                    st.session_state.videos = videos
                    st.success(f"✅ {len(videos)}개의 영상을 찾았습니다!")
                else:
                    st.error("❌ 영상을 찾을 수 없습니다. 채널명 또는 URL을 확인해주세요.")
                    st.session_state.videos = None
                
                # 페이지 재로드로 입력창 초기화 확실히 적용
                st.rerun()
            except Exception as e:
                # 오류 발생 시에도 입력창 초기화
                st.session_state.channel_input_value = ""
                st.session_state.input_key += 1
                st.error(f"오류 발생: {e}")
                st.session_state.videos = None
                st.rerun()
    
    # 영상 목록 표시
    if st.session_state.videos:
        st.markdown("---")
        st.subheader(f"📹 영상 목록 ({len(st.session_state.videos)}개)")
        
        # 영상 선택
        selected_videos = []
        videos_container = st.container()
        
        with videos_container:
            for video in st.session_state.videos:
                col1, col2, col3 = st.columns([1, 5, 1])
                
                with col1:
                    checkbox_key = f"video_{video['id']}"
                    if st.checkbox("선택", key=checkbox_key, label_visibility="hidden"):
                        selected_videos.append(video)
                
                with col2:
                    duration_str = downloader.format_duration(video.get('duration', 0))
                    # 제목을 기본 폰트/기본 굵기로 보이도록 정규화하여 출력
                    title_norm = unicodedata.normalize('NFKD', video['title'])
                    title_norm = ''.join(c for c in title_norm if unicodedata.category(c) != 'Mn')
                    st.markdown(f"<div style='font-size: 20px; font-weight: 400; margin-bottom: 5px;'>{title_norm}</div>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color: #666; margin-top: 5px;'>⏱️ {duration_str} | 🔗 <a href='{video['url']}' target='_blank'>YouTube 보기</a></p>", unsafe_allow_html=True)
                
                with col3:
                    video_num = video['index']
                    st.markdown(f"<div style='text-align: center; color: #888;'>#{video_num}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
        
        # 다운로드 버튼
        if selected_videos:
            st.markdown("---")
            st.subheader(f"📥 다운로드 ({len(selected_videos)}개 선택됨)")
            
            if st.button("⬇️ 선택한 영상 다운로드", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                downloaded_files_list = []
                
                for idx, video in enumerate(selected_videos):
                    status_text.info(f"📥 다운로드 중: {video['title']}")
                    progress_bar.progress((idx + 1) / len(selected_videos))
                    
                    downloaded_file = downloader.download_video(video['url'], video['title'])
                    
                    if downloaded_file:
                        title_display = downloader._normalize_visible_text(video['title'])
                        downloaded_files_list.append({
                            'title': title_display,
                            'path': downloaded_file,
                            'filename': os.path.basename(downloaded_file)
                        })
                
                progress_bar.empty()
                status_text.success("✅ 모든 다운로드가 완료되었습니다!")
                
                # 다운로드된 파일 목록 표시
                if downloaded_files_list:
                    st.markdown("### 📁 다운로드 완료된 파일")
                    for file_info in downloaded_files_list:
                        file_path_abs = os.path.abspath(file_info['path'])
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**{file_info['title']}**")
                            st.code(file_path_abs, language=None)
                        
                        with col2:
                            # 파일 읽기 및 다운로드 버튼 제공
                            try:
                                with open(file_info['path'], 'rb') as f:
                                    file_data = f.read()
                                
                                st.download_button(
                                    label="💾 다운로드",
                                    data=file_data,
                                    file_name=file_info['filename'],
                                    mime="audio/mpeg",
                                    key=f"download_btn_{file_info['filename']}"
                                )
                            except Exception as e:
                                st.error(f"파일 읽기 오류: {e}")
                        
                        st.markdown("---")


if __name__ == "__main__":
    main()

