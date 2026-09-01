from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.services.government_data_service import (
    get_state_crime_data,
    get_cyber_crime_data,
)
from app.utils.security import get_current_officer


router = APIRouter(
    prefix="/government-data",
    tags=["Government Data"]
)


@router.get("/state-crime")
def state_crime_statistics(
    state: Optional[str] = None,
    current_officer=Depends(get_current_officer)
):
    try:
        records = get_state_crime_data(
            state=state
        )

        return {
            "source": "Open Government Data Platform India / NCRB",
            "dataset": "State/UT-wise IPC Crimes from 2020 to 2022",
            "data_type": "Official Aggregate Government Data",
            "count": len(records),
            "records": records
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.get("/cyber-crime")
def cyber_crime_statistics(
    crime_head: Optional[str] = None,
    current_officer=Depends(get_current_officer)
):
    try:
        records = get_cyber_crime_data(
            crime_head=crime_head
        )

        return {
            "source": "Open Government Data Platform India / NCRB",
            "dataset": "Crime Head-wise Police Disposal of Cyber Crime Cases during 2023",
            "data_type": "Official Aggregate Government Data",
            "count": len(records),
            "records": records
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )