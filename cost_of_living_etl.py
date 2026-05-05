from dagster import job
from extract import *
from transform_and_load import *
from visualisation import *

@job
def etl():
    # Visualise data from PostgreSQL 
    visualise(
        # Load the joined data into PostgreSQL
        load(
            # Join all three data
            join(
                # Transform the stored flights data
                transform_unemployment(
                    # Extract and store the flights data
                    extract_unemployment()
                ),
                # Transform the stored weather data
                transform_cost_of_living(
                    # Extract and store the weather data
                    extract_cost_of_living()
                ),
                transform_quality_of_life(
                    # Extract and store the weather data
                    extract_quality_of_life()
                )
            )
        )
    )