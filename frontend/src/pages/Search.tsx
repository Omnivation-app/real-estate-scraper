/**
 * Page de recherche principale.
 */

import React, { useState, useEffect } from "react";
import { listingsAPI, agenciesAPI, scraperAPI, type SearchResponse, type Listing, type Agency } from "../services/api";
import "./Search.css";

export default function Search() {
  const [postalCode, setPostalCode] = useState("");
  const [propertyType, setPropertyType] = useState("");
  const [operationType, setOperationType] = useState("");
  const [priceMin, setPriceMin] = useState("");
  const [priceMax, setPriceMax] = useState("");
  const [surfaceMin, setSurfaceMin] = useState("");
  const [surfaceMax, setSurfaceMax] = useState("");
  const [agencyId, setAgencyId] = useState("");

  const [results, setResults] = useState<SearchResponse | null>(null);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [scraping, setScraping] = useState(false);

  // Récupérer les agences quand le code postal change
  useEffect(() => {
    if (postalCode.length === 5) {
      loadAgencies(postalCode);
    }
  }, [postalCode]);

  const loadAgencies = async (postal: string) => {
    try {
      const data = await agenciesAPI.getByPostalCode(postal);
      setAgencies(data);
    } catch (err) {
      console.error("Error loading agencies:", err);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const filters = {
        postal_code: postalCode,
        property_type: propertyType || undefined,
        operation_type: operationType || undefined,
        price_min: priceMin ? parseFloat(priceMin) : undefined,
        price_max: priceMax ? parseFloat(priceMax) : undefined,
        surface_min: surfaceMin ? parseFloat(surfaceMin) : undefined,
        surface_max: surfaceMax ? parseFloat(surfaceMax) : undefined,
        agency_id: agencyId ? parseInt(agencyId) : undefined,
      };

      const data = await listingsAPI.search(filters);
      setResults(data);
    } catch (err: any) {
      setError(err.message || "Error searching listings");
    } finally {
      setLoading(false);
    }
  };

  const handleScrape = async () => {
    if (!postalCode) {
      setError("Please enter a postal code");
      return;
    }

    setScraping(true);
    setError("");

    try {
      await scraperAPI.scrapePostalCode(postalCode);
      // Attendre un peu puis recharger les résultats
      setTimeout(() => {
        handleSearch({ preventDefault: () => {} } as any);
        setScraping(false);
      }, 2000);
    } catch (err: any) {
      setError(err.message || "Error starting scrape");
      setScraping(false);
    }
  };

  return (
    <div className="search-container">
      <header className="search-header">
        <h1>🏠 Real Estate Scraper</h1>
        <p>Find properties by postal code with real-time data from multiple agencies</p>
      </header>

      <main className="search-main">
        {/* Search Form */}
        <form className="search-form" onSubmit={handleSearch}>
          <div className="form-group">
            <label htmlFor="postal-code">Postal Code *</label>
            <input
              id="postal-code"
              type="text"
              value={postalCode}
              onChange={(e) => setPostalCode(e.target.value)}
              placeholder="e.g., 75015"
              maxLength={5}
              pattern="[0-9]{5}"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="property-type">Property Type</label>
              <select
                id="property-type"
                value={propertyType}
                onChange={(e) => setPropertyType(e.target.value)}
              >
                <option value="">All Types</option>
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="land">Land</option>
                <option value="commercial">Commercial</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="operation-type">Operation</label>
              <select
                id="operation-type"
                value={operationType}
                onChange={(e) => setOperationType(e.target.value)}
              >
                <option value="">All Operations</option>
                <option value="sale">Sale</option>
                <option value="rental">Rental</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="price-min">Price Min (€)</label>
              <input
                id="price-min"
                type="number"
                value={priceMin}
                onChange={(e) => setPriceMin(e.target.value)}
                placeholder="0"
              />
            </div>

            <div className="form-group">
              <label htmlFor="price-max">Price Max (€)</label>
              <input
                id="price-max"
                type="number"
                value={priceMax}
                onChange={(e) => setPriceMax(e.target.value)}
                placeholder="999999"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="surface-min">Surface Min (m²)</label>
              <input
                id="surface-min"
                type="number"
                value={surfaceMin}
                onChange={(e) => setSurfaceMin(e.target.value)}
                placeholder="0"
              />
            </div>

            <div className="form-group">
              <label htmlFor="surface-max">Surface Max (m²)</label>
              <input
                id="surface-max"
                type="number"
                value={surfaceMax}
                onChange={(e) => setSurfaceMax(e.target.value)}
                placeholder="999"
              />
            </div>
          </div>

          {agencies.length > 0 && (
            <div className="form-group">
              <label htmlFor="agency">Agency</label>
              <select
                id="agency"
                value={agencyId}
                onChange={(e) => setAgencyId(e.target.value)}
              >
                <option value="">All Agencies</option>
                {agencies.map((agency) => (
                  <option key={agency.id} value={agency.id}>
                    {agency.legal_name} ({agency.listings_count})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="form-actions">
            <button type="submit" disabled={loading || !postalCode}>
              {loading ? "Searching..." : "Search"}
            </button>
            <button
              type="button"
              onClick={handleScrape}
              disabled={scraping || !postalCode}
              className="scrape-btn"
            >
              {scraping ? "Scraping..." : "Scrape Now"}
            </button>
          </div>
        </form>

        {/* Error Message */}
        {error && <div className="error-message">{error}</div>}

        {/* Results */}
        {results && (
          <div className="results-section">
            <div className="results-header">
              <h2>Results</h2>
              <p className="results-count">
                Found <strong>{results.total}</strong> properties
              </p>
            </div>

            {/* Listings Grid */}
            <div className="listings-grid">
              {results.listings.length > 0 ? (
                results.listings.map((listing) => (
                  <ListingCard key={listing.id} listing={listing} />
                ))
              ) : (
                <div className="no-results">No listings found. Try different filters.</div>
              )}
            </div>

            {/* Agencies Summary */}
            {results.agencies.length > 0 && (
              <div className="agencies-section">
                <h3>Agencies ({results.agencies.length})</h3>
                <div className="agencies-list">
                  {results.agencies.map((agency) => (
                    <div key={agency.id} className="agency-card">
                      <h4>{agency.legal_name}</h4>
                      <p className="agency-info">
                        📍 {agency.city}, {agency.postal_code}
                      </p>
                      {agency.phone && <p className="agency-info">📞 {agency.phone}</p>}
                      {agency.siren && <p className="agency-info">SIREN: {agency.siren}</p>}
                      <a href={agency.website_url} target="_blank" rel="noopener noreferrer">
                        Visit Website →
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function ListingCard({ listing }: { listing: Listing }) {
  return (
    <div className="listing-card">
      {listing.image_urls && listing.image_urls.length > 0 && (
        <img src={listing.image_urls[0]} alt={listing.title} className="listing-image" />
      )}
      <div className="listing-content">
        <h3>{listing.title}</h3>
        <p className="listing-price">€{listing.price.toLocaleString()}</p>
        <div className="listing-details">
          {listing.surface_area && (
            <span className="detail">📏 {listing.surface_area} m²</span>
          )}
          {listing.number_of_rooms && (
            <span className="detail">🚪 {listing.number_of_rooms} rooms</span>
          )}
          <span className="detail">📍 {listing.city}</span>
        </div>
        <div className="listing-meta">
          <span className={`badge ${listing.operation_type}`}>
            {listing.operation_type === "sale" ? "For Sale" : "For Rent"}
          </span>
          <span className="badge property-type">{listing.property_type}</span>
        </div>
        <a href={listing.listing_url} target="_blank" rel="noopener noreferrer" className="listing-link">
          View Listing →
        </a>
      </div>
    </div>
  );
}
