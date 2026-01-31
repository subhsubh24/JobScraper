enum UserTier { free, premium }

class User {
  final String id;
  final String email;
  final UserTier tier;
  final String? fullName;
  final String? resumeText;
  final int jobsAddedThisMonth;
  final int prepPacksThisMonth;
  final DateTime createdAt;

  User({
    required this.id,
    required this.email,
    required this.tier,
    this.fullName,
    this.resumeText,
    this.jobsAddedThisMonth = 0,
    this.prepPacksThisMonth = 0,
    required this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      tier: json['tier'] == 'premium' ? UserTier.premium : UserTier.free,
      fullName: json['full_name'],
      resumeText: json['resume_text'],
      jobsAddedThisMonth: json['jobs_added_this_month'] ?? 0,
      prepPacksThisMonth: json['prep_packs_this_month'] ?? 0,
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  bool get isPremium => tier == UserTier.premium;

  // Free tier limits
  static const int freeJobsLimit = 5;
  static const int freePrepPacksLimit = 1;

  int get jobsRemaining => isPremium ? -1 : freeJobsLimit - jobsAddedThisMonth;
  int get prepPacksRemaining =>
      isPremium ? -1 : freePrepPacksLimit - prepPacksThisMonth;

  bool get canAddJob => isPremium || jobsAddedThisMonth < freeJobsLimit;
  bool get canGeneratePrepPack =>
      isPremium || prepPacksThisMonth < freePrepPacksLimit;
}
