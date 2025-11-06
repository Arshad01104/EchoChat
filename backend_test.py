import requests
import sys
import json
from datetime import datetime

class EchoChatAPITester:
    def __init__(self, base_url="https://echochat-dev.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.username = None
        self.room_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    print(f"   Response Data: {json.dumps(response_data, indent=2)[:200]}...")
                    self.log_test(name, True)
                    return True, response_data
                except:
                    self.log_test(name, True, "No JSON response")
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Error: {error_data}"
                except:
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"   Error: {error_msg}")
            self.log_test(name, False, error_msg)
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        self.username = f"testuser_{timestamp}"
        password = "TestPass123!"
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"username": self.username, "password": password}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['user_id']
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"username": self.username, "password": "TestPass123!"}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            return True
        return False

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "auth/login",
            401,
            data={"username": "nonexistent", "password": "wrongpass"}
        )
        return success

    def test_create_room(self):
        """Test room creation"""
        room_data = {
            "name": "Test Chat Room",
            "description": "A test room for API testing",
            "room_code": "TEST123"
        }
        
        success, response = self.run_test(
            "Create Room",
            "POST",
            "rooms/create",
            200,
            data=room_data
        )
        
        if success and 'room_id' in response:
            self.room_id = response['room_id']
            return True
        return False

    def test_list_rooms(self):
        """Test listing all rooms"""
        success, response = self.run_test(
            "List Rooms",
            "GET",
            "rooms/list",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} rooms")
            return True
        return False

    def test_get_room_details(self):
        """Test getting specific room details"""
        if not self.room_id:
            self.log_test("Get Room Details", False, "No room_id available")
            return False
            
        success, response = self.run_test(
            "Get Room Details",
            "GET",
            f"rooms/{self.room_id}",
            200
        )
        return success

    def test_check_membership(self):
        """Test checking room membership"""
        if not self.room_id:
            self.log_test("Check Membership", False, "No room_id available")
            return False
            
        success, response = self.run_test(
            "Check Membership",
            "GET",
            f"rooms/{self.room_id}/check-membership",
            200
        )
        
        if success:
            print(f"   Membership status: {response.get('status', 'unknown')}")
        return success

    def test_get_messages(self):
        """Test getting room messages"""
        if not self.room_id:
            self.log_test("Get Messages", False, "No room_id available")
            return False
            
        success, response = self.run_test(
            "Get Messages",
            "GET",
            f"rooms/{self.room_id}/messages",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} messages")
        return success

    def test_pending_requests(self):
        """Test getting pending join requests (admin only)"""
        if not self.room_id:
            self.log_test("Get Pending Requests", False, "No room_id available")
            return False
            
        success, response = self.run_test(
            "Get Pending Requests",
            "GET",
            f"rooms/{self.room_id}/pending-requests",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} pending requests")
        return success

    def test_unauthorized_access(self):
        """Test API access without token"""
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Unauthorized Access",
            "GET",
            "rooms/list",
            401
        )
        
        # Restore token
        self.token = original_token
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting EchoChat API Tests")
        print("=" * 50)
        
        # Authentication Tests
        print("\n📝 Authentication Tests")
        if not self.test_user_registration():
            print("❌ Registration failed, stopping tests")
            return False
            
        self.test_invalid_login()
        
        if not self.test_user_login():
            print("❌ Login failed, stopping tests")
            return False
        
        # Authorization Tests
        print("\n🔒 Authorization Tests")
        self.test_unauthorized_access()
        
        # Room Management Tests
        print("\n🏠 Room Management Tests")
        if not self.test_create_room():
            print("❌ Room creation failed, stopping room tests")
        else:
            self.test_get_room_details()
            self.test_check_membership()
            self.test_get_messages()
            self.test_pending_requests()
        
        self.test_list_rooms()
        
        # Print Results
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Overall Status: GOOD")
        elif success_rate >= 60:
            print("⚠️  Overall Status: NEEDS ATTENTION")
        else:
            print("🚨 Overall Status: CRITICAL ISSUES")
        
        return success_rate >= 80

def main():
    tester = EchoChatAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())