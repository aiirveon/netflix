import os
from supabase import create_client, Client
import pandas as pd
from dotenv import load_dotenv

class NetflixDataLoader:
    def __init__(self):
        """Initialize Supabase connection using environment variables"""
        # Load environment variables from .env file
        load_dotenv()
        
        # Get Supabase credentials from environment
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.table_name = os.getenv("TABLE_NAME", "netflix_titles")
        
        # Validate that we have the required credentials
        if not self.url or not self.key:
            raise ValueError("Missing Supabase credentials. Please check your .env file.")
        
        # Initialize Supabase client
        try:
            self.supabase: Client = create_client(self.url, self.key)
            print(f"Connected to Supabase successfully!")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {str(e)}")
    
    def load_netflix_data(self):
        """Load all Netflix titles from Supabase database"""
        try:
            # Query all data from your Netflix table
            response = self.supabase.table(self.table_name).select("*").execute()
            
            # Check if we got data
            if not response.data:
                print("Warning: No data returned from database")
                return pd.DataFrame()
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(response.data)
            
            print(f"Successfully loaded {len(df)} Netflix titles from Supabase!")
            return df
            
        except Exception as e:
            print(f"Error loading Netflix data: {str(e)}")
            return None
    
    def search_by_genre(self, genre):
        """Search movies by genre directly in the database"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .ilike("listed_in", f"%{genre}%")\
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                print(f"Found {len(df)} titles in genre: {genre}")
                return df
            else:
                print(f"No titles found for genre: {genre}")
                return pd.DataFrame()
            
        except Exception as e:
            print(f"Error searching by genre: {str(e)}")
            return None
    
    def search_by_director(self, director):
        """Search movies by director"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .ilike("director", f"%{director}%")\
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                print(f"Found {len(df)} titles by director: {director}")
                return df
            else:
                print(f"No titles found for director: {director}")
                return pd.DataFrame()
            
        except Exception as e:
            print(f"Error searching by director: {str(e)}")
            return None
    
    def get_movies_by_year_range(self, start_year, end_year):
        """Get movies from specific year range"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .gte("release_year", start_year)\
                .lte("release_year", end_year)\
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                print(f"Found {len(df)} titles from {start_year}-{end_year}")
                return df
            else:
                print(f"No titles found for years {start_year}-{end_year}")
                return pd.DataFrame()
            
        except Exception as e:
            print(f"Error filtering by year range: {str(e)}")
            return None
    
    def get_content_by_type(self, content_type):
        """Get content by type (Movie or TV Show)"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("type", content_type)\
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                print(f"Found {len(df)} {content_type}s")
                return df
            else:
                print(f"No {content_type}s found")
                return pd.DataFrame()
            
        except Exception as e:
            print(f"Error filtering by content type: {str(e)}")
            return None
    
    def test_connection(self):
        """Test the Supabase connection and table access"""
        try:
            # Try to get just one record to test connection
            response = self.supabase.table(self.table_name).select("*").limit(1).execute()
            
            if response.data:
                print("✅ Supabase connection test successful!")
                print(f"✅ Table '{self.table_name}' is accessible")
                sample_record = response.data[0]
                print(f"✅ Sample record columns: {list(sample_record.keys())}")
                return True
            else:
                print("❌ Connection successful but no data found")
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed: {str(e)}")
            return False

# Example usage and testing
if __name__ == "__main__":
    try:
        # Test the loader
        print("Testing Netflix Data Loader...")
        loader = NetflixDataLoader()
        
        # Test connection
        if loader.test_connection():
            
            # Load all data
            data = loader.load_netflix_data()
            
            if data is not None and not data.empty:
                print(f"\n📊 Dataset Info:")
                print(f"Total records: {len(data)}")
                print(f"Columns: {list(data.columns)}")
                
                # Show sample data
                print(f"\n📋 Sample records:")
                sample_cols = ['title', 'type', 'release_year', 'listed_in']
                available_cols = [col for col in sample_cols if col in data.columns]
                print(data[available_cols].head())
                
                # Test genre search
                print(f"\n🎭 Testing genre search (Action):")
                action_movies = loader.search_by_genre("Action")
                if action_movies is not None and not action_movies.empty:
                    print(f"Found {len(action_movies)} action titles")
                
            else:
                print("❌ Failed to load data or data is empty")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        print("\nPlease check:")
        print("1. Your .env file exists and has correct Supabase credentials")
        print("2. Your Supabase table name is correct")
        print("3. Your Supabase API key has proper permissions")