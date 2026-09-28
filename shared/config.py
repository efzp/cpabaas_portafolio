import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BvcMgcSettings:
    page_url: str
    file_url: str
    sql_connection_string: str

    @classmethod
    def from_environment(cls):
        return cls(
            page_url=os.environ["BVC_MGC_PAGE_URL"],
            file_url=os.environ["BVC_MGC_FILE_URL"],
            sql_connection_string=os.environ["SQL_CONNECTION_STRING"],
        )
