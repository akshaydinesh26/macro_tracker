from pathlib import Path

import pandas as pd

from macrotracker.api.routes import DataRequest
from macrotracker.database.storage import DatabaseQueryError
from macrotracker.models.models import DataPoint


def retrive_data(data: DataRequest, database_path: Path) -> tuple[list[DataPoint], int]:
    """
    DataRequest.indicator, DataRequest.start_date, and DataRequest.end_date are used to retrieve the data.
    """
    indicator_data_path = database_path / f"{data.indicator}.db"
    if not indicator_data_path.exists():
        raise DatabaseQueryError(f"Database for indicator {data.indicator} not found at {indicator_data_path}")
    # Load the data from the CSV file
    data_table = pd.read_csv(indicator_data_path)
    data_table['date'] = pd.to_datetime(data_table['date'])
    data_table['value'] = pd.to_numeric(data_table['value'])
    query_return = data_table[
        (data_table['date'] >= pd.to_datetime(data.start_date)) &
        (data_table['date'] <= pd.to_datetime(data.end_date))
    ]
    if query_return.empty:
            raise DatabaseQueryError(f"No data found for indicator {data.indicator} in the specified date range.")
    # create respose data structure
    response_data = [DataPoint(datepoint=row['date'], value=row['value']) for _, row in query_return.iterrows()]
    data_point_count = len(response_data)
    
    return response_data, data_point_count

    
