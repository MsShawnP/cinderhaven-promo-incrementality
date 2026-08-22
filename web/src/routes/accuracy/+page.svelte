<script>
	// The accuracy view — the proof behind the Scorecard's numbers, one click deep.
	// Estimate vs truth, scored against quarantined ground truth. Method 0 sits beside
	// Method 1 in every figure; large error is displayed, not softened. Copy carries
	// the pre-registered claim language verbatim (docs/accuracy-spec.md §8).
	//
	// Imported at build time; written by src/incrementality/accuracy.py, which is the
	// one module that reads truth and publishes error metrics only — never truth.
	import accuracy from '$lib/data/accuracy.json';

	const { methods, stories } = accuracy;
	const m0 = methods.method0.headline;
	const m1 = methods.method1.headline;

	const pct = (x) => (x === null || x === undefined ? '—' : `${x}%`);
	const signed = (x) => (x === null || x === undefined ? '—' : `${x > 0 ? '+' : ''}${x}%`);

	const STORY_LABELS = {
		pure_subsidy: 'Pure subsidy',
		hero_cannibal: 'Hero cannibal',
		pantry_trap: 'Pantry trap',
		clean_winner: 'Clean winner'
	};

	const REGIME_NAMES = {
		retailer: 'Retailer',
		promo_type: 'Promotion type',
		product_line: 'Product line',
		depth_band: 'Discount depth',
		duration_band: 'Duration',
		season: 'Season'
	};

	// Merge a shared regime feature's buckets across both methods, aligned by label.
	function sharedRegime(feature) {
		const b0 = Object.fromEntries(methods.method0.regimes[feature].map((b) => [b.label, b]));
		const b1 = Object.fromEntries(methods.method1.regimes[feature].map((b) => [b.label, b]));
		const labels = [...new Set([...Object.keys(b0), ...Object.keys(b1)])].sort();
		return labels.map((label) => ({ label, m0: b0[label], m1: b1[label] }));
	}
	const relaxRegime = methods.method1.regimes.match_relaxed_share ?? [];
</script>

<div class="lailara-container accuracy">
	<p class="eyebrow">Accuracy · estimate vs truth</p>
	<a class="back" href="/">← Back to the Scorecard</a>

	<h1 class="title">How wrong are these numbers?</h1>

	<p class="framing ll-measure">
		Every incrementality tool asserts accuracy. This one measures it. The two baselines
		are scored against <strong>known ground truth</strong> — the error is shown, by
		regime, including where it is large. That is the whole claim, and it is a narrow one:
		<em>this is the error a standard method makes under a realistic, fully-known world.</em>
		It is not a prediction of the error on your data.
	</p>

	<p class="framing ll-measure">
		The estimators are <strong>provably blind</strong> — enforced in code, not promised.
		An AST gate runs over every estimation file on every push; the generator's own
		coefficients are banned from the estimation path; and the git history shows both
		methods frozen and tagged <em>before</em> this page's code first read truth. The
		blindness claim is scoped exactly there — to the code — and nowhere wider.
	</p>

	<!-- Headline: both methods side by side. Method 0 is never shown alone. -->
	<section class="headline">
		<h2 class="section-title">Median error, full population</h2>
		<div class="cards">
			<div class="method-card">
				<p class="method-name">Method 0 · pre-period</p>
				<p class="big">{pct(m0.median_abs_pct_error)}</p>
				<p class="big-note">median absolute error on incremental units</p>
				<p class="bias">Bias {signed(m0.median_signed_pct_error)} · {m0.n_scored} events scored</p>
			</div>
			<div class="method-card">
				<p class="method-name">Method 1 · comparable-store</p>
				<p class="big">{pct(m1.median_abs_pct_error)}</p>
				<p class="big-note">median absolute error on incremental units</p>
				<p class="bias">Bias {signed(m1.median_signed_pct_error)} · {m1.n_scored} events scored</p>
			</div>
		</div>
		<p class="read ll-measure">
			Both methods over-credit promotions — the sign of the bias is positive for each.
			The comparable-store method, the more defensible one, is <strong>more</strong>
			biased, not less: the better baseline does not flatter the promo book, it indicts
			it further. A demonstration engineered to make the naive method lose would not show
			this. Large error is the finding, not a blemish to sand off.
		</p>
	</section>

	<!-- The four seeded stories, marked and separate — never folded into the headline. -->
	<section class="stories">
		<h2 class="section-title">The four seeded stories, scored separately</h2>
		<p class="section-sub ll-measure">
			These four events are planted outliers the tool is supposed to surface. They are
			reported here, apart from the headline median above — the honest denominator is the
			full population, not the outliers.
		</p>
		<div class="lailara-table-wrap">
			<table class="acc-table">
				<thead>
					<tr>
						<th scope="col">Story</th>
						<th class="col-num" scope="col">Method 0 error</th>
						<th class="col-num" scope="col">Method 1 error</th>
					</tr>
				</thead>
				<tbody>
					{#each stories as s (s.promo_id)}
						<tr>
							<td><span class="badge badge-story">{STORY_LABELS[s.story_tag]}</span> {s.promo_id}</td>
							<td class="col-num">{signed(s.method0.signed_pct_error)}</td>
							<td class="col-num">{signed(s.method1.signed_pct_error)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>

	<!-- Error by regime — observed features only, ≥5 events per bucket. -->
	<section class="regimes">
		<h2 class="section-title">Error by regime</h2>
		<p class="section-sub ll-measure">
			Median absolute error, cut by observed features only — promotion type, depth,
			season and the like. No cut uses a truth-derived label, and every bucket holds at
			least five events, so no number reads back to an individual promotion.
		</p>

		{#each Object.entries(REGIME_NAMES) as [feature, name] (feature)}
			<div class="regime">
				<h3>{name}</h3>
				<div class="lailara-table-wrap">
					<table class="acc-table">
						<thead>
							<tr>
								<th scope="col">{name}</th>
								<th class="col-num" scope="col">Method 0</th>
								<th class="col-num" scope="col">Method 1</th>
							</tr>
						</thead>
						<tbody>
							{#each sharedRegime(feature) as row (row.label)}
								<tr>
									<td>{row.label}</td>
									<td class="col-num">{row.m0 ? pct(row.m0.median_abs_pct_error) : '—'}</td>
									<td class="col-num">{row.m1 ? pct(row.m1.median_abs_pct_error) : '—'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/each}

		{#if relaxRegime.length}
			<div class="regime">
				<h3>Match relaxation — Method 1 only</h3>
				<p class="section-sub ll-measure">
					Method 1 matches comparable stores by region, format class and volume; where the
					in-format pool is too thin it relaxes to region and volume alone. This cut asks
					whether the relaxation costs accuracy — and it does.
				</p>
				<div class="lailara-table-wrap">
					<table class="acc-table">
						<thead>
							<tr>
								<th scope="col">Match stratum</th>
								<th class="col-num" scope="col">Median error</th>
								<th class="col-num" scope="col">Bias</th>
								<th class="col-num" scope="col">Events</th>
							</tr>
						</thead>
						<tbody>
							{#each relaxRegime as b (b.label)}
								<tr>
									<td>{b.label}</td>
									<td class="col-num">{pct(b.median_abs_pct_error)}</td>
									<td class="col-num">{signed(b.median_signed_pct_error)}</td>
									<td class="col-num">{b.n_events}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}
	</section>

	<p class="disclosure ll-measure">
		<strong>Synthetic data is the only honest testbed for this.</strong> It is at once the
		only world where truth is knowable and the only world that can be published: real
		client promotion data can never be shown, by any vendor, at any client count. Anyone
		claiming to demonstrate accuracy on real client data is either breaching
		confidentiality or making it up. The methodology and the deliverable are real; the
		data is synthetic, and that is the point.
	</p>
</div>

<style>
	.accuracy {
		font-family: var(--ll-sans);
		color: var(--ll-london-20);
	}
	.eyebrow {
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--ll-red-42);
		margin: 0 0 var(--ll-space-sm);
	}
	.back {
		display: inline-block;
		font-size: 14px;
		color: var(--ll-london-20);
		text-decoration: underline;
		margin: 0 0 var(--ll-space-lg);
	}
	.back:hover {
		color: var(--ll-chicago-20);
	}
	.title {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(2rem, 6vw, 3.5rem);
		line-height: 1.05;
		letter-spacing: -0.02em;
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-lg);
	}
	.framing {
		font-size: 17px;
		line-height: 1.6;
		color: var(--ll-london-20);
		margin: 0 0 var(--ll-space-base);
	}
	.section-title {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.25rem, 3vw, 1.375rem);
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-xs);
	}
	.section-sub {
		font-size: 14px;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-base);
	}
	section {
		margin-top: var(--ll-space-3xl);
		padding-top: var(--ll-space-2xl);
		border-top: 1px solid var(--ll-london-85);
	}
	.cards {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--ll-space-lg);
		margin: var(--ll-space-base) 0 var(--ll-space-lg);
	}
	.method-card {
		border: 1px solid var(--ll-london-85);
		border-radius: var(--ll-radius);
		padding: var(--ll-space-lg);
	}
	.method-name {
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-sm);
	}
	.big {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(2.25rem, 5vw, 3rem);
		letter-spacing: -0.02em;
		color: var(--ll-tokyo-40);
		margin: 0;
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}
	.big-note {
		font-size: 13px;
		color: var(--ll-london-35);
		margin: var(--ll-space-xs) 0 var(--ll-space-sm);
	}
	.bias {
		font-size: 14px;
		font-weight: 600;
		color: var(--ll-london-20);
		margin: 0;
		font-variant-numeric: tabular-nums;
	}
	.read {
		font-size: 15px;
		line-height: 1.6;
		color: var(--ll-london-20);
		margin: 0;
	}
	.acc-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 14px;
	}
	.acc-table thead th {
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ll-london-35);
		text-align: left;
		padding: 0 var(--ll-space-base) var(--ll-space-sm);
		border-bottom: 2px solid var(--ll-london-5);
		white-space: nowrap;
	}
	.acc-table tbody td {
		padding: var(--ll-space-sm) var(--ll-space-base);
		border-bottom: 1px solid var(--ll-london-85);
		color: var(--ll-london-20);
	}
	.col-num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.regime {
		margin-top: var(--ll-space-lg);
	}
	.regime h3 {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: 18px;
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-sm);
	}
	.badge {
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.02em;
		padding: 1px 6px;
		border-radius: var(--ll-radius);
		white-space: nowrap;
	}
	.badge-story {
		background: var(--ll-chicago-95);
		color: var(--ll-chicago-20);
	}
	.disclosure {
		font-size: 14px;
		line-height: 1.6;
		color: var(--ll-london-35);
		margin: var(--ll-space-3xl) 0 0;
		padding-top: var(--ll-space-2xl);
		border-top: 1px solid var(--ll-london-85);
	}
	.lailara-table-wrap {
		overflow-x: auto;
		max-width: 100%;
		-webkit-overflow-scrolling: touch;
	}

	@media (max-width: 640px) {
		.cards {
			grid-template-columns: 1fr;
		}
	}
</style>
