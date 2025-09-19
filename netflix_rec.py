import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import numpy as np
# First, add these imports at the top
from supabase_loader import NetflixDataLoader
import os
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="Netflix Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Replace the entire load_netflix_data function with this:
@st.cache_data
def load_netflix_data():
    try:
        # Load environment variables
        load_dotenv()
        
        
        
        # Initialize Supabase loader
        loader = NetflixDataLoader()
        
        # Load data from Supabase instead of CSV
        data = loader.load_netflix_data()
        
        if data is None or data.empty:
            st.error("Failed to load data from Supabase database!")
            st.stop()
        
        # Clean and prepare data (same as before)
        data['release_year'] = pd.to_numeric(data['release_year'], errors='coerce')
        data['listed_in'] = data['listed_in'].fillna('')
        data['director'] = data['director'].fillna('')
        data['country'] = data['country'].fillna('')
        
        return data
        
    except Exception as e:
        st.error(f"Error connecting to database: {str(e)}")
        st.error("Please check your Supabase configuration in the .env file.")
        st.stop()

netflix_data = load_netflix_data()

# Extract unique values for dropdowns
@st.cache_data
def get_dropdown_options():
    options = {}
    
    # Get unique genres
    all_genres = []
    for genres in netflix_data['listed_in'].dropna():
        if genres:  # Skip empty strings
            genre_list = [g.strip() for g in genres.split(',')]
            all_genres.extend(genre_list)
    
    unique_genres = sorted(list(set(all_genres)))
    options['genres'] = [''] + unique_genres  # Empty option first
    
    # Get unique directors
    all_directors = []
    for directors in netflix_data['director'].dropna():
        if directors:  # Skip empty strings
            director_list = [d.strip() for d in directors.split(',')]
            all_directors.extend(director_list)
    
    unique_directors = sorted(list(set(all_directors)))
    # Keep only directors with more than 1 movie to reduce clutter
    director_counts = Counter(all_directors)
    popular_directors = [d for d, count in director_counts.items() if count > 1]
    options['directors'] = [''] + sorted(popular_directors)
    
    # Get unique countries
    all_countries = []
    for countries in netflix_data['country'].dropna():
        if countries:  # Skip empty strings
            country_list = [c.strip() for c in countries.split(',')]
            all_countries.extend(country_list)
    
    unique_countries = sorted(list(set(all_countries)))
    # Keep only countries with more than 5 titles
    country_counts = Counter(all_countries)
    popular_countries = [c for c, count in country_counts.items() if count > 5]
    options['countries'] = [''] + sorted(popular_countries)
    
    return options

dropdown_options = get_dropdown_options()

# Enhanced recommendation function with min_year parameter
def get_smart_recommendations(genre=None, director=None, country=None, content_type="Both", count=10, min_year=1900):
    filtered = netflix_data.copy()
    
    # Apply filters
    if genre:
        filtered = filtered[filtered['listed_in'].str.contains(genre, case=False, na=False)]
    
    if director:
        filtered = filtered[filtered['director'].str.contains(director, case=False, na=False)]
    
    if country:
        filtered = filtered[filtered['country'].str.contains(country, case=False, na=False)]
    
    if content_type != "Both":
        filtered = filtered[filtered['type'] == content_type]
    
    # Filter by minimum year
    filtered = filtered[filtered['release_year'] >= min_year]
    
    # Create popularity score
    if not filtered.empty:
        filtered = filtered.copy()
        filtered['popularity_score'] = 0
        
        # Newer content bonus
        filtered.loc[filtered['release_year'] >= 2018, 'popularity_score'] += 3
        filtered.loc[filtered['release_year'] >= 2015, 'popularity_score'] += 2
        filtered.loc[filtered['release_year'] >= 2010, 'popularity_score'] += 1
        
        # Multiple genres bonus
        filtered['genre_count'] = filtered['listed_in'].str.count(',') + 1
        filtered['popularity_score'] += filtered['genre_count'] * 0.5
        
        # Sort by popularity and year
        return filtered.sort_values(['popularity_score', 'release_year'], ascending=[False, False]).head(count)
    
    return filtered

# Analysis functions
@st.cache_data
def analyze_netflix_data(data):
    analysis = {}
    
    # Basic stats
    analysis['total_titles'] = len(data)
    analysis['movies'] = len(data[data['type'] == 'Movie'])
    analysis['tv_shows'] = len(data[data['type'] == 'TV Show'])
    
    # Genre analysis
    all_genres = []
    for genres in data['listed_in'].dropna():
        genre_list = [g.strip() for g in genres.split(',')]
        all_genres.extend(genre_list)
    
    analysis['top_genres'] = Counter(all_genres).most_common(10)
    
    # Year analysis
    analysis['year_distribution'] = data['release_year'].value_counts().sort_index()
    
    # Country analysis
    all_countries = []
    for countries in data['country'].dropna():
        country_list = [c.strip() for c in countries.split(',')]
        all_countries.extend(country_list)
    
    analysis['top_countries'] = Counter(all_countries).most_common(10)
    
    return analysis

# Main app layout
def main():
    # Header
    st.title("🎬 Netflix Content Recommendation System")
    st.markdown("### Discover your next favorite movie or TV show from Netflix's catalog!")
    
    # Sidebar for analytics
    with st.sidebar:
        st.header("📊 Dataset Analytics")
        
        # Get analysis
        analysis = analyze_netflix_data(netflix_data)
        
        # Display metrics
        st.metric("Total Titles", f"{analysis['total_titles']:,}")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Movies", f"{analysis['movies']:,}")
        with col2:
            st.metric("TV Shows", f"{analysis['tv_shows']:,}")
        
        # Top genres
        st.subheader("🎭 Top Genres")
        for genre, count in analysis['top_genres'][:5]:
            st.write(f"• **{genre}**: {count}")
        
        # Top countries
        st.subheader("🌍 Top Countries")
        for country, count in analysis['top_countries'][:5]:
            st.write(f"• **{country}**: {count}")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["🔍 Get Recommendations", "📈 Data Insights", "ℹ️ About"])
    
    with tab1:
        recommendation_interface()
    
    with tab2:
        data_insights()
    
    with tab3:
        about_section()

def recommendation_interface():
    st.header("🎯 Find Your Perfect Watch")
    
    # Input section with dropdowns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Genre dropdown
        genre = st.selectbox(
            "🎭 Select Genre:", 
            options=dropdown_options['genres'],
            index=0,
            help="Choose from available genres in the dataset"
        )
        
        # Director dropdown
        director = st.selectbox(
            "🎬 Select Director:", 
            options=dropdown_options['directors'],
            index=0,
            help="Directors with multiple movies in the dataset"
        )
    
    with col2:
        # Country dropdown
        country = st.selectbox(
            "🌍 Select Country:", 
            options=dropdown_options['countries'],
            index=0,
            help="Countries with 5+ titles in the dataset"
        )
        
        # Content type dropdown
        content_type = st.selectbox("📺 Content Type:", ["Both", "Movie", "TV Show"])
    
    with col3:
        # Sliders
        num_recommendations = st.slider("📊 Number of recommendations:", min_value=5, max_value=20, value=10)
        min_year = st.slider("📅 Minimum release year:", 
                            min_value=int(netflix_data['release_year'].min()), 
                            max_value=int(netflix_data['release_year'].max()), 
                            value=2000)
    
    # Quick genre buttons (popular genres)
    st.subheader("🚀 Quick Select Popular Genres:")
    popular_genres = ["Comedies", "Dramas", "International Movies", "Action & Adventure", 
                     "Independent Movies", "Documentaries", "Children & Family Movies", "Horror Movies"]
    
    cols = st.columns(4)
    for i, quick_genre in enumerate(popular_genres[:8]):  # Show 8 most popular
        with cols[i % 4]:
            if st.button(quick_genre, key=f"quick_{quick_genre}"):
                # Trigger search with selected genre
                get_and_display_recommendations(quick_genre, director, country, content_type, num_recommendations, min_year)
                return
    
    # Get recommendations button
    if st.button("🔍 Get Smart Recommendations", type="primary", use_container_width=True):
        get_and_display_recommendations(genre, director, country, content_type, num_recommendations, min_year)
    
    # Show current selections
    if any([genre, director, country]) or content_type != "Both":
        st.subheader("🎯 Current Filters:")
        filter_info = []
        if genre: filter_info.append(f"**Genre:** {genre}")
        if director: filter_info.append(f"**Director:** {director}")
        if country: filter_info.append(f"**Country:** {country}")
        if content_type != "Both": filter_info.append(f"**Type:** {content_type}")
        filter_info.append(f"**Min Year:** {min_year}")
        filter_info.append(f"**Max Results:** {num_recommendations}")
        
        st.write(" | ".join(filter_info))

def get_and_display_recommendations(genre, director, country, content_type, num_recommendations, min_year):
    # Convert empty strings to None for the function
    genre_param = genre if genre else None
    director_param = director if director else None  
    country_param = country if country else None
    
    # Validate inputs
    if not any([genre_param, director_param, country_param]):
        st.warning("Please select at least one search criteria (genre, director, or country)!")
        return
    
    # Get recommendations
    with st.spinner("🔍 Finding perfect recommendations for you..."):
        recommendations = get_smart_recommendations(
            genre=genre_param, 
            director=director_param, 
            country=country_param, 
            content_type=content_type, 
            count=num_recommendations, 
            min_year=min_year
        )
    
    # Display results
    if recommendations.empty:
        st.error("😔 No recommendations found with your criteria!")
        
        # Show applied filters for debugging
        st.subheader("Applied Filters:")
        if genre: st.write(f"• **Genre:** {genre}")
        if director: st.write(f"• **Director:** {director}")
        if country: st.write(f"• **Country:** {country}")
        st.write(f"• **Content Type:** {content_type}")
        st.write(f"• **Min Year:** {min_year}")
        
        st.write("**Try:**")
        st.write("• Different genre/director/country combination")
        st.write("• Lower minimum release year")
        st.write("• Change content type to 'Both'")
        return
    
    # Show filter summary
    applied_filters = []
    if genre: applied_filters.append(f"genre '{genre}'")
    if director: applied_filters.append(f"director '{director}'")
    if country: applied_filters.append(f"country '{country}'")
    
    filter_text = ", ".join(applied_filters) if applied_filters else "your criteria"
    st.success(f"🎉 Found {len(recommendations)} recommendations for {filter_text}!")
    
    # Display recommendations in a nice format
    for idx, (_, movie) in enumerate(recommendations.iterrows(), 1):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {idx}. {movie['title']}")
                
                # Movie details
                details = []
                details.append(f"**{movie['type']}** ({movie['release_year']})")
                
                if pd.notna(movie['director']) and movie['director']:
                    details.append(f"🎬 {movie['director']}")
                
                if pd.notna(movie['country']) and movie['country']:
                    details.append(f"🌍 {movie['country']}")
                
                if pd.notna(movie['rating']) and movie['rating']:
                    details.append(f"📺 Rated: {movie['rating']}")
                
                st.write(" | ".join(details))
                st.write(f"**Genres:** {movie['listed_in']}")
                
                # Description if available
                if 'description' in netflix_data.columns and pd.notna(movie.get('description')) and movie.get('description'):
                    with st.expander("📖 Read description"):
                        st.write(movie['description'])
            
            with col2:
                # Popularity score if we calculated it
                if 'popularity_score' in movie:
                    st.metric("⭐ Popularity", f"{movie['popularity_score']:.1f}")
                
                # Year check
                if movie['release_year'] >= min_year:
                    st.success(f"✅ {movie['release_year']} ≥ {min_year}")
                else:
                    st.error(f"❌ {movie['release_year']} < {min_year}")
            
            st.divider()

def data_insights():
    st.header("📈 Netflix Catalog Insights")
    
    analysis = analyze_netflix_data(netflix_data)
    
    # Content type distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📺 Content Type Distribution")
        type_data = netflix_data['type'].value_counts()
        fig_pie = px.pie(values=type_data.values, names=type_data.index, 
                        title="Movies vs TV Shows",
                        color_discrete_sequence=['#E50914', '#B20710'])
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("🎭 Top 10 Genres")
        genres, counts = zip(*analysis['top_genres'])
        fig_bar = px.bar(x=list(counts), y=list(genres), orientation='h',
                        title="Most Popular Genres",
                        color=list(counts),
                        color_continuous_scale='Reds')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Release year trend
    st.subheader("📅 Content Release Timeline")
    yearly_data = analysis['year_distribution']
    fig_line = px.line(x=yearly_data.index, y=yearly_data.values,
                      title="Content Added by Release Year",
                      labels={'x': 'Release Year', 'y': 'Number of Titles'})
    fig_line.update_traces(line_color='#E50914')
    st.plotly_chart(fig_line, use_container_width=True)

def about_section():
    st.header("ℹ️ About This Project")
    
    st.markdown("""
    ## 🎯 Project Overview
    
    This **Netflix Content Recommendation System** uses content-based filtering to suggest movies and TV shows based on user preferences.
    
    ### 🚀 Key Features:
    - **Dropdown Menus**: Easy selection from actual data values
    - **Smart Filtering**: Multiple criteria with popularity scoring
    - **Interactive Analytics**: Data insights and visualizations
    - **Year Filtering**: Find content from specific time periods
    
    ### 🛠 Technical Implementation:
    - **Data Processing**: Pandas for data manipulation
    - **Visualization**: Plotly for interactive charts
    - **Web Framework**: Streamlit for user interface
    - **Recommendation Logic**: Content-based filtering with popularity weighting
    
    ### 📊 Dataset Statistics:
    - **Total Titles**: {total_titles:,}
    - **Movies**: {movies:,}
    - **TV Shows**: {tv_shows:,}
    - **Genres Available**: {genre_count}
    - **Directors with Multiple Works**: {director_count}
    - **Countries Represented**: {country_count}
    """.format(
        total_titles=len(netflix_data),
        movies=len(netflix_data[netflix_data['type'] == 'Movie']),
        tv_shows=len(netflix_data[netflix_data['type'] == 'TV Show']),
        genre_count=len(dropdown_options['genres']) - 1,  # Subtract 1 for empty option
        director_count=len(dropdown_options['directors']) - 1,
        country_count=len(dropdown_options['countries']) - 1
    ))

# Debug section


if __name__ == "__main__":
    main()