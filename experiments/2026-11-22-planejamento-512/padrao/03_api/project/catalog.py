def list_items(items, page, page_size):
    if page < 1 or page_size < 1:
        raise ValueError('Page and page size must be greater than or equal to 1')
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    return items[start_index:end_index]
