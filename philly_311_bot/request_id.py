import pandas as pd
import re
import collections
import humanize


class RequestIDHandler(object):
    """
    Handle questions about a specific request id.
    """
    @classmethod
    def parse_message(cls, message):
        """
        Check if the message contains a valid request id.

        Parameters
        ----------
        message : str
            the message to check

        Returns
        -------
        bool :
            returns `True` if the message has a valid id number
        """
        # request id is at least 7 digits
        m = re.search("(?P<request_id>[0-9]{7,})", message)
        if m:
            request_id = int(m.groupdict()['request_id'])
            return request_id

        return None

    @classmethod
    def get_response(cls, db, message):
        """
        Get the response to a specific message. 

        If parsing the message fails, e.g., this is not the 
        right handler, ``None`` will be returned.

        Parameters
        ----------
        db : CartoDB
            the database connection to CARTO
        message : str
            the message to parse and respond to 

        Returns
        -------
        None, str : 
            None is returned if parsing fails, otherwise the response
            text is returned
        """
        # parse message and extract a request ID
        request_id = cls.parse_message(message)

        # no match, return error
        if request_id is None:
            return None
        else:
            where = "WHERE service_request_id = %d" % request_id
            df = db.query(where)

            # this means an ID was found, but it led to an error
            if len(df) == 0 or len(df) > 1:
                return None

        # remove missing fields
        row = df.iloc[0].dropna()

        # check if the status is delayed
        now = pd.to_datetime("now")
        delayed = (row['status'] == 'Open') & (
            row['expected_datetime'] < now)
        if delayed:
            row['status'] += ", Delayed"

        # format dates
        for col in ['requested_datetime', 'expected_datetime', 'updated_datetime']:
            if col in row:
                delta = row[col] - now
                row[col] = row[col].strftime("%m/%d/%Y")
                if delta < pd.Timedelta(0):
                    tag = "ago"
                else:
                    tag = "from now"
                row[col] += " (%s %s)" % (humanize.naturaldelta(delta), tag)

        # info to print
        d = collections.OrderedDict()
        d['status'] = 'Status'
        d['service_name'] = 'Type'
        d['agency_responsible'] = 'Agency'
        d['address'] = 'Address'
        d['requested_datetime'] = 'Requested Date'
        d['expected_datetime'] = 'Expected Date'
        d['updated_datetime'] = 'Last Updated'
        d['service_notes'] = 'Notes'

        # make the response
        response = f"Hi, here's some info on case # {request_id}:\n\n"
        for col in d:
            if col in row:
                response += f"{d[col]}: {row[col]}\n"

        return response
