// Photo gallery for the restaurant detail page. `gallery_photos` already
// arrives pre-truncated by the backend to the location's tier limit
// (`backend/app/services/photo_service.py`'s `gallery_limit_for` — 2 free /
// 10 paid, docs/DECISIONS.md "Photo gallery: 2 photos free, 10 photos
// paid per location") — this component just renders whatever it's given,
// it does not re-implement that gate.
import { ImageIcon } from "@/components/ui/icons";
import type { GalleryPhoto } from "@/types/location";

export default function RestaurantGallery({ photos }: { photos: GalleryPhoto[] }) {
  if (photos.length === 0) return null;

  const sorted = [...photos].sort((a, b) => a.display_order - b.display_order);

  return (
    <section aria-labelledby="gallery-heading">
      <h2 id="gallery-heading" className="flex items-center gap-2 font-display text-xl font-bold text-brand-ink">
        <ImageIcon className="h-5 w-5 text-brand-ink-subtle" />
        Photos
      </h2>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {sorted.map((photo) => (
          // eslint-disable-next-line @next/next/no-img-element -- remote
          // CloudFront URLs; no next/image domain config exists yet for
          // this host, and adding one is outside this task's scope.
          <img
            key={photo.id}
            src={photo.url}
            alt="Restaurant photo"
            className="h-32 w-full rounded-brand-control border border-brand-border object-cover sm:h-40"
          />
        ))}
      </div>
    </section>
  );
}
