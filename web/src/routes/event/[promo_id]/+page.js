// Deep-linkable per-event anatomy. Option B (DECISIONS 2026-08-27): only the ~150
// events in the prerender manifest are baked to HTML; any other event renders
// client-side from the adapter-static fallback. Either way, load() fetches only this
// event's slice, so the ~5,900-event artifact never ships whole to the browser.
import { error } from '@sveltejs/kit';

import manifest from '$lib/data/anatomy-manifest.json';

export const prerender = true;

export function entries() {
	return manifest.prerender.map((promo_id) => ({ promo_id }));
}

export async function load({ params, fetch }) {
	const res = await fetch(`/anatomy/${params.promo_id}.json`);
	if (!res.ok) throw error(404, `Unknown event ${params.promo_id}`);
	const { event } = await res.json();
	return { event };
}
