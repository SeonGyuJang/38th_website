"""
조직도(Organization) Repository
"""
from typing import List, Dict, Any
from .base_repository import BaseRepository


class OrganizationRepository(BaseRepository):
    """조직도 관련 데이터 접근 클래스"""

    def __init__(self):
        super().__init__("organization")

    def get_presidents(self) -> List[Dict[str, Any]]:
        """
        회장단 조회 (회장, 부회장)

        Returns:
            List[Dict[str, Any]]: 회장단 리스트
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .like("position", "%회장%")
            .order("order")
            .execute()
        )
        return response.data

    def get_committee_heads(self) -> List[Dict[str, Any]]:
        """
        위원장 조회

        Returns:
            List[Dict[str, Any]]: 위원장 리스트
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .like("position", "%위원장%")
            .order("order")
            .execute()
        )
        return response.data

    def get_by_department(self, department: str) -> List[Dict[str, Any]]:
        """
        부서별 조직도 조회

        Args:
            department: 부서명

        Returns:
            List[Dict[str, Any]]: 조직 구성원 리스트
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("department", department)
            .order("order")
            .execute()
        )
        return response.data

    def get_all_by_departments(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        모든 구성원을 부서별로 그룹화하여 조회

        Returns:
            Dict[str, List[Dict[str, Any]]]: 부서별 구성원 딕셔너리
        """
        response = self.supabase.table(self.table).select("*").order("order").execute()

        departments = {}
        for member in response.data:
            dept = member.get('department') or "회장단 및 중앙기구"
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(member)

        return departments

    def get_by_position(self, position: str) -> List[Dict[str, Any]]:
        """
        직책별 조회

        Args:
            position: 직책 (국장, 차장, 국원 등)

        Returns:
            List[Dict[str, Any]]: 구성원 리스트
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("position", position)
            .order("order")
            .execute()
        )
        return response.data
