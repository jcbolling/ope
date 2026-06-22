import requests
import datetime
import os
import time
import sys
from tabulate import tabulate

# 1. Configuration Constants
# Public endpoint (No API key required for basic keyword searches)
ENDPOINT = 'https://www.googleapis.com/books/v1/volumes'
API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY')

def search_google_books_paginated(query, total_limit=25):
    """
    Queries Google Books API, automatically paginating using startIndex 
    until the total_limit is reached or all results are found.
    """
    all_results = []
    current_index = 0
    
    # Google Books API allows a maximum of 40 items per single request
    page_size = min(total_limit, 40) 
    
    # Get current date and time for logging purposes
    current_datetime = datetime.datetime.now()

    print(f"[{current_datetime}]: Fetching up to {total_limit} results for '{query}' from Google Books...")
    
    while len(all_results) < total_limit:
        remaining_needed = total_limit - len(all_results)
        
        params = {
            'q': query,
            'maxResults': min(page_size, remaining_needed),
            'startIndex': current_index,
            'key': API_KEY
        }
        
        try:
            response = requests.get(ENDPOINT, params=params)
            if response.status_code != 200:
                print(f"\nError {response.status_code}: {response.text}")
                break
                
            data = response.json()
            page_results = data.get('items', []) # Google Books uses 'items' instead of 'results'
            
            if not page_results:
                break
                
            all_results.extend(page_results)
            
            # Stop if we've reached the total items available on Google's servers
            total_items_available = data.get('totalItems', 0)
            if len(all_results) >= total_items_available:
                break
                
            # Advance the index by the number of items we just fetched
            current_index += len(page_results)
            time.sleep(0.5)  # Rate limit safety buffer
            
        except requests.exceptions.RequestException as e:
            print(f"\nHTTP Request failed: {e}")
            break
            
    return all_results[:total_limit]


def display_results_table(results):
    """
    Processes raw Google Books API results and prints them in a clean ASCII table.
    """
    if not results:
        print("\nNo results found to display.")
        return

    table_data = []
    for index, item in enumerate(results, start=1):
        # Google Books nests metadata inside a 'volumeInfo' dictionary
        volume_info = item.get('volumeInfo', {})
        
        title = volume_info.get('title', 'N/A')
        
        # Authors come as a list, so we join them into a clean string
        authors_list = volume_info.get('authors', ['N/A'])
        authors = ", ".join(authors_list)
        
        pub_date = volume_info.get('publishedDate', 'N/A')
        
        # Get the URL to the Google Books website page (as if searched on books.google.com)
        book_id = item.get('id', 'N/A')
        book_url = f'https://books.google.com/books?id={book_id}' if book_id != 'N/A' else 'N/A'
        
        # Truncate title text if it is too long for a terminal window
        display_title = title[:50] + "..." if len(title) > 50 else title

        table_data.append([index, display_title, authors, pub_date, book_url])

    headers = ["#", "Book Title", "Author(s)", "Publication Date", "URL"]
    
    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid") + "\n")


# 3. Main Execution Flow
if __name__ == "__main__":
    # Accept search term from CLI
    search_term = sys.argv[1] if len(sys.argv) > 1 else print("ERROR: Please provide a search term as a command-line argument.") or sys.exit(1) # Print function outputs None so or is triggered and sys.exit(1) is called
    user_limit_override = int(sys.argv[2]) if len(sys.argv) > 2 else None  # Change this to an integer (e.g., 50) to override
    
    final_limit = user_limit_override if user_limit_override is not None else 25
    
    # Step 1: Fetch the data from Google Books
    results = search_google_books_paginated(search_term, total_limit=final_limit)
    
    # Step 2: Display the data
    display_results_table(results)
