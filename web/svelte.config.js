import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		// Static, but Option B (DECISIONS 2026-08-27) prerenders only ~150 event pages
		// (the manifest set), not all ~5,900. Fallback is 404.html, NOT a /event/*
		// _redirects rewrite: on Cloudflare Pages that catch-all shadowed the prerendered
		// event files (a direct hit on a story page 308'd to /200 instead of serving its
		// own HTML — Max's audit). With the plain fallback, every prerendered event serves
		// its real HTML + meta; a non-prerendered event gets the SPA shell (a 404 that the
		// client router renders from the event's fetched slice). crawl is off so Scorecard
		// links to non-manifest events don't drag the whole universe into the prerender.
		adapter: adapter({ fallback: '404.html' }),
		prerender: { crawl: false }
	}
};

export default config;
