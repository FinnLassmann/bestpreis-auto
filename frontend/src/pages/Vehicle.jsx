import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { fetchVehicle, submitLead } from '../lib/api';
import VehicleDetail from '../components/VehicleDetail';

function LoadingSkeleton() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8 animate-pulse">
      {/* Back link skeleton */}
      <div className="h-4 w-40 bg-gray-200 rounded mb-6" />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Left column */}
        <div className="lg:col-span-3 space-y-6">
          <div className="w-full aspect-4/3 bg-gray-200 rounded-lg" />
          <div className="flex gap-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="w-20 h-16 bg-gray-200 rounded-md" />
            ))}
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-3">
            <div className="h-5 w-32 bg-gray-200 rounded" />
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="flex justify-between">
                <div className="h-4 w-24 bg-gray-200 rounded" />
                <div className="h-4 w-32 bg-gray-200 rounded" />
              </div>
            ))}
          </div>
        </div>

        {/* Right column */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
            <div className="h-7 w-48 bg-gray-200 rounded" />
            <div className="h-4 w-32 bg-gray-200 rounded" />
            <div className="flex gap-2">
              <div className="h-6 w-24 bg-gray-200 rounded-full" />
              <div className="h-6 w-16 bg-gray-200 rounded-full" />
            </div>
            <div className="h-4 w-20 bg-gray-200 rounded" />
            <div className="h-9 w-40 bg-gray-200 rounded" />
            <div className="h-12 w-full bg-gray-200 rounded-lg" />
          </div>
        </div>
      </div>
    </div>
  );
}

function LeadForm({ vehicleId }) {
  const [form, setForm] = useState({ name: '', email: '', phone: '', message: '' });
  const [sending, setSending] = useState(false);
  const [banner, setBanner] = useState(null);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSending(true);
    setBanner(null);

    try {
      await submitLead({
        vehicle_id: vehicleId,
        name: form.name,
        email: form.email,
        phone: form.phone || undefined,
        message: form.message || undefined,
      });
      setBanner({ type: 'success', text: 'Ihre Anfrage wurde erfolgreich gesendet!' });
      setForm({ name: '', email: '', phone: '', message: '' });
    } catch (err) {
      if (err.status === 429) {
        setBanner({
          type: 'error',
          text: 'Zu viele Anfragen. Bitte versuchen Sie es spater erneut.',
        });
      } else {
        setBanner({
          type: 'error',
          text: err.message || 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.',
        });
      }
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Jetzt anfragen</h2>

      {banner && (
        <div
          className={`mb-4 px-4 py-3 rounded-lg text-sm font-medium ${
            banner.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {banner.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="lead-name" className="block text-sm font-medium text-gray-700 mb-1">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              id="lead-name"
              name="name"
              type="text"
              required
              value={form.name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ihr Name"
            />
          </div>
          <div>
            <label htmlFor="lead-email" className="block text-sm font-medium text-gray-700 mb-1">
              E-Mail <span className="text-red-500">*</span>
            </label>
            <input
              id="lead-email"
              name="email"
              type="email"
              required
              value={form.email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="ihre@email.de"
            />
          </div>
        </div>

        <div>
          <label htmlFor="lead-phone" className="block text-sm font-medium text-gray-700 mb-1">
            Telefon
          </label>
          <input
            id="lead-phone"
            name="phone"
            type="tel"
            value={form.phone}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="+49 123 456789"
          />
        </div>

        <div>
          <label htmlFor="lead-message" className="block text-sm font-medium text-gray-700 mb-1">
            Nachricht
          </label>
          <textarea
            id="lead-message"
            name="message"
            rows={4}
            value={form.message}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y"
            placeholder="Ihre Nachricht oder Fragen zum Fahrzeug..."
          />
        </div>

        <button
          type="submit"
          disabled={sending}
          className="w-full sm:w-auto px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {sending ? 'Wird gesendet...' : 'Anfrage senden'}
        </button>
      </form>
    </div>
  );
}

export default function Vehicle() {
  const { id } = useParams();
  const [vehicle, setVehicle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchVehicle(id);
        if (!cancelled) setVehicle(data);
      } catch (err) {
        if (!cancelled) {
          if (err.status === 404) {
            setError('Fahrzeug nicht gefunden. Moglicherweise ist es nicht mehr verfugbar.');
          } else {
            setError('Fehler beim Laden des Fahrzeugs. Bitte versuchen Sie es spater erneut.');
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center">
        <svg
          className="w-16 h-16 text-gray-300 mx-auto mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
          />
        </svg>
        <p className="text-gray-600 text-lg mb-6">{error}</p>
        <a
          href="/"
          className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
        >
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Zuruck zur Ubersicht
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-10">
      <VehicleDetail vehicle={vehicle} />
      <LeadForm vehicleId={vehicle.id} />
    </div>
  );
}
