from fastapi import Query
from typing import Optional


class PaginationParams:
    
    def __init__(
        self,
        skip: int = Query(
            0,
            ge=0,
            description="Number of records to skip"
        ),
        limit: int = Query(
            50,
            ge=1,
            le=1000,
            description="Maximum number of records to return"
        )
    ):
        self.skip = skip
        self.limit = limit


class SearchParams:
    
    def __init__(
        self,
        q: Optional[str] = Query(
            None,
            description="Search query string",
            min_length=1,
            max_length=100
        ),
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=1000),
        sort_by: Optional[str] = Query(
            None,
            description="Field to sort by"
        ),
        sort_order: str = Query(
            "desc",
            regex="^(asc|desc)$",
            description="Sort order: asc or desc"
        )
    ):
        self.q = q
        self.skip = skip
        self.limit = limit
        self.sort_by = sort_by
        self.sort_order = sort_order


class DateRangeParams:
    
    def __init__(
        self,
        start_date: Optional[str] = Query(
            None,
            description="Start date (YYYY-MM-DD)"
        ),
        end_date: Optional[str] = Query(
            None,
            description="End date (YYYY-MM-DD)"
        )
    ):
        self.start_date = start_date
        self.end_date = end_date