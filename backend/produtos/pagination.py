from rest_framework.pagination import PageNumberPagination


class ProdutoPagination(PageNumberPagination):
    # page_size_query_param opt-in only on ProdutoViewSet (not set globally
    # on DEFAULT_PAGINATION_CLASS in settings) — the Catálogo is the only
    # place with a page-size selector; every other paginated list (pedidos,
    # enderecos, ...) keeps the fixed PAGE_SIZE=10 default.
    page_size_query_param = "page_size"
    # max_page_size caps ?page_size= regardless of what a client sends —
    # without it, ?page_size=10000 would return the entire catalog in one
    # response.
    max_page_size = 50
