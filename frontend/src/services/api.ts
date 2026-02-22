/**
 * Service API pour communiquer avec le back-end FastAPI.
 */

import axios, { AxiosInstance } from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || "10000");

// Créer une instance axios
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

// Types
export interface Listing {
  id: number;
  title: string;
  description?: string;
  property_type: "apartment" | "house" | "land" | "commercial" | "other";
  operation_type: "sale" | "rental";
  price: number;
  surface_area?: number;
  number_of_rooms?: number;
  number_of_bedrooms?: number;
  city: string;
  postal_code: string;
  district?: string;
  address_partial?: string;
  listing_url: string;
  image_urls?: string[];
  posted_date?: string;
  agency_id: number;
  created_at: string;
  last_updated: string;
}

export interface Agency {
  id: number;
  legal_name: string;
  website_url: string;
  postal_address?: string;
  postal_code?: string;
  city?: string;
  phone?: string;
  siren?: string;
  siret?: string;
  professional_card?: string;
  listings_count: number;
  created_at: string;
  last_scraped: string;
  is_active: boolean;
}

export interface SearchFilters {
  postal_code: string;
  property_type?: string;
  operation_type?: string;
  price_min?: number;
  price_max?: number;
  surface_min?: number;
  surface_max?: number;
  agency_id?: number;
  city?: string;
  limit?: number;
  offset?: number;
}

export interface SearchResponse {
  total: number;
  listings: Listing[];
  agencies: Agency[];
  filters_applied: Record<string, any>;
}

// Endpoints
export const listingsAPI = {
  /**
   * Rechercher les annonces avec filtres.
   */
  search: async (filters: SearchFilters): Promise<SearchResponse> => {
    const response = await apiClient.get("/api/listings/", { params: filters });
    return response.data;
  },

  /**
   * Récupérer une annonce par ID.
   */
  getById: async (id: number): Promise<Listing> => {
    const response = await apiClient.get(`/api/listings/${id}`);
    return response.data;
  },

  /**
   * Récupérer les annonces par code postal.
   */
  getByPostalCode: async (
    postalCode: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<any> => {
    const response = await apiClient.get(`/api/listings/by-postal-code/${postalCode}`, {
      params: { limit, offset },
    });
    return response.data;
  },

  /**
   * Récupérer les statistiques par code postal.
   */
  getStats: async (postalCode: string): Promise<any> => {
    const response = await apiClient.get(`/api/listings/stats/by-postal-code/${postalCode}`);
    return response.data;
  },
};

export const agenciesAPI = {
  /**
   * Lister les agences.
   */
  list: async (
    postalCode?: string,
    isActive?: boolean,
    limit: number = 50,
    offset: number = 0
  ): Promise<Agency[]> => {
    const response = await apiClient.get("/api/agencies/", {
      params: { postal_code: postalCode, is_active: isActive, limit, offset },
    });
    return response.data;
  },

  /**
   * Récupérer une agence par ID.
   */
  getById: async (id: number): Promise<Agency> => {
    const response = await apiClient.get(`/api/agencies/${id}`);
    return response.data;
  },

  /**
   * Récupérer les agences par code postal.
   */
  getByPostalCode: async (postalCode: string): Promise<Agency[]> => {
    const response = await apiClient.get(`/api/agencies/by-postal-code/${postalCode}`);
    return response.data;
  },

  /**
   * Récupérer les annonces d'une agence.
   */
  getListings: async (
    agencyId: number,
    limit: number = 50,
    offset: number = 0
  ): Promise<any> => {
    const response = await apiClient.get(`/api/agencies/${agencyId}/listings`, {
      params: { limit, offset },
    });
    return response.data;
  },
};

export const scraperAPI = {
  /**
   * Lancer le scraping pour un code postal.
   */
  scrapePostalCode: async (postalCode: string): Promise<any> => {
    const response = await apiClient.post(`/api/scraper/scrape-postal-code/${postalCode}`);
    return response.data;
  },

  /**
   * Récupérer les logs de scraping.
   */
  getLogs: async (limit: number = 50, offset: number = 0): Promise<any> => {
    const response = await apiClient.get("/api/scraper/logs", { params: { limit, offset } });
    return response.data;
  },

  /**
   * Récupérer les logs pour un domaine.
   */
  getLogsByDomain: async (
    domain: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<any> => {
    const response = await apiClient.get(`/api/scraper/logs/${domain}`, {
      params: { limit, offset },
    });
    return response.data;
  },
};

export const healthAPI = {
  /**
   * Vérifier la santé de l'API.
   */
  check: async (): Promise<any> => {
    const response = await apiClient.get("/health");
    return response.data;
  },

  /**
   * Récupérer les informations sur l'API.
   */
  getInfo: async (): Promise<any> => {
    const response = await apiClient.get("/api/info");
    return response.data;
  },
};

export default apiClient;
