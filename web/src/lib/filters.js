// Cross-view filters, carried in the URL so they persist across the Scorecard and
// the event pages. Four observed dimensions: retailer, product line, promo type,
// plan status. Filtering narrows which events a list shows — it never recomputes a
// portfolio figure (those come from the pipeline; DECISIONS.md).

export const FILTER_KEYS = ['retailer', 'line', 'type', 'status'];

const FIELD = {
	retailer: (e) => e.retailer_id,
	line: (e) => e.sku.split('-')[1],
	type: (e) => e.promo_type,
	status: (e) => e.plan_status
};

/** Read the four filters from a URLSearchParams; missing → '' (no constraint). */
export function parseFilters(searchParams) {
	const f = {};
	for (const key of FILTER_KEYS) f[key] = searchParams.get(key) ?? '';
	return f;
}

/** Does one event pass every active filter? */
export function matches(event, filters) {
	return FILTER_KEYS.every((key) => !filters[key] || FIELD[key](event) === filters[key]);
}

/** Are any filters active? */
export function anyActive(filters) {
	return FILTER_KEYS.some((key) => filters[key]);
}

/** The distinct, sorted option values for each dimension, from the event set. */
export function optionsFor(events) {
	const opts = {};
	for (const key of FILTER_KEYS) {
		opts[key] = [...new Set(events.map((e) => FIELD[key](e)))].sort();
	}
	return opts;
}

/** A query string ('?a=b&c=d' or '') for the active filters — for links. */
export function toQuery(filters) {
	const params = new URLSearchParams();
	for (const key of FILTER_KEYS) if (filters[key]) params.set(key, filters[key]);
	const s = params.toString();
	return s ? `?${s}` : '';
}
