import os
import logging
from retry import retry
import arcgis
from datetime import datetime

class CamsConnection:

    @retry(delay=5, tries=3)
    def __init__(self):
        print(f"Connecting to {os.environ['ARCGIS_URL']}")
        self.gis = arcgis.GIS(url=os.environ['ARCGIS_URL'],
                              username=os.environ['ARCGIS_USERNAME'],
                              password=os.environ['ARCGIS_PASSWORD'])
        print("Connecting to layer")
        self.item = self.gis.content.get(os.environ['ARCGIS_FEATURE_LAYER_ID'])
        print("Connected")

        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', force=True)
        logging.info(f"Successfully logged in to {self.item.type} '{self.item.title}' as '{self.gis.properties.user.username}'")

        self.layer = self.item.layers[0]
        self.table = self.item.tables[0]

    def find_features_with_redgrowth_to_purplehistoric(self):
        logging.info("Querying layer and table data...")

        # Query all features in the layer
        layer_features = self.layer.query(where="SpeciesDropDown = 'OldMansBeard'", out_fields="OBJECTID, GlobalID, StatusAt202310, StatusAt202410, SiteSource, SpeciesDropDown", return_geometry=False).features
        logging.info(f"Retrieved {len(layer_features)} features from the layer.")

        # Query all rows in the table
        table_rows = self.table.query(where="1=1", out_fields="GUID_visits, OBJECTID, WeedVisitStatus, DateCheck, CreationDate_1, VisitDataSource", order_by_fields="GUID_visits ASC, OBJECTID ASC").features
        logging.info(f"Retrieved {len(table_rows)} rows from the table.")

        # Group table rows by GUID_visits
        table_rows_by_guid = {}
        for row in table_rows:
            guid = row.attributes["GUID_visits"]
            if guid not in table_rows_by_guid:
                table_rows_by_guid[guid] = []

            # Determine visit date
            date_check = row.attributes["DateCheck"]
            creation_date = row.attributes["CreationDate_1"]
            visit_date = datetime.fromtimestamp(date_check / 1000) if date_check else datetime.fromtimestamp(creation_date / 1000)

            # Append with visit date
            row.attributes["VisitDate"] = visit_date
            table_rows_by_guid[guid].append(row)

        results = []
        html_report = "<html><head><title>Weed Report</title></head><body><h1>Weed Report</h1>"

        sorted_features = []

        for feature in layer_features:
            global_id = feature.attributes["GlobalID"]
            object_id = feature.attributes["OBJECTID"]
            species = feature.attributes.get("SpeciesDropDown", "Unknown Species")

            # Add synthetic visits for StatusAt202310 and StatusAt202410
            for status_field, date in [("StatusAt202310", datetime(2023, 9, 30)), ("StatusAt202410", datetime(2024, 9, 30))]:
                status_value = feature.attributes.get(status_field)
                if status_value:
                    synthetic_row = {
                        "WeedVisitStatus": status_value,
                        "VisitDate": date,
                        "Source": status_field,
                        "DataSource": feature.attributes.get("SiteSource", "Unknown")
                    }
                    if global_id not in table_rows_by_guid:
                        table_rows_by_guid[global_id] = []
                    table_rows_by_guid[global_id].append(arcgis.features.Feature(attributes=synthetic_row))

            # Get related table rows
            related_rows = table_rows_by_guid.get(global_id, [])

            if not related_rows:
                continue

            # Combine feature rows and table rows
            related_rows = [row for row in related_rows if row.attributes["WeedVisitStatus"] is not None]

            # Exclude features if any row's DataSource (from SiteSource or VisitDataSource) is not iNaturalist_v1
            if not any(data_source == "iNaturalist_v1"
                       for row in related_rows
                       for data_source in [row.attributes.get("DataSource"), row.attributes.get("VisitDataSource")]):
                continue

            # Ensure all related_rows statuses are either Red or Purple
            if not all(row.attributes["WeedVisitStatus"].startswith("Red") or row.attributes["WeedVisitStatus"].startswith("Purple") for row in related_rows):
                continue

            # Sort related rows by VisitDate in ascending order
            related_rows.sort(key=lambda x: x.attributes["VisitDate"])

            # Check for the exact sequence Purple -> Red -> Purple with exactly three rows
            if len(related_rows) != 3:
                continue

            if (related_rows[0].attributes["WeedVisitStatus"].startswith("Purple") and
                related_rows[1].attributes["WeedVisitStatus"].startswith("Red") and
                related_rows[2].attributes["WeedVisitStatus"].startswith("Purple")):

                # Determine date first visited (earliest date_check or creation_date)
                date_first_visited = min((row.attributes.get("DateCheck") or row.attributes.get("CreationDate_1")) / 1000 for row in related_rows if row.attributes.get("DateCheck") or row.attributes.get("CreationDate_1"))
                date_first_visited = datetime.fromtimestamp(date_first_visited).strftime("%Y-%m-%d")

                # Add to sorted features for ordering later
                sorted_features.append((date_first_visited, feature, related_rows))

        # Sort features by Date First Visited in ascending order
        sorted_features.sort(key=lambda x: x[0])

        for date_first_visited, feature, related_rows in sorted_features:
            object_id = feature.attributes["OBJECTID"]
            species = feature.attributes.get("SpeciesDropDown", "Unknown Species")

            # Add to HTML report
            html_report += f"<h2>{species}: <a href='https://cams.econet.nz/weed/{object_id}'>Weed ID: {object_id}</a></h2>"
            html_report += f"<p>Date First Visited: {date_first_visited}</p>"
            html_report += "<table border='1'><tr><th>Visit Date</th><th>Status</th><th>Source</th><th>DataSource</th></tr>"

            # Add related rows in descending date order to HTML table
            for row in sorted(related_rows, key=lambda x: x.attributes["VisitDate"], reverse=True):
                visit_date = row.attributes["VisitDate"].strftime("%Y-%m-%d")
                status = row.attributes["WeedVisitStatus"]
                source = row.attributes.get("Source", f"Visit Row {row.attributes.get('OBJECTID', 'N/A')}")
                data_source = row.attributes.get("DataSource", row.attributes.get("VisitDataSource", "Unknown"))
                html_report += f"<tr><td>{visit_date}</td><td>{status}</td><td>{source}</td><td>{data_source}</td></tr>"

            html_report += "</table>"

        html_report += "</body></html>"
        logging.info(f"Found {len(sorted_features)} features with the specified conditions.")
        with open("weed_report.html", "w") as report_file:
            report_file.write(html_report)
        logging.info("HTML report generated as weed_report.html")
        return [f"https://cams.econet.nz/weed/{feature.attributes['OBJECTID']}" for _, feature, _ in sorted_features]

if __name__ == "__main__":
    try:
        connection = CamsConnection()
        matching_features = connection.find_features_with_redgrowth_to_purplehistoric()

        print("Matching Features:")
        for feature_url in matching_features:
            print(feature_url)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
