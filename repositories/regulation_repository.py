"""
회칙(Regulation) Repository
"""
from typing import List, Dict, Any
from .base_repository import BaseRepository


class RegulationRepository(BaseRepository):
    """회칙 관련 데이터 접근 클래스"""

    def __init__(self):
        super().__init__("regulation")

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        카테고리별 회칙 조회

        Args:
            category: 카테고리 (총학생회, 동아리연합회 등)

        Returns:
            List[Dict[str, Any]]: 회칙 리스트
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("category", category)
            .order("order")
            .execute()
        )
        return response.data

    def get_all_by_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        모든 회칙을 카테고리별로 그룹화하여 조회

        Returns:
            Dict[str, List[Dict[str, Any]]]: 카테고리별 회칙 딕셔너리
        """
        response = self.supabase.table(self.table).select("*").order("order").execute()

        categories = {}
        for regulation in response.data:
            cat = regulation.get('category', '기타')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(regulation)

        return categories
