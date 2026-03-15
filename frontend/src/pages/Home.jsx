import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchVehicles, fetchFilters } from '../lib/api';
import SearchBar from '../components/SearchBar';
import FilterPanel from '../components/FilterPanel';
import VehicleCard from '../components/VehicleCard';

const ITEMS_PER_PAGE = 24;

function SkeletonCard() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden animate-pulse">
      <div className="aspect-[3/2] bg-gray-200" />
      <div className="p-4 space-y-3">
        <div className="h-5 bg-gray-200 rounded w-3/4" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
        <div className="h-6 bg-gray-200 rounded w-1/3" />
        <div className="h-4 bg-gray-200 rounded w-2/3" />
        <div className="h-5 bg-gray-200 rounded w-1/4" />
      </div>
    </div>
  );
}

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [vehicles, setVehicles] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [filters, setFilters] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  function getParamValue(key) {
    return searchParams.get(key) || '';
  }

  function getParamArray(key) {
    const val = searchParams.get(key);
    return val ? val.split(',') : [];
  }

  const searchValues = {
    brand: getParamValue('brand'),
    model: getParamValue('model'),
    availability: getParamValue('availability'),
  };

  const filterValues = {
    price_min: getParamValue('price_min'),
    price_max: getParamValue('price_max'),
    fuel_types: getParamArray('fuel_types'),
    gearboxes: getParamArray('gearboxes'),
    source: getParamValue('source'),
  };

  const sort = getParamValue('sort') || 'price_asc';
  const page = parseInt(getParamValue('page') || '1', 10);

  const updateParams = useCallback(
    (updates) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        for (const [key, val] of Object.entries(updates)) {
          if (Array.isArray(val)) {
            if (val.length > 0) {
              next.set(key, val.join(','));
            } else {
              next.delete(key);
            }
          } else if (val === '' || val === null || val === undefined) {
            next.delete(key);
          } else {
            next.set(key, val);
          }
        }
        if (!updates.hasOwnProperty('page')) {
          next.set('page', '1');
        }
        return next;
      });
    },
    [setSearchParams]
  );

  function handleSearchChange(vals) {
    updateParams({ brand: vals.brand, model: vals.model, availability: vals.availability });
  }

  function handleFilterChange(vals) {
    updateParams({
      price_min: vals.price_min,
      price_max: vals.price_max,
      fuel_types: vals.fuel_types,
      gearboxes: vals.gearboxes,
      source: vals.source,
    });
  }

  function handleSortChange(e) {
    updateParams({ sort: e.target.value });
  }

  function goToPage(p) {
    updateParams({ page: String(p) });
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const currentBrand = searchParams.get('brand') || '';
    const currentModel = searchParams.get('model') || '';
    const currentAvailability = searchParams.get('availability') || '';
    const currentPriceMin = searchParams.get('price_min') || '';
    const currentPriceMax = searchParams.get('price_max') || '';
    const currentFuelTypes = searchParams.get('fuel_types') || '';
    const currentGearboxes = searchParams.get('gearboxes') || '';
    const currentSource = searchParams.get('source') || '';
    const currentSort = searchParams.get('sort') || 'price_asc';
    const currentPage = parseInt(searchParams.get('page') || '1', 10);

    const vehicleParams = {
      page: currentPage,
      limit: ITEMS_PER_PAGE,
      sort: currentSort,
    };
    const filterParams = {};

    if (currentBrand) { vehicleParams.brand = currentBrand; filterParams.brand = currentBrand; }
    if (currentModel) { vehicleParams.model = currentModel; filterParams.model = currentModel; }
    if (currentAvailability) { vehicleParams.availability = currentAvailability; filterParams.availability = currentAvailability; }
    if (currentPriceMin) { vehicleParams.price_min = currentPriceMin; filterParams.price_min = currentPriceMin; }
    if (currentPriceMax) { vehicleParams.price_max = currentPriceMax; filterParams.price_max = currentPriceMax; }
    if (currentFuelTypes) vehicleParams.fuel_type = currentFuelTypes;
    if (currentGearboxes) vehicleParams.gearbox = currentGearboxes;
    if (currentSource) { vehicleParams.source = currentSource; filterParams.source = currentSource; }

    Promise.all([fetchVehicles(vehicleParams), fetchFilters(filterParams)])
      .then(([vehicleData, filterData]) => {
        if (cancelled) return;
        setVehicles(vehicleData.items || []);
        setTotalCount(vehicleData.total_count ?? 0);
        setFilters(filterData);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message);
        setVehicles([]);
        setTotalCount(0);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [searchParams.toString()]);

  const totalPages = Math.max(1, Math.ceil(totalCount / ITEMS_PER_PAGE));

  function renderPageNumbers() {
    const pages = [];
    const maxVisible = 5;
    let start = Math.max(1, page - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    for (let i = start; i <= end; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => goToPage(i)}
          className={`px-3 py-1.5 text-sm rounded ${
            i === page
              ? 'bg-blue-600 text-white font-semibold'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          {i}
        </button>
      );
    }
    return pages;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Bestpreis Auto</h1>
          <span className="text-sm text-gray-500">EU-Reimport Marktplatz</span>
        </div>
      </header>

      <section className="bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-12 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold">
            Neue EU-Reimport Fahrzeuge bis zu 40% guenstiger
          </h2>
          <p className="mt-3 text-lg text-blue-100 max-w-2xl mx-auto">
            Vergleiche Preise von fuehrenden EU-Reimport Haendlern und spare tausende Euro
            gegenueber dem deutschen Listenpreis.
          </p>
        </div>
      </section>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-6">
          <SearchBar filters={filters} value={searchValues} onChange={handleSearchChange} />
        </div>

        <div className="flex flex-col md:flex-row gap-6">
          <aside className="w-full md:w-64 shrink-0">
            <FilterPanel filters={filters || {}} value={filterValues} onChange={handleFilterChange} />
          </aside>

          <div className="flex-1 min-w-0">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
              <p className="text-sm text-gray-600">
                {loading ? (
                  'Fahrzeuge werden geladen...'
                ) : error ? (
                  <span className="text-red-600">Fehler: {error}</span>
                ) : (
                  <span className="font-medium">{totalCount} Fahrzeuge gefunden</span>
                )}
              </p>
              <div className="flex items-center gap-2">
                <label htmlFor="sort" className="text-sm text-gray-600">
                  Sortierung:
                </label>
                <select
                  id="sort"
                  value={sort}
                  onChange={handleSortChange}
                  className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="price_asc">Preis aufsteigend</option>
                  <option value="price_desc">Preis absteigend</option>
                  <option value="savings_desc">Groesste Ersparnis</option>
                </select>
              </div>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 6 }).map((_, i) => (
                  <SkeletonCard key={i} />
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-gray-500">
                  Beim Laden der Fahrzeuge ist ein Fehler aufgetreten.
                </p>
                <button
                  onClick={() => window.location.reload()}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 transition-colors"
                >
                  Erneut versuchen
                </button>
              </div>
            ) : vehicles.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">Keine Fahrzeuge gefunden</p>
                <p className="text-gray-400 text-sm mt-1">
                  Versuche andere Filter oder Suchbegriffe.
                </p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {vehicles.map((v) => (
                    <VehicleCard key={v.id} vehicle={v} />
                  ))}
                </div>

                {totalPages > 1 && (
                  <nav className="mt-8 flex items-center justify-center gap-2">
                    <button
                      onClick={() => goToPage(page - 1)}
                      disabled={page <= 1}
                      className="px-3 py-1.5 text-sm rounded bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Zurueck
                    </button>
                    {renderPageNumbers()}
                    <button
                      onClick={() => goToPage(page + 1)}
                      disabled={page >= totalPages}
                      className="px-3 py-1.5 text-sm rounded bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Weiter
                    </button>
                  </nav>
                )}
              </>
            )}
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-sm text-gray-500">
          Bestpreis Auto - EU-Reimport Fahrzeuge zum besten Preis
        </div>
      </footer>
    </div>
  );
}
