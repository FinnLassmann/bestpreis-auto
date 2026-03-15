import { useState } from 'react';

export default function FilterPanel({ filters, value, onChange }) {
  const [open, setOpen] = useState(false);

  const fuelTypes = filters?.fuel_types || [];
  const gearboxes = filters?.gearboxes || [];

  const selectedFuels = value?.fuel_types || [];
  const selectedGearboxes = value?.gearboxes || [];
  const priceMin = value?.price_min || '';
  const priceMax = value?.price_max || '';
  const source = value?.source || '';

  function update(patch) {
    onChange({ ...value, ...patch });
  }

  function toggleInArray(arr, item) {
    return arr.includes(item) ? arr.filter((v) => v !== item) : [...arr, item];
  }

  function handleReset() {
    onChange({
      fuel_types: [],
      gearboxes: [],
      price_min: '',
      price_max: '',
      source: '',
    });
  }

  const hasActiveFilters =
    selectedFuels.length > 0 ||
    selectedGearboxes.length > 0 ||
    priceMin !== '' ||
    priceMax !== '' ||
    source !== '';

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 md:hidden text-left"
      >
        <span className="font-medium text-gray-900">
          Filter
          {hasActiveFilters && (
            <span className="ml-2 inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-xs">
              !
            </span>
          )}
        </span>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <div className={`${open ? 'block' : 'hidden'} md:block p-4 space-y-5`}>
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-2">Preisspanne</h3>
          <div className="flex items-center gap-2">
            <input
              type="number"
              placeholder="Min"
              value={priceMin}
              onChange={(e) => update({ price_min: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
            <span className="text-gray-400">-</span>
            <input
              type="number"
              placeholder="Max"
              value={priceMax}
              onChange={(e) => update({ price_max: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        {fuelTypes.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Kraftstoff</h3>
            <div className="space-y-1.5">
              {fuelTypes.map((fuel) => (
                <label key={fuel} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedFuels.includes(fuel)}
                    onChange={() => update({ fuel_types: toggleInArray(selectedFuels, fuel) })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{fuel}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {gearboxes.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Getriebe</h3>
            <div className="space-y-1.5">
              {gearboxes.map((gb) => (
                <label key={gb} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedGearboxes.includes(gb)}
                    onChange={() => update({ gearboxes: toggleInArray(selectedGearboxes, gb) })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{gb}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-2">Quelle</h3>
          <div className="space-y-1.5">
            {[
              { label: 'Alle', val: '' },
              { label: 'Viscaal', val: 'viscaal' },
              { label: 'APEG', val: 'apeg' },
            ].map((opt) => (
              <label key={opt.val} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="source"
                  checked={source === opt.val}
                  onChange={() => update({ source: opt.val })}
                  className="border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>

        {hasActiveFilters && (
          <button
            type="button"
            onClick={handleReset}
            className="w-full text-center text-sm text-red-600 hover:text-red-700 font-medium py-2 border border-red-200 rounded-md hover:bg-red-50 transition-colors"
          >
            Filter zuruecksetzen
          </button>
        )}
      </div>
    </div>
  );
}
