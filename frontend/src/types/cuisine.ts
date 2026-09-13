// docs/DATA_MODEL.md "cuisine_tag": category is one of these five values.
// Seeded from docs/TAXONOMY.md — no public write API, admin panel only.
export type CuisineCategory =
  | "regional"
  | "dietary"
  | "type"
  | "signature"
  | "dining_time";

export interface CuisineTag {
  name: string;
  display_name: string;
  category: CuisineCategory;
}
