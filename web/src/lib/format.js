// Display formatters shared by the Scorecard header and the ranked event list.
// Money arrives as integer cents from the pipeline; ratios as floats or null.

const usd = new Intl.NumberFormat('en-US', {
	style: 'currency',
	currency: 'USD',
	maximumFractionDigits: 0
});

/** Integer cents → "$104,425" (whole dollars; the header is not a ledger). */
export const dollars = (cents) => usd.format(cents / 100);

/** ROI ratio → "1.13×", or "—" when undefined (zero accrued cost). */
export const roiText = (roi) => (roi === null ? '—' : `${roi.toFixed(2)}×`);

/** Volume share (0–1+) → "62%", or "—" when undefined (no complied volume). */
export const pct = (share) => (share === null ? '—' : `${Math.round(share * 100)}%`);
