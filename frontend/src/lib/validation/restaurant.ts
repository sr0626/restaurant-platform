// Client-side validation mirroring POST/PATCH /restaurants body shapes
// (docs/API_CONTRACTS.md "Restaurants").
import { z } from "zod";

export const createRestaurantSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(200),
  description: z.string().trim().min(1, "Description is required").max(2000),
  cuisine_tag_ids: z.array(z.number().int().positive()).min(1, "Pick at least one cuisine tag"),
});

export type CreateRestaurantFormValues = z.infer<typeof createRestaurantSchema>;

export const updateRestaurantSchema = createRestaurantSchema.partial();

export type UpdateRestaurantFormValues = z.infer<typeof updateRestaurantSchema>;
