import { useState } from 'react';
import { Link } from 'react-router-dom';

const currencyFormat = new Intl.NumberFormat('de-DE', {
  style: 'currency',
  currency: 'EUR',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const AVAILABILITY_STYLES = {
  lager: 'bg-green-100 text-green-800',
  vorlauf: 'bg-yellow-100 text-yellow-800',
  bestellung: 'bg-gray-100 text-gray-700',
};

const AVAILABILITY_LABELS = {
  lager: 'Sofort verfugbar',
  vorlauf: 'Vorlauf',
  bestellung: 'Bestellung',
};

function AvailabilityBadge({ availability }) {
  if (!availability) return null;
  const key = availability.toLowerCase();
  const style = AVAILABILITY_STYLES[key] || 'bg-gray-100 text-gray-700';
  const label = AVAILABILITY_LABELS[key] || availability;
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${style}`}>
      {label}
    </span>
  );
}

function SourceBadge({ source }) {
  if (!source) return null;
  const label = source === 'viscaal' ? 'Viscaal' : source === 'apeg' ? 'APEG' : source;
  return (
    <span className="inline-block px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
      {label}
    </span>
  );
}

function ImageGallery({ imageUrls }) {
  const [activeIndex, setActiveIndex] = useState(0);

  if (!imageUrls || imageUrls.length === 0) {
    return (
      <div className="w-full aspect-4/3 bg-gray-200 rounded-lg flex items-center justify-center">
        <svg
          className="w-16 h-16 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z"
          />
        </svg>
        <span className="ml-3 text-gray-500 text-lg">Kein Bild verfugbar</span>
      </div>
    );
  }

  return (
    <div>
      <div className="w-full aspect-4/3 bg-gray-100 rounded-lg overflow-hidden">
        <img
          src={imageUrls[activeIndex]}
          alt="Fahrzeugbild"
          className="w-full h-full object-cover"
          loading="lazy"
        />
      </div>
      {imageUrls.length > 1 && (
        <div className="mt-3 flex gap-2 overflow-x-auto pb-2">
          {imageUrls.map((url, index) => (
            <button
              key={index}
              onClick={() => setActiveIndex(index)}
              className={`shrink-0 w-20 h-16 rounded-md overflow-hidden border-2 transition-colors ${
                index === activeIndex
                  ? 'border-blue-600'
                  : 'border-transparent hover:border-gray-300'
              }`}
            >
              <img
                src={url}
                alt={`Bild ${index + 1}`}
                className="w-full h-full object-cover"
                loading="lazy"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function SpecRow({ label, value }) {
  if (value === null || value === undefined || value === '') return null;
  return (
    <div className="flex justify-between py-2 border-b border-gray-100">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900 text-right">{value}</span>
    </div>
  );
}

export default function VehicleDetail({ vehicle }) {
  const v = vehicle;

  const specs = [
    { label: 'Marke', value: v.brand },
    { label: 'Modell', value: v.model },
    { label: 'Variante', value: v.variant },
    { label: 'Ausstattung', value: v.trim_line },
    { label: 'Karosserie', value: v.body_type },
    { label: 'Kraftstoff', value: v.fuel_type },
    { label: 'Getriebe', value: v.gearbox },
    {
      label: 'Leistung',
      value:
        v.power_kw || v.power_ps
          ? `${v.power_kw ? `${v.power_kw} kW` : ''}${v.power_kw && v.power_ps ? ' / ' : ''}${v.power_ps ? `${v.power_ps} PS` : ''}`
          : null,
    },
    {
      label: 'Hubraum',
      value: v.engine_cc ? `${v.engine_cc.toLocaleString('de-DE')} ccm` : null,
    },
    {
      label: 'Kilometerstand',
      value:
        v.mileage_km !== null && v.mileage_km !== undefined
          ? `${v.mileage_km.toLocaleString('de-DE')} km`
          : null,
    },
    {
      label: 'Erstzulassung',
      value: v.first_reg_date
        ? new Date(v.first_reg_date).toLocaleDateString('de-DE', {
            month: '2-digit',
            year: 'numeric',
          })
        : null,
    },
    { label: 'Farbe', value: v.color },
    {
      label: 'Verfugbarkeit',
      value: v.availability
        ? AVAILABILITY_LABELS[v.availability.toLowerCase()] || v.availability
        : null,
    },
    {
      label: 'Quelle',
      value: v.source === 'viscaal' ? 'Viscaal' : v.source === 'apeg' ? 'APEG' : v.source,
    },
  ];

  return (
    <div>
      <Link
        to="/"
        className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-6 text-sm font-medium"
      >
        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Zuruck zur Ubersicht
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Left column: images + specs */}
        <div className="lg:col-span-3 space-y-6">
          <ImageGallery imageUrls={v.image_urls} />

          {/* Specs table */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Fahrzeugdaten</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
              {specs.map(
                (spec) =>
                  spec.value != null &&
                  spec.value !== '' && (
                    <SpecRow key={spec.label} label={spec.label} value={spec.value} />
                  )
              )}
            </div>
          </div>
        </div>

        {/* Right column: price block + actions */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-gray-200 p-6 sticky top-6 space-y-5">
            {/* Title */}
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {[v.brand, v.model].filter(Boolean).join(' ')}
              </h1>
              {v.variant && <p className="text-gray-600 mt-1">{v.variant}</p>}
            </div>

            {/* Badges */}
            <div className="flex flex-wrap gap-2">
              <AvailabilityBadge availability={v.availability} />
              <SourceBadge source={v.source} />
            </div>

            {/* Price block */}
            <div>
              <p className="text-sm text-gray-500 mb-1">Unser Preis</p>
              <p className="text-3xl font-bold text-blue-600">
                {v.price_eur != null ? currencyFormat.format(v.price_eur) : 'Preis auf Anfrage'}
              </p>

              {v.uvp_eur != null && v.uvp_eur > 0 && (
                <div className="mt-2">
                  <p className="text-sm text-gray-400 line-through">
                    UVP {currencyFormat.format(v.uvp_eur)}
                  </p>
                  {(v.savings_eur > 0 || v.savings_pct > 0) && (
                    <span className="inline-block mt-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                      Du sparst {v.savings_eur ? currencyFormat.format(v.savings_eur) : ''}
                      {v.savings_eur && v.savings_pct ? ' ' : ''}
                      {v.savings_pct ? `(${v.savings_pct.toFixed(0)}%)` : ''}
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* External link */}
            {v.source_url && (
              <a
                href={v.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full text-center px-4 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
              >
                Beim Anbieter ansehen
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
