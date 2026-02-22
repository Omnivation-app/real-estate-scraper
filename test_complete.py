#!/usr/bin/env python3
"""
Script de test complet pour l'application Real Estate Scraper
Teste tous les endpoints et fonctionnalités principales
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

class TestRunner:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        self.token = None
        self.user_id = None
        self.agency_id = None
        self.listing_id = None
    
    def log(self, test_name: str, status: str, message: str = "", duration: float = 0):
        """Enregistrer un résultat de test"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "duration": f"{duration:.2f}s" if duration else "",
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        emoji = "✅" if status == "PASS" else "❌"
        print(f"{emoji} {test_name}: {status} {message}")
    
    def print_summary(self):
        """Afficher un résumé des tests"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = total - passed
        
        print("\n" + "="*60)
        print("RÉSUMÉ DES TESTS")
        print("="*60)
        print(f"Total: {total} | Réussis: {passed} | Échoués: {failed}")
        print(f"Taux de réussite: {(passed/total*100):.1f}%")
        print("="*60 + "\n")
        
        # Afficher les tests échoués
        failed_tests = [r for r in self.results if r["status"] == "FAIL"]
        if failed_tests:
            print("TESTS ÉCHOUÉS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
    
    # ==================== HEALTH CHECKS ====================
    
    def test_health_check(self):
        """Tester l'endpoint de santé"""
        start = time.time()
        try:
            response = self.session.get(f"{self.base_url}/health")
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log("Health Check", "PASS", f"DB: {data.get('database')}", duration)
                else:
                    self.log("Health Check", "FAIL", "Status not healthy", duration)
            else:
                self.log("Health Check", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Health Check", "FAIL", str(e))
    
    def test_api_info(self):
        """Tester l'endpoint d'info API"""
        start = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/info")
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                if "name" in data and "version" in data:
                    self.log("API Info", "PASS", f"v{data.get('version')}", duration)
                else:
                    self.log("API Info", "FAIL", "Missing fields", duration)
            else:
                self.log("API Info", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("API Info", "FAIL", str(e))
    
    # ==================== AUTHENTICATION ====================
    
    def test_register(self):
        """Tester l'enregistrement"""
        start = time.time()
        try:
            payload = {
                "email": f"test_{int(time.time())}@example.com",
                "username": f"testuser_{int(time.time())}",
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/register", json=payload)
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get("user_id")
                self.log("Register", "PASS", f"User ID: {self.user_id}", duration)
            else:
                self.log("Register", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Register", "FAIL", str(e))
    
    def test_login(self):
        """Tester la connexion"""
        if not self.user_id:
            self.log("Login", "SKIP", "No user registered")
            return
        
        start = time.time()
        try:
            payload = {
                "username": f"testuser_{int(time.time())}",
                "password": "TestPassword123!"
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/login", json=payload)
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log("Login", "PASS", f"Token obtained", duration)
            else:
                self.log("Login", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Login", "FAIL", str(e))
    
    # ==================== DISCOVERY ====================
    
    def test_discover_agencies(self):
        """Tester la découverte d'agences"""
        start = time.time()
        try:
            response = self.session.post(f"{self.base_url}/api/discovery/discover-agencies/75015")
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                discovered = data.get("agencies_discovered", 0)
                saved = data.get("agencies_saved", 0)
                self.log("Discover Agencies", "PASS", f"Found: {discovered}, Saved: {saved}", duration)
            else:
                self.log("Discover Agencies", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Discover Agencies", "FAIL", str(e))
    
    def test_get_agencies(self):
        """Tester la récupération des agences"""
        start = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/discovery/agencies", params={
                "postal_code": "75015",
                "limit": 10
            })
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                agencies = data.get("agencies", [])
                if agencies:
                    self.agency_id = agencies[0].get("id")
                    self.log("Get Agencies", "PASS", f"Found: {len(agencies)}", duration)
                else:
                    self.log("Get Agencies", "PASS", "No agencies found", duration)
            else:
                self.log("Get Agencies", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Get Agencies", "FAIL", str(e))
    
    def test_get_agency_details(self):
        """Tester la récupération des détails d'une agence"""
        if not self.agency_id:
            self.log("Get Agency Details", "SKIP", "No agency ID")
            return
        
        start = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/discovery/agencies/{self.agency_id}")
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                name = data.get("name", "Unknown")
                self.log("Get Agency Details", "PASS", f"Agency: {name}", duration)
            else:
                self.log("Get Agency Details", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Get Agency Details", "FAIL", str(e))
    
    # ==================== LISTINGS ====================
    
    def test_search_listings(self):
        """Tester la recherche d'annonces"""
        start = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/discovery/listings", params={
                "postal_code": "75015",
                "price_min": 100000,
                "price_max": 500000,
                "limit": 10
            })
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                listings = data.get("listings", [])
                if listings:
                    self.listing_id = listings[0].get("id")
                    self.log("Search Listings", "PASS", f"Found: {data.get('total')}", duration)
                else:
                    self.log("Search Listings", "PASS", "No listings found", duration)
            else:
                self.log("Search Listings", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Search Listings", "FAIL", str(e))
    
    def test_get_listing_details(self):
        """Tester la récupération des détails d'une annonce"""
        if not self.listing_id:
            self.log("Get Listing Details", "SKIP", "No listing ID")
            return
        
        start = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/discovery/listings/{self.listing_id}")
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                title = data.get("title", "Unknown")
                price = data.get("price", "Unknown")
                self.log("Get Listing Details", "PASS", f"{title} - {price}€", duration)
            else:
                self.log("Get Listing Details", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Get Listing Details", "FAIL", str(e))
    
    # ==================== STATISTICS ====================
    
    def test_market_statistics(self):
        """Tester les statistiques du marché"""
        start = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/discovery/statistics/market", params={
                "postal_code": "75015"
            })
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("statistics", [])
                if stats:
                    avg_price = stats[0].get("average_price", "Unknown")
                    self.log("Market Statistics", "PASS", f"Avg price: {avg_price}€", duration)
                else:
                    self.log("Market Statistics", "PASS", "No statistics found", duration)
            else:
                self.log("Market Statistics", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Market Statistics", "FAIL", str(e))
    
    # ==================== FAVORITES ====================
    
    def test_add_favorite(self):
        """Tester l'ajout aux favoris"""
        if not self.token or not self.listing_id:
            self.log("Add Favorite", "SKIP", "No token or listing ID")
            return
        
        start = time.time()
        try:
            response = self.session.post(f"{self.base_url}/api/user/favorites/{self.listing_id}")
            duration = time.time() - start
            
            if response.status_code == 200:
                self.log("Add Favorite", "PASS", "", duration)
            else:
                self.log("Add Favorite", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Add Favorite", "FAIL", str(e))
    
    def test_get_favorites(self):
        """Tester la récupération des favoris"""
        if not self.token:
            self.log("Get Favorites", "SKIP", "No token")
            return
        
        start = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/user/favorites")
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                favorites = data.get("favorites", [])
                self.log("Get Favorites", "PASS", f"Count: {len(favorites)}", duration)
            else:
                self.log("Get Favorites", "FAIL", f"Status {response.status_code}", duration)
        except Exception as e:
            self.log("Get Favorites", "FAIL", str(e))
    
    # ==================== RUN ALL TESTS ====================
    
    def run_all(self):
        """Exécuter tous les tests"""
        print("\n" + "="*60)
        print("TESTS COMPLETS - REAL ESTATE SCRAPER")
        print("="*60 + "\n")
        
        # Health checks
        print("📊 HEALTH CHECKS")
        self.test_health_check()
        self.test_api_info()
        
        # Authentication
        print("\n🔐 AUTHENTICATION")
        self.test_register()
        self.test_login()
        
        # Discovery
        print("\n🔍 DISCOVERY")
        self.test_discover_agencies()
        self.test_get_agencies()
        self.test_get_agency_details()
        
        # Listings
        print("\n📋 LISTINGS")
        self.test_search_listings()
        self.test_get_listing_details()
        
        # Statistics
        print("\n📈 STATISTICS")
        self.test_market_statistics()
        
        # Favorites
        print("\n❤️ FAVORITES")
        self.test_add_favorite()
        self.test_get_favorites()
        
        # Summary
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Sauvegarder les résultats des tests"""
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"Résultats sauvegardés dans test_results.json")


if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all()
