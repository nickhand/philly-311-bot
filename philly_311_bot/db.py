import pandas as pd
import carto2gpd


class CartoDB(object):
    """
    Interface to Philadelphia's CARTO database for 311 requests.
    """

    url = "https://phl.carto.com/api/v2/sql"
    table_name = "public_cases_fc"

    def count(self, where=None):
        """
        Return the size of the data base.

        Parameters
        ----------
        where : str
            clause to only select a subset of the data
        
        Returns
        -------
        count : int
            the number of rows in the database
        """
        return carto2gpd.get_size(self.url, self.table_name, where=where)

    def query(self, where=None):
        """
        Query the CARTO database.

        Parameters
        ----------
        where : str
            clause to only select a subset of the data

        Returns
        -------
        data : geopandas.GeoDataFrame
            the selected data
        """
        # Get the data
        data = carto2gpd.get(self.url, self.table_name, where=where)

        # format the datetimes
        date_cols = ["expected_datetime", "updated_datetime", "requested_datetime"]
        for col in date_cols:
            if col in data:
                data[col] = pd.to_datetime(data[col])

        return data
