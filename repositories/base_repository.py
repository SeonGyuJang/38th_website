"""
Base Repository 클래스

모든 Repository가 상속받는 기본 클래스입니다.
"""
from typing import List, Optional, Dict, Any
from database import get_supabase_client


class BaseRepository:
    """모든 Repository의 기본 클래스"""

    def __init__(self, table_name: str):
        """
        Args:
            table_name: Supabase 테이블 이름
        """
        self.supabase = get_supabase_client()
        self.table = table_name

    def get_all(self, order_by: str = "id", ascending: bool = True) -> List[Dict[str, Any]]:
        """
        모든 레코드 조회

        Args:
            order_by: 정렬할 컬럼명
            ascending: 오름차순 여부

        Returns:
            List[Dict[str, Any]]: 레코드 리스트
        """
        query = self.supabase.table(self.table).select("*").order(order_by, desc=not ascending)
        response = query.execute()
        return response.data

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        ID로 레코드 조회

        Args:
            record_id: 레코드 ID

        Returns:
            Optional[Dict[str, Any]]: 레코드 또는 None
        """
        response = self.supabase.table(self.table).select("*").eq("id", record_id).execute()
        return response.data[0] if response.data else None

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        레코드 생성

        Args:
            data: 생성할 데이터

        Returns:
            Optional[Dict[str, Any]]: 생성된 레코드 또는 None
        """
        response = self.supabase.table(self.table).insert(data).execute()
        return response.data[0] if response.data else None

    def update(self, record_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        레코드 수정

        Args:
            record_id: 레코드 ID
            data: 수정할 데이터

        Returns:
            Optional[Dict[str, Any]]: 수정된 레코드 또는 None
        """
        response = self.supabase.table(self.table).update(data).eq("id", record_id).execute()
        return response.data[0] if response.data else None

    def delete(self, record_id: int) -> bool:
        """
        레코드 삭제

        Args:
            record_id: 레코드 ID

        Returns:
            bool: 삭제 성공 여부
        """
        response = self.supabase.table(self.table).delete().eq("id", record_id).execute()
        return len(response.data) > 0

    def count(self) -> int:
        """
        전체 레코드 개수 조회

        Returns:
            int: 레코드 개수
        """
        response = self.supabase.table(self.table).select("*", count="exact").execute()
        return response.count
