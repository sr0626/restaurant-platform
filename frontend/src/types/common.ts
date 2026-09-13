// Shared response envelope types used across the typed API client.
// Mirrors the `{ results, page, page_size, total }` shape used by every
// paginated endpoint in docs/API_CONTRACTS.md (GET /search,
// GET /restaurants/{id}/locations, etc).

export interface PaginatedResponse<TResult> {
  results: TResult[];
  page: number;
  page_size: number;
  total: number;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}
