import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../services/api_client.dart';

class AuthProvider extends ChangeNotifier {
  ApiClient _api;
  User? _user;
  bool _isLoading = false;
  String? _error;

  AuthProvider(this._api);

  void updateApi(ApiClient api) {
    _api = api;
  }

  User? get user => _user;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _user != null;
  bool get isPremium => _user?.isPremium ?? false;

  Future<void> initialize() async {
    await _api.loadToken();
    if (_api.hasToken) {
      // TODO: Fetch user profile from API
      // For now, we'll set a placeholder
      notifyListeners();
    }
  }

  Future<bool> login({
    required String email,
    required String password,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _api.login(email: email, password: password);
      _user = User.fromJson(data['user']);
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> register({
    required String email,
    required String password,
    String? fullName,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _api.register(
        email: email,
        password: password,
        fullName: fullName,
      );
      _user = User.fromJson(data['user']);
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _api.logout();
    _user = null;
    notifyListeners();
  }

  Future<bool> upgradeToPremium(String receiptData) async {
    _isLoading = true;
    notifyListeners();

    try {
      final data = await _api.verifyPurchase(receiptData);
      _user = User.fromJson(data['user']);
      _isLoading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
