import { useState, useEffect, useMemo } from 'react';

export default function SearchBar({ filters, value, onChange }) {
  const [brand, setBrand] = useState(value?.brand || '');
  const [model, setModel] = useState(value?.model || '');
  const [availability, setAvailability] = useState(value?.availability || '');

  const brands = useMemo(() => filters?.brands || [], [filters]);
  const models = useMemo(() => filters?.models || [], [filters]);
  const availabilities = useMemo(() => filters?.availabilities || [], [filters]);

  const availabilityLabels = {
    lager: 'Lager',
    vorlauf: 'Vorlauf',
    bestellung: 'Bestellung',
  };

  useEffect(() => {
    setBrand(value?.brand || '');
    setModel(value?.model || '');
    setAvailability(value?.availability || '');
  }, [value?.brand, value?.model, value?.availability]);

  function handleBrandChange(e) {
    const newBrand = e.target.value;
    setBrand(newBrand);
    setModel('');
    onChange({ brand: newBrand, model: '', availability });
  }

  function handleModelChange(e) {
    const newModel = e.target.value;
    setModel(newModel);
    onChange({ brand, model: newModel, availability });
  }

  function handleAvailabilityChange(e) {
    const newAvail = e.target.value;
    setAvailability(newAvail);
    onChange({ brand, model, availability: newAvail });
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label htmlFor="search-brand" className="block text-sm font-medium text-gray-700 mb-1">
            Marke
          </label>
          <select
            id="search-brand"
            value={brand}
            onChange={handleBrandChange}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          >
            <option value="">Alle Marken</option>
            {brands.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="search-model" className="block text-sm font-medium text-gray-700 mb-1">
            Modell
          </label>
          <select
            id="search-model"
            value={model}
            onChange={handleModelChange}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none disabled:bg-gray-100 disabled:text-gray-400"
          >
            <option value="">Alle Modelle</option>
            {models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="search-availability" className="block text-sm font-medium text-gray-700 mb-1">
            Verfuegbarkeit
          </label>
          <select
            id="search-availability"
            value={availability}
            onChange={handleAvailabilityChange}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          >
            <option value="">Alle</option>
            {availabilities.map((a) => (
              <option key={a} value={a}>
                {availabilityLabels[a] || a}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
