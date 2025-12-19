"""
일정(Schedule) Repository
"""
from typing import List, Dict, Any
from datetime import datetime
from .base_repository import BaseRepository


class ScheduleRepository(BaseRepository):
    """일정 관련 데이터 접근 클래스"""

    def __init__(self):
        super().__init__("schedule")

    def get_upcoming(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        다가오는 일정 조회

        Args:
            limit: 조회할 최대 개수

        Returns:
            List[Dict[str, Any]]: 일정 리스트
        """
        now = datetime.now().isoformat()
        query = (
            self.supabase.table(self.table)
            .select("*")
            .gte("start_date", now)
            .order("start_date")
            .limit(limit)
        )
        response = query.execute()
        return response.data

    def get_past(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        지난 일정 조회

        Args:
            limit: 조회할 최대 개수

        Returns:
            List[Dict[str, Any]]: 일정 리스트
        """
        now = datetime.now().isoformat()
        query = (
            self.supabase.table(self.table)
            .select("*")
            .lt("start_date", now)
            .order("start_date", desc=True)
            .limit(limit)
        )
        response = query.execute()
        return response.data

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        카테고리별 일정 조회

        Args:
            category: 카테고리명 (회의, 행사, 프로젝트 등)

        Returns:
            List[Dict[str, Any]]: 일정 리스트
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("category", category)
            .order("start_date", desc=True)
            .execute()
        )
        return response.data

    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        날짜 범위로 일정 조회

        Args:
            start_date: 시작 날짜 (ISO format)
            end_date: 종료 날짜 (ISO format)

        Returns:
            List[Dict[str, Any]]: 일정 리스트
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .gte("start_date", start_date)
            .lte("start_date", end_date)
            .order("start_date")
            .execute()
        )
        return response.data
