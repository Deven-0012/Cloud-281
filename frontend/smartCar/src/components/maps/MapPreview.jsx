import React from 'react';
import Card from '../ui/Card';


export default function MapPreview() {
return (
<Card>
<div className="flex items-center justify-between mb-3">
<h2 className="font-medium">Map Preview</h2>
<button className="btn-secondary">Open Map</button>
</div>
<div className="aspect-[4/3] w-full grid place-items-center rounded-xl border border-dashed border-neutral-300 bg-neutral-50 text-sm text-neutral-500">
Live pins hidden in demo
</div>
</Card>
);
}