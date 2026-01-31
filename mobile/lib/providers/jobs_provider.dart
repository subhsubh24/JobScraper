import 'package:flutter/foundation.dart';
import '../models/job.dart';
import '../services/api_client.dart';

class JobsProvider extends ChangeNotifier {
  ApiClient _api;
  List<Job> _jobs = [];
  bool _isLoading = false;
  String? _error;
  Map<String, dynamic>? _pipelineStats;

  JobsProvider(this._api);

  void updateApi(ApiClient api) {
    _api = api;
  }

  List<Job> get jobs => _jobs;
  bool get isLoading => _isLoading;
  String? get error => _error;
  Map<String, dynamic>? get pipelineStats => _pipelineStats;

  // Filtered lists
  List<Job> get savedJobs =>
      _jobs.where((j) => j.status == ApplicationStatus.saved).toList();
  List<Job> get appliedJobs =>
      _jobs.where((j) => j.status == ApplicationStatus.applied).toList();
  List<Job> get interviewingJobs => _jobs
      .where((j) =>
          j.status == ApplicationStatus.phoneScreen ||
          j.status == ApplicationStatus.interview)
      .toList();
  List<Job> get offerJobs =>
      _jobs.where((j) => j.status == ApplicationStatus.offer).toList();

  // Sorted by score
  List<Job> get topJobs {
    final sorted = List<Job>.from(_jobs);
    sorted.sort((a, b) {
      final scoreA = a.score?.overallScore ?? 0;
      final scoreB = b.score?.overallScore ?? 0;
      return scoreB.compareTo(scoreA);
    });
    return sorted;
  }

  Future<void> loadJobs() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _api.getJobs();
      _jobs = data.map((j) => Job.fromJson(j)).toList();
      _isLoading = false;
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> addJob({
    required String title,
    required String companyName,
    String? location,
    String? description,
    String? url,
    int? salaryMin,
    int? salaryMax,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _api.addJob(
        title: title,
        companyName: companyName,
        location: location,
        description: description,
        url: url,
        salaryMin: salaryMin,
        salaryMax: salaryMax,
      );
      final newJob = Job.fromJson(data['job']);
      _jobs.insert(0, newJob);
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

  Future<bool> updateJobStatus(String jobId, ApplicationStatus status,
      {String? notes}) async {
    try {
      await _api.updateJobStatus(
        jobId: jobId,
        status: status.apiValue,
        notes: notes,
      );

      final index = _jobs.indexWhere((j) => j.id == jobId);
      if (index != -1) {
        _jobs[index] = _jobs[index].copyWith(status: status, notes: notes);
        notifyListeners();
      }
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    }
  }

  Future<String?> generatePrepPack(String jobId) async {
    _isLoading = true;
    notifyListeners();

    try {
      final data = await _api.generatePrepPack(jobId);
      _isLoading = false;
      notifyListeners();
      return data['prep_pack']?['content'];
    } on ApiException catch (e) {
      _error = e.message;
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  Future<void> loadPipelineStats() async {
    try {
      _pipelineStats = await _api.getPipelineStats();
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
    }
  }

  Job? getJobById(String id) {
    try {
      return _jobs.firstWhere((j) => j.id == id);
    } catch (_) {
      return null;
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
