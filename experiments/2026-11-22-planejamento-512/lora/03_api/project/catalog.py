def list_items(items, page, page_size):
    # Validate page and page_size
    if page < 1 or page_size < 1:
        raise ValueError('Page and page size must be at least 1')
    
    # Calculate the start index based on the current page
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    # Return the appropriate slice of items
    return items[start_index:end_index]
