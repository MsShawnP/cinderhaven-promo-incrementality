import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		// Static, but Option B (DECISIONS 2026-08-27) prerenders only ~150 event pages
		// (the manifest set), not all ~5,900. The SPA fallback (200.html) renders any
		// other event page client-side from its fetched slice; crawl is off so links to
		// non-manifest events on the Scorecard don't drag the whole universe back into
		// the prerender. Direct hits are routed to the fallback by static/_redirects.
		adapter: adapter({ fallback: '200.html' }),
		prerender: { crawl: false }
	}
};

export default config;
