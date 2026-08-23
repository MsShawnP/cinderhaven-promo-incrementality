// Deep-linkable per-event anatomy. Prerendered for all 131 events via entries();
// the anatomy artifact is read at build time and sliced to this event.
import { error } from '@sveltejs/kit';

import anatomy from '$lib/data/anatomy.json';

export const prerender = true;

export function entries() {
	return anatomy.events.map((e) => ({ promo_id: e.promo_id }));
}

export function load({ params }) {
	const event = anatomy.events.find((e) => e.promo_id === params.promo_id);
	if (!event) throw error(404, `Unknown event ${params.promo_id}`);
	return { event };
}
