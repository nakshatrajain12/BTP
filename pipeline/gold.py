import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import supabase

def refresh_gold_views():
    try:
        # Note: Supabase's python client doesn't natively expose a .rpc() or direct method to run arbitrary raw SQL
        # unless it is registered as a database function. Since we are using standard Postgres Materialized Views,
        # we can execute a remote RPC call if defined, or we can use the python-dotenv + psycopg2 to connect directly.
        # As a fallback, since Streamlit will fetch via the analytical fallback if the views are empty, we 
        # highly recommend creating a postgres function in Supabase SQL editor:
        # CREATE OR REPLACE FUNCTION refresh_gold() RETURNS void AS $$ 
        # BEGIN 
        #   REFRESH MATERIALIZED VIEW funding_by_ministry; 
        #   REFRESH MATERIALIZED VIEW sector_distribution; 
        #   REFRESH MATERIALIZED VIEW stage_coverage; 
        # END; 
        # $$ LANGUAGE plpgsql;
        #
        # Then calling: supabase.rpc("refresh_gold").execute()
        
        print("To refresh gold views, please run the following in Supabase SQL Editor:")
        print("REFRESH MATERIALIZED VIEW funding_by_ministry;")
        print("REFRESH MATERIALIZED VIEW sector_distribution;")
        print("REFRESH MATERIALIZED VIEW stage_coverage;")
    except Exception as e:
        print(f"Error during gold refresh: {e}")

if __name__ == "__main__":
    refresh_gold_views()
