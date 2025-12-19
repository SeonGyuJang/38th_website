"""
공약(Promise) Repository
"""
from typing import List, Dict, Any
from .base_repository import BaseRepository


class PromiseRepository(BaseRepository):
    """공약 관련 데이터 접근 클래스"""

    def __init__(self):
        super().__init__("promise")

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        카테고리별 공약 조회

        Args:
            category: 카테고리명 (학술, 복지 등)

        Returns:
            List[Dict[str, Any]]: 공약 리스트
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("category", category)
            .order("order")
            .execute()
        )
        return response.data

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        상태별 공약 조회

        Args:
            status: 상태 (진행중, 완료, 보류)

        Returns:
            List[Dict[str, Any]]: 공약 리스트
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("status", status)
            .order("order")
            .execute()
        )
        return response.data

    def get_with_progress(self, promise_id: int) -> Dict[str, Any]:
        """
        공약과 진행 상황을 함께 조회

        Args:
            promise_id: 공약 ID

        Returns:
            Dict[str, Any]: 공약 정보 및 진행 상황
        """
        # 공약 정보 조회
        promise_response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("id", promise_id)
            .execute()
        )
        promise = promise_response.data[0] if promise_response.data else None

        if not promise:
            return None

        # 진행 상황 조회
        progress_response = (
            self.supabase.table("promise_progress")
            .select("*")
            .eq("promise_id", promise_id)
            .order("date", desc=True)
            .execute()
        )
        promise['progress_updates'] = progress_response.data

        return promise

    def get_average_progress_rate(self) -> float:
        """
        전체 공약의 평균 이행률 계산

        Returns:
            float: 평균 이행률 (0-100)
        """
        response = self.supabase.table(self.table).select("progress_rate").execute()
        if not response.data:
            return 0.0

        total = sum(item['progress_rate'] for item in response.data)
        return total / len(response.data)
