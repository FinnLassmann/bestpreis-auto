import { Link } from 'react-router-dom';

const priceFormatter = new Intl.NumberFormat('de-DE', {
  style: 'currency',
  currency: 'EUR',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const savingsFormatter = new Intl.NumberFormat('de-DE', {
  style: 'currency',
  currency: 'EUR',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

function SourceBadge({ source }) {
  const isViscaal = source === 'viscaal';
  return (
    <span
      className={`absolute top-2 right-2 px-2 py-0.5 rounded text-xs font-semibold text-white ${
        isViscaal ? 'bg-blue-600' : 'bg-purple-600'
      }`}
    >
      {isViscaal ? 'Viscaal' : 'APEG'}
    </span>
  );
}

function AvailabilityTag({ availability }) {
  const config = {
    lager: { label: 'Sofort verfuegbar', classes: 'bg-green-100 text-green-800' },
    vorlauf: { label: 'Vorlauf', classes: 'bg-yellow-100 text-yellow-800' },
    bestellung: { label: 'Bestellung', classes: 'bg-gray-100 text-gray-800' },
  };
  const { label, classes } = config[availability] || config.bestellung;
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${classes}`}>
      {label}
    </span>
  );
}

export default function VehicleCard({ vehicle }) {
  const {
    id,
    brand,
    model,
    variant,
    price_eur,
    savings_eur,
    savings_pct,
    fuel_type,
    power_ps,
    gearbox,
    availability,
    source,
    image_urls,
  } = vehicle;

  const imageUrl = image_urls && image_urls.length > 0 ? image_urls[0] : null;

  const specs = [fuel_type, power_ps ? `${power_ps} PS` : null, gearbox]
    .filter(Boolean)
    .join(' \u00B7 ');

  return (
    <Link
      to={`/fahrzeug/${id}`}
      className="block bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
    >
      <div className="relative aspect-[3/2] bg-gray-200">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={`${brand} ${model}`}
            loading="lazy"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z"
              />
            </svg>
          </div>
        )}
        <SourceBadge source={source} />
      </div>

      <div className="p-4">
        <h3 className="font-semibold text-gray-900 truncate">
          {brand} {model}
        </h3>
        {variant && (
          <p className="text-sm text-gray-500 truncate mt-0.5">{variant}</p>
        )}

        <div className="mt-3 flex items-baseline gap-2 flex-wrap">
          <span className="text-xl font-bold text-gray-900">
            {priceFormatter.format(price_eur)}
          </span>
          {savings_eur > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800">
              Du sparst {savingsFormatter.format(savings_eur)}
              {savings_pct > 0 && ` (${Math.round(savings_pct)}%)`}
            </span>
          )}
        </div>

        {specs && (
          <p className="text-sm text-gray-500 mt-2">{specs}</p>
        )}

        <div className="mt-3 flex items-center justify-between">
          <AvailabilityTag availability={availability} />
          <span className="text-sm font-medium text-blue-600 hover:text-blue-700">
            Mehr Details &rarr;
          </span>
        </div>
      </div>
    </Link>
  );
}
