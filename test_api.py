#!/usr/bin/env python3
"""
Script de test des endpoints API.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
TOKEN = None


def print_response(title: str, response: requests.Response):
    """Afficher la réponse formatée."""
    print(f"\n{'='*60}")
    print(f"✓ {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)


def test_health():
    """Tester l'endpoint de santé."""
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    return response.status_code == 200


def test_api_info():
    """Tester l'endpoint d'info API."""
    response = requests.get(f"{BASE_URL}/api/info")
    print_response("API Info", response)
    return response.status_code == 200


def test_register():
    """Tester l'enregistrement utilisateur."""
    global TOKEN
    
    data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    print_response("User Registration", response)
    return response.status_code == 200


def test_login():
    """Tester la connexion utilisateur."""
    global TOKEN
    
    data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
    print_response("User Login", response)
    
    if response.status_code == 200:
        TOKEN = response.json()["access_token"]
        print(f"\n✓ Token obtained: {TOKEN[:50]}...")
        return True
    return False


def test_get_me():
    """Tester la récupération des infos utilisateur."""
    if not TOKEN:
        print("❌ No token available")
        return False
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print_response("Get Current User", response)
    return response.status_code == 200


def test_create_alert():
    """Tester la création d'une alerte de recherche."""
    if not TOKEN:
        print("❌ No token available")
        return False
    
    data = {
        "name": "Appartements Paris 75015",
        "postal_code": "75015",
        "min_price": 200000,
        "max_price": 500000,
        "min_surface": 50,
        "property_type": "apartment"
    }
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(f"{BASE_URL}/api/user/alerts", json=data, headers=headers)
    print_response("Create Search Alert", response)
    return response.status_code == 200


def test_get_alerts():
    """Tester la récupération des alertes."""
    if not TOKEN:
        print("❌ No token available")
        return False
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/api/user/alerts", headers=headers)
    print_response("Get Search Alerts", response)
    return response.status_code == 200


def test_listings():
    """Tester la récupération des annonces."""
    response = requests.get(f"{BASE_URL}/api/listings?postal_code=75015&limit=5")
    print_response("Get Listings", response)
    return response.status_code == 200


def test_agencies():
    """Tester la récupération des agences."""
    response = requests.get(f"{BASE_URL}/api/agencies?postal_code=75015&limit=5")
    print_response("Get Agencies", response)
    return response.status_code == 200


def test_swagger():
    """Tester l'accès à Swagger UI."""
    response = requests.get(f"{BASE_URL}/docs")
    print_response("Swagger UI", response)
    return response.status_code == 200


def run_all_tests():
    """Exécuter tous les tests."""
    print("\n" + "="*60)
    print("🧪 REAL ESTATE SCRAPER API — TEST SUITE")
    print("="*60)
    
    tests = [
        ("Health Check", test_health),
        ("API Info", test_api_info),
        ("Swagger UI", test_swagger),
        ("User Registration", test_register),
        ("User Login", test_login),
        ("Get Current User", test_get_me),
        ("Create Search Alert", test_create_alert),
        ("Get Search Alerts", test_get_alerts),
        ("Get Listings", test_listings),
        ("Get Agencies", test_agencies),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✓ PASS" if result else "❌ FAIL"))
        except Exception as e:
            print(f"\n❌ Error in {name}: {str(e)}")
            results.append((name, f"❌ ERROR: {str(e)[:50]}"))
    
    # Résumé
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    for name, result in results:
        print(f"{name:<30} {result}")
    
    passed = sum(1 for _, r in results if r.startswith("✓"))
    total = len(results)
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_all_tests()
