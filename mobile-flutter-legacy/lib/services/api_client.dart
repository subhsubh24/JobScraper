import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class ApiClient {
  // Change this to your Railway URL after deployment
  static const String baseUrl = 'http://localhost:8000';

  String? _token;

  Future<void> loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('auth_token');
  }

  Future<void> saveToken(String token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }

  Future<void> clearToken() async {
    _token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
  }

  bool get hasToken => _token != null;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Future<Map<String, dynamic>> _handleResponse(http.Response response) async {
    final body = jsonDecode(response.body);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }

    throw ApiException(
      body['detail'] ?? 'An error occurred',
      statusCode: response.statusCode,
    );
  }

  // ============ AUTH ============

  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    String? fullName,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/register'),
      headers: _headers,
      body: jsonEncode({
        'email': email,
        'password': password,
        if (fullName != null) 'full_name': fullName,
      }),
    );
    final data = await _handleResponse(response);
    await saveToken(data['token']);
    return data;
  }

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/login'),
      headers: _headers,
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );
    final data = await _handleResponse(response);
    await saveToken(data['token']);
    return data;
  }

  Future<void> logout() async {
    await clearToken();
  }

  Future<Map<String, dynamic>> verifyPurchase(String receiptData) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/verify-purchase'),
      headers: _headers,
      body: jsonEncode({'receipt_data': receiptData}),
    );
    return _handleResponse(response);
  }

  // ============ JOBS ============

  Future<List<dynamic>> getJobs() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/jobs'),
      headers: _headers,
    );
    final data = await _handleResponse(response);
    return data['jobs'] ?? [];
  }

  Future<Map<String, dynamic>> addJob({
    required String title,
    required String companyName,
    String? location,
    String? description,
    String? url,
    int? salaryMin,
    int? salaryMax,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/jobs'),
      headers: _headers,
      body: jsonEncode({
        'title': title,
        'company_name': companyName,
        if (location != null) 'location': location,
        if (description != null) 'description': description,
        if (url != null) 'url': url,
        if (salaryMin != null) 'salary_min': salaryMin,
        if (salaryMax != null) 'salary_max': salaryMax,
      }),
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> updateJobStatus({
    required String jobId,
    required String status,
    String? notes,
  }) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/api/jobs/$jobId'),
      headers: _headers,
      body: jsonEncode({
        'status': status,
        if (notes != null) 'notes': notes,
      }),
    );
    return _handleResponse(response);
  }

  // ============ PREP PACKS ============

  Future<Map<String, dynamic>> generatePrepPack(String jobId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/prep-packs/generate'),
      headers: _headers,
      body: jsonEncode({'job_id': jobId}),
    );
    return _handleResponse(response);
  }

  // ============ AI COACH ============

  Future<Map<String, dynamic>> sendCoachMessage({
    required String message,
    String? sessionId,
    String? jobId,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/coach/chat'),
      headers: _headers,
      body: jsonEncode({
        'message': message,
        if (sessionId != null) 'session_id': sessionId,
        if (jobId != null) 'job_id': jobId,
      }),
    );
    return _handleResponse(response);
  }

  Future<List<String>> getCoachSuggestions() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/coach/suggestions'),
      headers: _headers,
    );
    final data = await _handleResponse(response);
    return List<String>.from(data['suggestions'] ?? []);
  }

  // ============ ANALYTICS ============

  Future<Map<String, dynamic>> getPipelineStats() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/analytics/pipeline'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  // ============ PROFILE ============

  Future<Map<String, dynamic>> updateResume(String resumeText) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/api/profile'),
      headers: _headers,
      body: jsonEncode({'resume_text': resumeText}),
    );
    return _handleResponse(response);
  }
}
