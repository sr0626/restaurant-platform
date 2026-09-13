// Weekly hours list for the restaurant detail page, rendered from
// `LocationDetail.hours` (docs/API_CONTRACTS.md "GET /locations/{id}" —
// all 7 `restaurant_hours` rows, day_of_week 0=Monday..6=Sunday). A day
// missing from the array is treated the same as `is_closed: null`
// ("hours unknown", never guessed) per that same contract note.
import { ClockIcon } from "@/components/ui/icons";
import type { LocationHour } from "@/types/location";

const DAY_NAMES = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

/** "14:00:00" -> "2:00 PM" — hours come back as `time` strings, not Dates. */
function formatTime(time: string): string {
  const [hourStr, minuteStr] = time.split(":");
  const hour = parseInt(hourStr ?? "0", 10);
  const minute = minuteStr ?? "00";
  const period = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 === 0 ? 12 : hour % 12;
  return `${displayHour}:${minute} ${period}`;
}

function describeDay(hour: LocationHour | undefined): string {
  if (!hour || hour.is_closed === null) return "Hours unknown";
  if (hour.is_closed) return "Closed";
  if (hour.open_time && hour.close_time) {
    return `${formatTime(hour.open_time)} – ${formatTime(hour.close_time)}`;
  }
  return "Hours unknown";
}

export default function RestaurantHours({ hours }: { hours: LocationHour[] }) {
  return (
    <section aria-labelledby="hours-heading">
      <h2 id="hours-heading" className="flex items-center gap-2 font-display text-xl font-bold text-brand-ink">
        <ClockIcon className="h-5 w-5 text-brand-ink-subtle" />
        Hours
      </h2>

      <ul className="mt-4 divide-y divide-brand-border rounded-brand-card border border-brand-border bg-white">
        {DAY_NAMES.map((day, index) => {
          const hour = hours.find((h) => h.day_of_week === index);
          return (
            <li key={day} className="flex items-center justify-between px-4 py-3 text-sm">
              <span className="font-medium text-brand-ink">{day}</span>
              <span className="text-brand-ink-muted">{describeDay(hour)}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
