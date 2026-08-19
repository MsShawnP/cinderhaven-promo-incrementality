import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		// Fully static: every route is prerendered (see src/routes/+layout.js).
		// No fallback — this tool has no client-side routing to unknown paths,
		// and a fallback would mask a route that failed to prerender.
		adapter: adapter()
	}
};

export default config;
