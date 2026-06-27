import 'package:flutter/foundation.dart';
import '../models/chat_message.dart';
import '../services/api_client.dart';

class CoachProvider extends ChangeNotifier {
  ApiClient _api;
  List<ChatMessage> _messages = [];
  List<String> _suggestions = [];
  String? _sessionId;
  bool _isLoading = false;
  String? _error;

  CoachProvider(this._api);

  void updateApi(ApiClient api) {
    _api = api;
  }

  List<ChatMessage> get messages => _messages;
  List<String> get suggestions => _suggestions;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadSuggestions() async {
    try {
      _suggestions = await _api.getCoachSuggestions();
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
    }
  }

  Future<void> sendMessage(String content, {String? jobId}) async {
    // Add user message immediately
    final userMessage = ChatMessage.user(content);
    _messages.add(userMessage);

    // Add loading indicator
    _messages.add(ChatMessage.loading());
    _isLoading = true;
    notifyListeners();

    try {
      final data = await _api.sendCoachMessage(
        message: content,
        sessionId: _sessionId,
        jobId: jobId,
      );

      // Remove loading indicator
      _messages.removeWhere((m) => m.isLoading);

      // Add assistant response
      final response = data['response'] ?? data['message'] ?? '';
      _sessionId = data['session_id'];
      _messages.add(ChatMessage.assistant(response));

      _isLoading = false;
      notifyListeners();
    } on ApiException catch (e) {
      _messages.removeWhere((m) => m.isLoading);
      _error = e.message;
      _isLoading = false;
      notifyListeners();
    }
  }

  void clearChat() {
    _messages = [];
    _sessionId = null;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
