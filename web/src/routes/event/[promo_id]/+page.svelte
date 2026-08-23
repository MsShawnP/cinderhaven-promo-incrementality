<script>
	// Event Anatomy — the per-event explanation. Observed + estimated only: the
	// three-bar volume waterfall a blind estimator can defend (gross → subsidized
	// baseline → net incremental lift), with the M0/M1 toggle and margin/cost
	// alongside. Dip and transfer are NOT here — they are protected truth (the next
	// estimation arc). Story annotations describe design intent from public upstream
	// docs, never truth values; the truth-scored error lives one click away at
	// /accuracy. See DECISIONS 2026-08-22.
	import { dollars, roiText, pct } from '$lib/format.js';

	let { data } = $props();
	const e = data.event;

	let method = $state('method1'); // comparable-store first — the more defensible read
	const m = $derived(e[method]);

	const fmtUnits = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
	const units = (x) => (x === null || x === undefined ? '—' : fmtUnits.format(x));

	const RETAILER = (r) => r.replace('RET-', '');

	// --- waterfall geometry ---------------------------------------------------
	const W = 680;
	const H = 300;
	const PAD_TOP = 44;
	const PAD_BOTTOM = 48;
	const PAD_X = 24;
	const PLOT_H = H - PAD_TOP - PAD_BOTTOM;
	const BAND = (W - 2 * PAD_X) / 3;
	const BAR_W = BAND * 0.52;

	// value → y, over a domain that always includes zero (net can be negative on a
	// dip artifact). Reactive to the active method.
	const vmax = $derived(m.estimable ? Math.max(m.gross_promoted_units, 0) : 1);
	const vmin = $derived(m.estimable ? Math.min(m.net_incremental_units, 0) : 0);
	const span = $derived(vmax - vmin || 1);
	const y = $derived((v) => PAD_TOP + ((vmax - v) / span) * PLOT_H);
	const cx = (i) => PAD_X + BAND * i + BAND / 2;
	const rect = (topVal, botVal) => {
		const yt = y(topVal);
		const yb = y(botVal);
		return { y: Math.min(yt, yb), height: Math.max(Math.abs(yb - yt), 1) };
	};

	const bars = $derived(
		m.estimable
			? [
					{
						i: 0,
						label: 'Gross promoted',
						value: m.gross_promoted_units,
						...rect(m.gross_promoted_units, 0),
						fill: 'var(--ll-chicago-70)'
					},
					{
						i: 1,
						label: '− Subsidized baseline',
						value: m.subsidized_baseline_units,
						...rect(m.gross_promoted_units, m.net_incremental_units),
						fill: 'var(--ll-london-70)'
					},
					{
						i: 2,
						label: '= Net incremental',
						value: m.net_incremental_units,
						...rect(m.net_incremental_units, 0),
						fill: m.net_incremental_units >= 0 ? 'var(--ll-hk-35)' : 'var(--ll-tokyo-40)'
					}
				]
			: []
	);

	// --- story / phantom narrative — design intent only, never truth ----------
	const givePct = $derived(m.subsidized_cost_share === null ? null : Math.round(m.subsidized_cost_share * 100));
	const STORY = $derived({
		clean_winner: {
			title: 'Clean winner — design intent',
			body: `A promotion built to genuinely work: modest lift, trivial spend, strong return. The paradox on display — about ${givePct}% of the discounted volume would have sold anyway, yet the ROI is high because the trade cost was tiny. A high giveaway share is not automatically a bad buy; what matters is what the spend bought relative to what it cost.`
		},
		pure_subsidy: {
			title: 'Pure subsidy — design intent',
			body: `A promotion built so that most of the discounted volume needed no discount. Roughly ${givePct}% of the trade spend subsidized baseline that would have sold anyway — dollars spent to move volume already moving.`
		},
		pantry_trap: {
			title: 'Pantry trap — design intent',
			body: `A promotion built to borrow from the future: shoppers pantry-load during the deal, then buy less after. That post-promo dip is not netted out of the bars above — the estimator scores only the promo weeks. The dip becomes its own estimated bar in the next method arc; for now, the accuracy view shows how far the estimate lands from truth.`
		},
		hero_cannibal: {
			title: 'Hero cannibal — design intent',
			body: `A promotion built so the hero SKU's lift partly transfers from its own shelf-mates — cannibalization, not net new volume. The bars above cannot separate transfer from true lift. That split becomes its own estimated bar in the next method arc; the accuracy view scores the gap today.`
		}
	}[e.story_tag]);

	const PHANTOM = $derived(
		e.plan_status === 'phantom'
			? `Planned and funded, ran nowhere — a phantom. There was no real promotion, so the small incremental above is estimation noise around zero, not lift.${e.method0.accrued_cost_cents === 0 ? ' Scan-funded, so nothing accrued: cost is $0 by construction.' : ''}`
			: e.plan_status === 'unplanned'
				? 'Ran without a plan — unplanned trade activity, scored like any other event.'
				: null
	);
</script>

<div class="lailara-container anatomy">
	<p class="eyebrow">Event Anatomy</p>
	<a class="back" href="/">← Back to the Scorecard</a>

	<h1 class="title">{e.promo_id}</h1>
	<p class="meta">
		{RETAILER(e.retailer_id)} · {e.sku} · {e.promo_type} · {e.discount_depth_pct}% off ·
		{e.n_weeks} {e.n_weeks === 1 ? 'week' : 'weeks'} · {e.start_week} to {e.end_week} · {e.funding_mechanism}
		{#if e.plan_status !== 'executed'}<span class="badge badge-status">{e.plan_status}</span>{/if}
		{#if e.story_tag}<span class="badge badge-story">{e.story_tag.replace('_', ' ')}</span>{/if}
	</p>

	<!-- Baseline-method toggle inside the view. -->
	<div class="toggle" role="group" aria-label="Baseline method">
		<button class:active={method === 'method0'} onclick={() => (method = 'method0')}>Method 0 · pre-period</button>
		<button class:active={method === 'method1'} onclick={() => (method = 'method1')}>Method 1 · comparable-store</button>
	</div>

	{#if m.estimable}
		<figure class="chart">
			<figcaption>
				<h2>Where the promoted volume came from</h2>
				<p class="chart-sub">
					Units over the promo weeks, {method === 'method0' ? 'Method 0' : 'Method 1'} baseline. The
					middle bar is volume that would have sold anyway; only the last bar is caused by the promo.
				</p>
			</figcaption>

			<svg viewBox="0 0 {W} {H}" role="img" aria-label="Volume waterfall">
				<!-- zero baseline (visible when net dips below zero) -->
				<line x1={PAD_X} x2={W - PAD_X} y1={y(0)} y2={y(0)} stroke="var(--ll-london-85)" />
				<!-- step connectors -->
				<line x1={cx(0) + BAR_W / 2} x2={cx(1) - BAR_W / 2} y1={y(m.gross_promoted_units)} y2={y(m.gross_promoted_units)} stroke="var(--ll-london-85)" stroke-dasharray="3 3" />
				<line x1={cx(1) + BAR_W / 2} x2={cx(2) - BAR_W / 2} y1={y(m.net_incremental_units)} y2={y(m.net_incremental_units)} stroke="var(--ll-london-85)" stroke-dasharray="3 3" />
				{#each bars as bar (bar.i)}
					<rect x={cx(bar.i) - BAR_W / 2} y={bar.y} width={BAR_W} height={bar.height} fill={bar.fill} rx="2" />
					<text class="bar-value" x={cx(bar.i)} y={bar.y - 8} text-anchor="middle">{units(bar.value)}</text>
					<text class="bar-label" x={cx(bar.i)} y={H - PAD_BOTTOM + 20} text-anchor="middle">{bar.label}</text>
				{/each}
			</svg>

			<p class="footnote">
				Gross promoted volume minus the subsidized baseline the estimator would have expected leaves
				net incremental lift. Dip (pantry-load) and transfer (cannibalization) are not shown — a blind
				estimator cannot see them; they arrive as their own bars in the next method arc.
			</p>
		</figure>

		<!-- Margin and accrued cost alongside. -->
		<dl class="stats">
			<div>
				<dt>Net incremental margin</dt>
				<dd>{dollars(m.net_margin_cents)}</dd>
			</div>
			<div>
				<dt>Accrued trade cost</dt>
				<dd>{dollars(m.accrued_cost_cents)}</dd>
			</div>
			<div>
				<dt>Return on spend</dt>
				<dd class:neg={m.lost_money}>{roiText(m.roi)}</dd>
			</div>
			<div>
				<dt>Giveaway share</dt>
				<dd>{pct(m.subsidized_cost_share)}{#if m.baseline_exceeds_promoted}<sup class="mark">†</sup>{/if}</dd>
			</div>
		</dl>
		{#if m.baseline_exceeds_promoted}
			<p class="dip-note">
				† Giveaway over 100%: sales during the promo fell below the baseline — a dip the naive baseline
				sits above. Method 0 reads a dip and a weak promotion the same way.
			</p>
		{/if}
	{:else}
		<p class="not-estimable">
			Not estimable by {method === 'method0' ? 'Method 0' : 'Method 1'} —
			{m.exclusion_reason === 'insufficient_pre_period'
				? 'too little pre-period history for a naive baseline (a series-start event).'
				: 'too few comparable control stores to match against.'}
			{#if e[method === 'method0' ? 'method1' : 'method0'].estimable}
				Try the other method above.
			{/if}
		</p>
	{/if}

	{#if STORY}
		<aside class="annotation">
			<h3>{STORY.title}</h3>
			<p>{STORY.body}</p>
		</aside>
	{/if}
	{#if PHANTOM}
		<aside class="annotation">
			<h3>{e.plan_status === 'phantom' ? 'Phantom' : 'Unplanned'} — design intent</h3>
			<p>{PHANTOM}</p>
		</aside>
	{/if}

	<a class="accuracy-link" href="/accuracy">
		<span class="accuracy-link-lead">How wrong is this estimate?</span>
		<span class="accuracy-link-sub">The error against known truth lives in the accuracy view — never on this page. →</span>
	</a>
</div>

<style>
	.anatomy {
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
		font-size: clamp(2rem, 6vw, 3rem);
		letter-spacing: -0.02em;
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-xs);
	}
	.meta {
		font-size: 14px;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-lg);
		line-height: 1.6;
	}
	.badge {
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.02em;
		padding: 1px 6px;
		border-radius: var(--ll-radius);
		white-space: nowrap;
		margin-left: var(--ll-space-xs);
		text-transform: capitalize;
	}
	.badge-story {
		background: var(--ll-chicago-95);
		color: var(--ll-chicago-20);
	}
	.badge-status {
		background: var(--ll-sg-95);
		color: var(--ll-sg-35);
	}
	.toggle {
		display: inline-flex;
		border: 1px solid var(--ll-chicago-20);
		border-radius: var(--ll-radius);
		overflow: hidden;
		margin: 0 0 var(--ll-space-xl);
	}
	.toggle button {
		font-family: var(--ll-sans);
		font-size: 14px;
		font-weight: 600;
		padding: 8px 16px;
		border: none;
		background: transparent;
		color: var(--ll-chicago-20);
		cursor: pointer;
	}
	.toggle button.active {
		background: var(--ll-chicago-20);
		color: #fff;
	}
	.chart {
		margin: 0 0 var(--ll-space-xl);
	}
	.chart figcaption h2 {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.25rem, 3vw, 1.375rem);
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-xxs);
	}
	.chart-sub {
		font-size: 14px;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-base);
		max-width: var(--ll-body-max-width);
	}
	svg {
		width: 100%;
		max-width: 680px;
		height: auto;
		display: block;
	}
	.bar-value {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: 16px;
		fill: var(--ll-london-5);
	}
	.bar-label {
		font-family: var(--ll-sans);
		font-size: 12px;
		fill: var(--ll-london-35);
	}
	.footnote {
		font-size: 12px;
		font-style: italic;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: var(--ll-space-sm) 0 0;
		max-width: var(--ll-body-max-width);
	}
	.stats {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--ll-space-lg);
		margin: 0 0 var(--ll-space-base);
		padding: var(--ll-space-lg) 0;
		border-top: 1px solid var(--ll-london-85);
		border-bottom: 1px solid var(--ll-london-85);
	}
	.stats dt {
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-xs);
	}
	.stats dd {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.375rem, 3vw, 1.75rem);
		letter-spacing: -0.02em;
		color: var(--ll-london-5);
		margin: 0;
		font-variant-numeric: tabular-nums;
	}
	.stats dd.neg {
		color: var(--ll-tokyo-40);
	}
	.mark {
		color: var(--ll-london-40);
		font-size: 0.7em;
	}
	.dip-note,
	.not-estimable {
		font-size: 13px;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: var(--ll-space-sm) 0 0;
		max-width: var(--ll-body-max-width);
	}
	.not-estimable {
		padding: var(--ll-space-lg);
		border: 1px solid var(--ll-london-85);
		border-radius: var(--ll-radius);
		font-size: 15px;
		color: var(--ll-london-20);
	}
	.annotation {
		margin: var(--ll-space-lg) 0 0;
		padding: var(--ll-space-lg);
		border-left: 3px solid var(--ll-chicago-20);
		background: var(--ll-chicago-95);
		border-radius: var(--ll-radius);
	}
	.annotation h3 {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: 18px;
		color: var(--ll-chicago-20);
		margin: 0 0 var(--ll-space-xs);
	}
	.annotation p {
		font-size: 15px;
		line-height: 1.6;
		color: var(--ll-london-20);
		margin: 0;
		max-width: var(--ll-body-max-width);
	}
	.accuracy-link {
		display: block;
		margin: var(--ll-space-2xl) 0 0;
		padding: var(--ll-space-lg);
		border: 1px solid var(--ll-chicago-20);
		border-radius: var(--ll-radius);
		text-decoration: none;
		background: var(--ll-canvas);
	}
	.accuracy-link:hover {
		background: var(--ll-chicago-95);
	}
	.accuracy-link-lead {
		display: block;
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.125rem, 2.5vw, 1.25rem);
		color: var(--ll-chicago-20);
		margin: 0 0 var(--ll-space-xxs);
	}
	.accuracy-link-sub {
		display: block;
		font-size: 14px;
		color: var(--ll-london-20);
	}

	@media (max-width: 640px) {
		.stats {
			grid-template-columns: repeat(2, 1fr);
		}
	}
</style>
